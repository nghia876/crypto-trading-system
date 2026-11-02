"""Checkpoint A acceptance: partial evidence, reconciled missingness and local PIT."""

import json
import sqlite3
from dataclasses import replace
from datetime import timedelta

import pytest

from tests.test_broad_news import WAR, T, atom, rss, session_for
from tradingagents.information.narrative_events import (
    narrative_events,
    render_narrative_events,
)
from tradingagents.information.news import _digest, parse_news_snapshot, poll_once
from tradingagents.information.polling import coordinate
from tradingagents.information.source_health import health_report
from tradingagents.information.store import SQLiteInformationStore


def permitted_config():
    # Synthetic exact-scope rights fixture; does not clear any operational publisher.
    return replace(WAR, source=replace(WAR.source, metadata=(
        *((f"summary_{right}", "permitted") for right in
          ("access", "retention", "inference", "redistribution")),
        ("summary_rights_reference", "https://example.org/fixture-rights"),
        ("summary_rights_review_date", "2026-01-09"),
    )))


def summary_rss(text="Original context about the reported negotiations."):
    return rss().replace("</item>", f"<description>{text}</description></item>")


@pytest.mark.parametrize("missing", ["access", "retention", "inference", "redistribution",
                                     "rights_reference", "rights_review_date"])
def test_each_summary_right_fails_closed(missing):
    config = permitted_config()
    config = replace(config, source=replace(config.source, metadata=tuple(
        (key, value) for key, value in config.source.metadata if key != f"summary_{missing}")))
    row = parse_news_snapshot(summary_rss(), config, retrieved_at=T).observations[0]
    assert row.payload["evidence_level"] == "HEADLINE_METADATA_ONLY"
    assert "evidence_text" not in row.payload
    assert row.payload["summary_status"] == "rights_gated"
    assert row.payload["body_status"] == "not_retrieved"


def test_summary_is_attributed_bounded_and_never_a_body():
    text = "&lt;p&gt;Original flood context&lt;/p&gt;&lt;script&gt;bad()&lt;/script&gt;" + "x" * 1400
    row = parse_news_snapshot(summary_rss(text), permitted_config(), retrieved_at=T).observations[0]
    assert row.payload["evidence_level"] == "FEED_SUMMARY"
    assert row.payload["evidence_field"] == "rss.description"
    assert row.payload["evidence_attribution"] == WAR.source.provider
    assert row.payload["evidence_text"].startswith("Original flood context")
    assert "bad()" not in row.payload["evidence_text"]
    assert len(row.payload["evidence_text"]) == 1200
    assert row.payload["evidence_text_truncated"]
    assert row.payload["body_status"] == "not_retrieved"
    assert row.raw_reference == "https://example.org/story?id=7"


def test_atom_summary_and_missing_summary():
    config = replace(permitted_config(), format="atom")
    xml = atom().replace("</entry>", "<summary>Actual supplied summary</summary></entry>")
    row = parse_news_snapshot(xml, config, retrieved_at=T).observations[0]
    assert row.payload["evidence_text"] == "Actual supplied summary"
    assert row.payload["evidence_field"] == "atom.summary"
    row = parse_news_snapshot(atom(), config, retrieved_at=T).observations[0]
    assert row.payload["evidence_level"] == "HEADLINE_METADATA_ONLY"
    assert row.payload["summary_status"] == "not_supplied"


def feed():
    # Deliberately oldest first: never assume provider ordering is newest first.
    items = [rss(f"Report {i}", f"https://example.org/{i}",
                 f"Fri, 09 Jan 2026 {8+i:02}:00:00 GMT").split("<channel>")[1].split("</channel>")[0]
             for i in range(5)]
    return "<rss><channel>" + "".join(items) + "</channel></rss>"


