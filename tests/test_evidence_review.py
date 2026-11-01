"""Real specimen provenance and frozen evaluation workflow contract tests."""

import json
import sqlite3
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

import pytest
import requests

from tests.test_broad_news import rss, session_for
from tests.test_claim_lifecycle import T, article, persist
from tests.test_event_evaluation import label
from tradingagents.information.event_intelligence import suggest_event_links
from tradingagents.information.evidence_review import (
    apply_article_review,
    digest,
    freeze_manifest,
    review_packet,
    score_frozen,
)
from tradingagents.information.evidence_slice import acquire, replay_specimens, require_rights
from tradingagents.information.news import parse_news_snapshot
from tradingagents.information.sources import SPECIALIST_WORLD_CONFIG, WORLD_NEWS_CONFIG
from tradingagents.information.store import SQLiteInformationStore


def packet(store):
    rows = review_packet(store.view_at(T))
    for row in rows:
        row.update(incident_cluster="conservative:test-connected",
                   origin_cluster="synthetic:publisher", duplicate_cluster="synthetic:episode")
    return rows


def labels(**kwargs):
    return [label(reviewer="synthetic-pair-author", reviewed_at=T.isoformat(), **kwargs)]


def test_freeze_score_isolation_reopen_and_tamper(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, article("a", "Drought threatens Colorado farmland irrigation"),
            article("b", "Colorado drought threatens farmland irrigation"))
    pairs = labels()
    manifest = freeze_manifest(packet(store), pairs, seed="fixed-before-score", frozen_at=T)
    assert set(manifest["assignment"].values()) == {"holdout"}
    before = suggest_event_links(store.view_at(T))
    result = score_frozen(store, manifest, pairs, [T - timedelta(seconds=1), T])
    assert result["reports"][0]["pairs"][0]["outcome"] == "unavailable"
    assert result["reports"][1]["metrics"]["overall"]["tp"] == 1
    assert result == score_frozen(SQLiteInformationStore(store.path, read_only=True),
                                  manifest, pairs, [T - timedelta(seconds=1), T])
    assert suggest_event_links(store.view_at(T)) == before
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("pragma integrity_check").fetchone()[0] == "ok"
    changed = deepcopy(pairs)
    changed[0]["label"] = "different_event"
    with pytest.raises(ValueError, match="changed"):
        score_frozen(store, manifest, changed, [T])
    manifest["assignment"]["a"] = "development"
    with pytest.raises(ValueError, match="changed"):
        score_frozen(store, manifest, pairs, [T])


def test_cluster_union_transitive_syndication_correction_and_order(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, *(article(str(i), "Drought threatens Colorado irrigation") for i in range(20)))
    rows = packet(store)
    for i, row in enumerate(rows):
        row.update(incident_cluster=f"incident:{i}", origin_cluster=f"origin:{i}",
                   duplicate_cluster=f"url:{i}")
    rows[1]["origin_cluster"] = rows[0]["origin_cluster"]
    rows[2]["duplicate_cluster"] = rows[1]["duplicate_cluster"]
    rows[3]["incident_cluster"] = rows[2]["incident_cluster"]
    one = freeze_manifest(rows, [], seed="fixed", frozen_at=T)
    assert one == freeze_manifest(list(reversed(rows)), [], seed="fixed", frozen_at=T)
    assert len({one["assignment"][rows[i]["evidence_id"]] for i in range(4)}) == 1
    assert set(one["assignment"].values()) == {"development", "holdout"}
    split = {side: next(key for key, value in one["assignment"].items() if value == side)
             for side in ("development", "holdout")}
    with pytest.raises(ValueError, match="spans splits"):
        freeze_manifest(rows, labels(evidence_ids=list(split.values())), seed="fixed", frozen_at=T)
    rows[0]["origin_cluster"] = None
    with pytest.raises(ValueError, match="unresolved"):
        freeze_manifest(rows, [], seed="fixed", frozen_at=T)