def test_retention_window_manifest_reconciles_every_item_and_restart(tmp_path):
    path = tmp_path / "canonical.db"
    store = SQLiteInformationStore(path)
    result = poll_once(store, (WAR,), poll_id="a", session=session_for(feed()), clock=lambda: T,
                       observation_limit=2, window_start=T - timedelta(hours=3))[0]
    detail = json.loads(result.detail)
    assert detail["snapshot_item_count"] == 5
    assert detail["parsed_unique_items"] == 5
    assert detail["outside_window_count"] == 1
    assert detail["omitted_by_slice_limit"] == 2
    assert [x["source_item_index"] for x in detail["item_manifest"]] == list(range(5))
    assert detail["item_manifest"][1]["state"] == "omitted_retention_cap"
    assert detail["item_manifest"][1]["article_id"] == "article:" + _digest("https://example.org/1")
    assert {r.payload["claim"] for r in store.view_at(T).observations} == {"Report 3", "Report 4"}
    assert "Report 1" not in "\n".join(render_narrative_events(store.view_at(T)))
    assert not store.view_at(T-timedelta(microseconds=1)).observations
    reopened = SQLiteInformationStore(path)
    retry = session_for(error=AssertionError("must not refetch"))
    assert poll_once(reopened, (WAR,), poll_id="a", session=retry)[0] == result
    assert not retry.get.called
    assert health_report(reopened, (WAR,), cutoff=T)["sources"][0]["latest_intake"]["omitted_by_slice_limit"] == 2
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_parser_overflow_is_atomic_and_counted(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    config = replace(WAR, max_items=3)
    result = poll_once(store, (config,), poll_id="overflow", session=session_for(feed()), clock=lambda: T)[0]
    detail = json.loads(result.detail)
    assert detail["outcome"] == "failure"
    assert detail["parser_overflow_count"] == 2
    assert detail["atomic_rejected_item_count"] == 5
    assert detail["items"] == 0 and not detail["item_manifest"]
    assert not store.view_at(T).observations


def test_summary_correction_repoll_and_pit_keep_one_mention(tmp_path):
    path = tmp_path / "canonical.db"
    store = SQLiteInformationStore(path)
    config = permitted_config()
    for i, text in enumerate(("Original context", "Original context", "Corrected context")):
        at = T + timedelta(minutes=i)
        poll_once(store, (config,), poll_id=str(i), session=session_for(summary_rss(text)), clock=lambda at=at: at)
    for i in range(3):
        rows = narrative_events(store.view_at(T+timedelta(minutes=i)))
        assert len(rows) == 1
        assert rows[0].first_seen_time == T
        assert rows[0].payload["evidence_text"] == ("Corrected context" if i == 2 else "Original context")
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM observations").fetchone()[0] == 3
    assert narrative_events(SQLiteInformationStore(path).view_at(T)) == narrative_events(store.view_at(T))


def test_source_health_deferral_reasons(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    other = replace(WAR, domain="TRADE", query="different")  # Same host, different config.
    _, health = coordinate(store, (WAR, other), now=T, clock=lambda: T,
                           session=session_for(rss()), source_ids=(WAR.source.source_id,))
    assert sorted(json.loads(r.detail)["selection_status"] for r in health) == ["host_budget", "selected"]


def test_old_payload_without_new_contract_reopens(tmp_path):
    path = tmp_path / "canonical.db"
    store = SQLiteInformationStore(path)
    batch = parse_news_snapshot(rss(), WAR, retrieved_at=T)
    row = batch.observations[0]
    payload = {k: v for k, v in row.payload.items() if not k.startswith("evidence_")}
    store.append(replace(batch, observations=(replace(row, payload=payload),)))
    view = SQLiteInformationStore(path).view_at(T)
    assert len(narrative_events(view)) == 1
    assert "HEADLINE_METADATA_ONLY" in "\n".join(render_narrative_events(view))


def test_reacquired_omission_never_backdates_and_source_cap_is_explicit(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    coordinate(store, (WAR,), now=T, clock=lambda: T, session=session_for(feed()),
               observation_limit=4, retention_limits={WAR.source.source_id: 1})
    assert len(narrative_events(store.view_at(T))) == 1
    later = T + timedelta(minutes=16)
    coordinate(store, (WAR,), now=later, clock=lambda: later, session=session_for(feed()),
               observation_limit=5)
    assert len(narrative_events(store.view_at(later))) == 5
    assert len(narrative_events(store.view_at(T))) == 1
    old = next(r for r in narrative_events(store.view_at(later)) if r.payload["claim"] == "Report 0")
    assert old.first_seen_time == old.available_at == later
    assert health_report(store, (WAR,), cutoff=later)["sources"][0]["latest_selection"] == "selected"


def test_duplicate_feed_items_future_gate_and_host_exclusion(tmp_path):
    config = replace(WAR, source=replace(WAR.source,
                     metadata=(("article_host_suffix", "example.org"),)))
    xml = (rss().replace("</channel>", rss().split("<channel>")[1].split("</channel>")[0] +
                        rss(url="https://third-party.org/a").split("<channel>")[1].split("</channel>")[0] +
                        rss(url="https://example.org/future", pub="Fri, 09 Jan 2026 13:00:00 GMT").split("<channel>")[1].split("</channel>")[0] + "</channel>"))
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    result = poll_once(store, (config,), poll_id="duplicates", session=session_for(xml), clock=lambda: T)[0]
    detail = json.loads(result.detail)
    assert detail["snapshot_item_count"] == 4
    assert detail["duplicate_item_count"] == 1
    assert detail["excluded_article_count"] == 1
    assert detail["parsed_unique_items"] == 2
    assert sorted(x["state"] for x in detail["item_manifest"]) == ["retained_available", "retained_future_gated"]
    assert len(narrative_events(store.view_at(T))) == 1
    assert len(narrative_events(store.view_at(T + timedelta(hours=1)))) == 2


def test_new_metadata_specimen_replay_preserves_evidence_fingerprint(tmp_path):
    from tradingagents.information.evidence_review import article_fingerprint
    from tradingagents.information.evidence_slice import acquire, replay_specimens

    original = SQLiteInformationStore(tmp_path / "original.db")
    xml = rss(url="https://water.usgs.gov/a")
    report = acquire(original, poll_id="new", session=session_for(xml), clock=lambda: T)
    replayed = SQLiteInformationStore(tmp_path / "replayed.db")
    replay_specimens(replayed, report)
    assert {r.observation_id: article_fingerprint(r) for r in original.view_at(T).observations} == {
        r.observation_id: article_fingerprint(r) for r in replayed.view_at(T).observations}