def test_article_adjudication_disagreement_late_review_no_holdout_tuning(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, article("a", "Drought threatens Colorado farmland irrigation"),
            article("b", "Drought threatens Colorado farmland irrigation"))
    pairs = labels()
    frozen = freeze_manifest(packet(store), pairs, seed="fixed", frozen_at=T)
    row = packet(store)[0]
    row.update(status="disputed", review_kind="agent_reviewed", reviewer="Codex agent",
               recorded_at=(T + timedelta(hours=1)).isoformat(), rationale="Unresolved place",
               provenance="synthetic contract; no human", episode_key="synthetic:separate")
    with pytest.raises(ValueError, match="adjudication"):
        apply_article_review(store, row)
    row["status"] = "adjudicated"
    review = apply_article_review(store, row)
    assert "agent_reviewed" in review.payload["provenance"]
    assert not any(r.metric == "narrative.event_context" for r in store.view_at(T).observations)
    with pytest.raises(ValueError, match="unfrozen context"):
        score_frozen(store, frozen, pairs, [T + timedelta(hours=1)])
    assert score_frozen(store, frozen, pairs, [T])["reports"][0]["metrics"]["overall"]["tp"] == 1


def test_rights_gate_bounded_acquisition_health_and_no_btc(tmp_path):
    for config in WORLD_NEWS_CONFIG:
        if config not in SPECIALIST_WORLD_CONFIG[:2]:
            with pytest.raises(ValueError, match="rights"):
                require_rights(config)
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    text = rss("Drought threatens Colorado irrigation", url="https://water.usgs.gov/a")
    result = acquire(store, poll_id="bounded", session=session_for(text), clock=lambda: T, limit=1)
    assert len(result["specimens"]) == 2
    assert result["human_reviews"] == 0
    assert all("BTC" not in s["title"] for s in result["specimens"])
    assert all(r["origin_cluster"] is None for r in result["review_queue"])
    failed = acquire(store, poll_id="failed", session=session_for(error=requests.Timeout()),
                     clock=lambda: T + timedelta(hours=1))
    assert not failed["specimens"]
    assert all(o["status"] == "unavailable" for o in failed["outcomes"])
    assert "unknown" in failed["gaps"]["DROUGHT_WATER"]["completeness"]


def test_real_source_specimens_not_synthetic():
    path = Path(__file__).parent / "fixtures/phase36/phase36_usgs_specimens.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["data_kind"] == "real_source_unreviewed" and data["human_reviews"] == 0
    assert len(data["specimens"]) == 8
    for specimen in data["specimens"]:
        config = next(c for c in SPECIALIST_WORLD_CONFIG if c.source.source_id == specimen["source_id"])
        text = ("<rss><channel><item><title>" + escape(specimen["title"]) + "</title><link>"
                + escape(specimen["url"]) + "</link><pubDate>" + specimen["published_raw"]
                + "</pubDate></item></channel></rss>")
        retrieved = datetime.fromisoformat(specimen["retrieved_at"])
        row = parse_news_snapshot(text, config, retrieved_at=retrieved).observations[0]
        assert row.raw_reference == specimen["url"]
        assert row.payload["publisher_group"] == "U.S. Geological Survey"
        assert row.first_seen_time == row.retrieved_at > row.publication_time
        assert row.payload["event_occurrence_time"] is None
        assert row.payload["independent_confirmation"] == "unknown"
        assert not row.is_available_at(retrieved - timedelta(microseconds=1))


def test_disputed_agent_review_strata_and_future_label(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    persist(store, article("a", "Drought threatens Colorado farmland irrigation"),
            article("b", "Drought threatens Colorado farmland irrigation"))
    pairs = labels(review_status="disputed")
    manifest = freeze_manifest(packet(store), pairs, seed="fixed", frozen_at=T)
    assert score_frozen(store, manifest, pairs, [T])["reports"][0]["pairs"][0]["outcome"] == "unknown"
    pairs[0]["reviewed_at"] = (T + timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError, match="precede"):
        freeze_manifest(packet(store), pairs, seed="fixed", frozen_at=T)
    assert digest({"a": 1, "b": 2}) == digest({"b": 2, "a": 1})


def test_recorded_real_manifest_reproducible_offline(tmp_path):
    folder = Path(__file__).parent / "fixtures/phase36"
    data, manifest, pairs, expected = [json.loads((folder / name).read_text(encoding="utf-8"))
                                     for name in ("phase36_usgs_specimens.json",
                                                  "phase36_frozen_manifest.json",
                                                  "phase36_pair_labels.json", "phase36_metrics.json")]
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    replay_specimens(store, data)
    cutoffs = [datetime.fromisoformat(r["cutoff"]) for r in expected["reports"]]
    actual = score_frozen(store, manifest, pairs, cutoffs)
    assert actual["reports"] == expected["reports"]
    assert actual["manifest_sha256"] == expected["manifest_sha256"]
