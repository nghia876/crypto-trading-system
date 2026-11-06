"""C1 synthetic evidence contracts; these are not real-world reporting results."""

from dataclasses import replace
from datetime import timedelta

import pytest

from tests.test_broad_news import T, rss
from tests.test_graph_end_to_end import PromptCapturingModel, _graph, offline  # noqa: F401
from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.claim_lifecycle import record_claim_assertion
from tradingagents.information.discovery_sources import DISCOVERY_CONFIGS
from tradingagents.information.event_intelligence import record_incident_membership
from tradingagents.information.event_propagation import (
    candidate_packet,
    candidate_relations,
    collection_sessions,
    identity_conflicts,
    incident_packets,
    sampled_window,
)
from tradingagents.information.narrative_events import render_narrative_events
from tradingagents.information.news import parse_news_snapshot
from tradingagents.information.political_intelligence import record_political_context
from tradingagents.information.store import SQLiteInformationStore


def add(store, title, *, path="story", publisher=0, at=T):
    config = DISCOVERY_CONFIGS[publisher]
    host = "globalvoices.org" if publisher == 0 else "www.ipsnews.net"
    batch = parse_news_snapshot(rss(title, url=f"https://{host}/{path}"), config, retrieved_at=at)
    store.append(batch)
    return next(
        r
        for r in store.view_at(at).evidence_history
        if r.observation_id == batch.observations[0].observation_id
    )


def test_novelty_repeat_revision_source_breadth_and_stale_discovery(tmp_path):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    first = add(store, "Synthetic ancient historical flood report")
    later = T + timedelta(days=1)
    repeat = add(store, first.payload["claim"], at=later)
    changed = add(
        store, "Correction: synthetic historical flood date", at=later + timedelta(seconds=1)
    )
    fresh = add(store, "Synthetic newly discovered historical drought", path="old-new", at=later)
    view = store.view_at(later + timedelta(seconds=1))
    window = sampled_window(view, T, view.decision_time)
    assert (
        window["retrievals"],
        window["new_urls"],
        window["revisions"],
        window["unchanged_retrievals"],
    ) == (3, 1, 1, 1)
    assert (
        fresh.publication_time < T
        and candidate_packet(view, fresh)["first_known"] == later.isoformat()
    )
    packets = [candidate_packet(view, row) for row in (first, repeat, changed)]
    assert len({p["id"] for p in packets}) == 1
    assert packets[-1]["version_id"] != packets[0]["version_id"]
    assert packets[-1]["first_known"] == T.isoformat()
    assert len(view.evidence_history) == 4
    assert window["acceleration"] == "NOT_MEASURED" and window["reach"] == "UNKNOWN"
    assert sampled_window(store.view_at(T), T - timedelta(seconds=1), T)["new_urls"] == 1
    with pytest.raises(ValueError):
        sampled_window(view, T, view.decision_time + timedelta(seconds=1))


@pytest.mark.parametrize(
    "field,left,right",
    [
        ("jurisdiction", "US:state-a", "KE"),
        ("race", "Senate", "President"),
        ("election_date", "2026-11-03", "2024-11-05"),
        ("institution", "Senate", "House"),
        ("instrument", "bill-a", "bill-b"),
    ],
)
def test_political_conflicts_quarantine_reviewed_incident(tmp_path, field, left, right):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    a = add(store, "Synthetic Senate regulation election result reported", path="a")
    b = add(store, "Synthetic Senate regulation election result reported", path="b", publisher=1)
    for row, value in ((a, left), (b, right)):
        record_political_context(
            store,
            evidence_id=row.observation_id,
            recorded_at=T,
            reviewer="synthetic",
            provenance="synthetic explicit identity",
            **{field: value},
        )
    record_incident_membership(
        store,
        incident_id="synthetic-review-error",
        evidence_ids=(a.observation_id, b.observation_id),
        recorded_at=T,
        rationale="Synthetic conflicting reviewer association",
    )
    packet = incident_packets(store.view_at(T))[0]
    assert packet["status"] == "CONFLICT_REQUIRES_REVIEW" and packet["conflicts"]
    assert len(packet["article_roots"]) == 2
    assert not candidate_relations(store.view_at(T))["proposals"]


def test_overlapping_titles_different_years_disasters_and_unknown_metadata(tmp_path):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    a = add(store, "Delta flood emergency in Atlas 2024", path="a")
    b = add(store, "Delta flood emergency in Atlas 2026", path="b")
    c = add(store, "Delta flood emergency in Boreal 2026", path="c")
    view = store.view_at(T)
    assert "headline_year" in identity_conflicts(view, a, b)
    assert len({candidate_packet(view, r)["id"] for r in (a, b, c)}) == 3
    assert not incident_packets(view)
    unknown = replace(a, payload={**a.payload, "publisher_group": "unknown", "version_id": None})
    sparse = replace(view, observations=(unknown,), evidence_history=(unknown,))
    packet = candidate_packet(sparse, unknown)
    assert packet["status"] == "CANDIDATE_UNRESOLVED"
    assert packet["statement_kind"] == "UNVERIFIED_ATTRIBUTED_ASSERTION"
    assert packet["topic_status"].startswith("TENTATIVE")


def test_cross_publisher_review_provenance_same_publisher_and_syndication(tmp_path):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    a = add(store, "Synthetic Atlas bridge collapse report", path="a")
    b = add(store, "Synthetic Atlas bridge collapse second report", path="b", publisher=1)
    c = add(store, "Synthetic Atlas bridge collapse copied report", path="c")
    record_incident_membership(
        store,
        incident_id="synthetic:atlas:bridge:2026-01-09",
        evidence_ids=tuple(r.observation_id for r in (a, b, c)),
        recorded_at=T,
        rationale="Synthetic incident review, no truth assertion",
    )
    record_claim_assertion(
        store,
        claim_id=a.subject,
        kind="support",
        evidence_ids=(
            a.observation_id,
            b.observation_id,
        ),
        recorded_at=T,
        rationale="Synthetic attributed report",
    )
    record_claim_assertion(
        store,
        claim_id=a.subject,
        kind="independence",
        evidence_ids=(a.observation_id,),
        target_ids=(b.observation_id,),
        recorded_at=T,
        rationale="Synthetic source-origin investigation",
    )
    view = store.view_at(T)
    packet = incident_packets(view)[0]
    assert len(packet["claims"]) == 3 and len(packet["article_roots"]) == 3
    assert packet["attention"]["publisher_breadth"] == 2
    assert packet["status"] == "REVIEWED_CANDIDATE_ASSOCIATION"
    assert candidate_packet(view, a)["lifecycle_status"] == "independently_corroborated_reporting"
    later = T + timedelta(seconds=1)
    record_claim_assertion(
        store,
        claim_id=a.subject,
        kind="syndication",
        evidence_ids=(a.observation_id,),
        target_ids=(b.observation_id,),
        recorded_at=later,
        rationale="Synthetic later evidence of shared origin",
    )
    assert candidate_packet(store.view_at(later), a)["independence"] == "unknown"
    assert (
        candidate_packet(store.view_at(T), a)["lifecycle_status"]
        == "independently_corroborated_reporting"
    )


def test_election_rumor_denial_correction_and_future_review_leakage(tmp_path):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    a = add(store, "Synthetic quoted allegation of election count fraud", path="rumor")
    b = add(
        store, "Synthetic publisher quotes denial of election fraud", path="denial", publisher=1
    )
    c = add(store, "Synthetic correction retracts quoted election allegation", path="correction")
    for index, (row, kind) in enumerate(((a, "rumor"), (b, "denial"), (c, "correction"))):
        record_political_context(
            store,
            evidence_id=row.observation_id,
            recorded_at=T + timedelta(hours=index),
            reviewer="synthetic",
            provenance="Synthetic attribution only",
            statement_kind=kind,
            jurisdiction="US:state-a",
            race="Senate",
            election_date="2026-11-03",
        )
    early = store.view_at(T)
    assert candidate_packet(early, b)["statement_kind"] == "UNVERIFIED_ATTRIBUTED_ASSERTION"
    late = store.view_at(T + timedelta(hours=2))
    assert [candidate_packet(late, r)["statement_kind"] for r in (a, b, c)] == [
        "rumor",
        "denial",
        "correction",
    ]
    assert all(candidate_packet(late, r)["independence"] == "unknown" for r in (a, b, c))
    assert "denial/correction is not confirmation" in "\n".join(render_narrative_events(late))
    assert not store.view_at(T - timedelta(microseconds=1)).evidence_history


@pytest.mark.usefixtures("offline")
def test_actual_graph_packets_core_context_diversity_and_future(tmp_path, monkeypatch):
    from tests.test_narrative_visibility import article

    store = SQLiteInformationStore(tmp_path / "isolated.db")
    a = add(store, "Synthetic Kenya election count developing", path="politics")
    others = tuple(
        replace(article(i, d, "agency" + str(i), available=T), event_time=T, publication_time=T)
        for i, d in enumerate(("FLOOD_DISASTER", "ENERGY_GRID", "TECHNOLOGY"))
    )
    store.append(MarketDataBatch(others, (), T))
    future = add(store, "FUTURE synthetic article", path="future", at=T + timedelta(days=1))
    view = store.view_at(T)
    with pytest.raises(ValueError, match="cutoff-eligible"):
        candidate_packet(view, future)
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
    state, _ = graph.propagate(
        "BTCUSDT", T.date().isoformat(), asset_type="crypto", decision_time=T
    )
    prompt = "\n".join(p for p in model.prompts if "get_verified_market_snapshot" in p)
    assert all(r.observation_id in prompt for r in (a, *others))
    assert candidate_packet(view, a)["id"] in prompt and "observed_24h" in prompt
    assert future.observation_id not in prompt and "FUTURE synthetic" not in prompt
    assert "Macro series:" in prompt and "Funding rate:" in prompt
    assert len("\n".join(render_narrative_events(view))) <= 6000
    assert len(state["analysis_information"]) <= 28000 and max(map(len, model.prompts)) <= 28000


@pytest.mark.usefixtures("offline")
def test_shared_reviewed_incident_reaches_graph_without_merging_claims(tmp_path, monkeypatch):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    a = add(store, "Synthetic Atlas bridge collapse reported", path="a")
    b = add(store, "Synthetic Atlas bridge collapse denied", path="b", publisher=1)
    record_incident_membership(
        store,
        incident_id="synthetic:atlas:2026-01-09",
        evidence_ids=(a.observation_id, b.observation_id),
        recorded_at=T,
        rationale="Synthetic same-incident review, competing claims",
    )
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
    graph.propagate("BTCUSDT", T.date().isoformat(), asset_type="crypto", decision_time=T)
    market = "\n".join(p for p in model.prompts if "get_verified_market_snapshot" in p)
    assert all(r.observation_id in market for r in (a, b))
    assert "synthetic:atlas:2026-01-09" in market and "REVIEWED_CANDIDATE_ASSOCIATION" in market
    assert "reported" in market and "denied" in market
    assert "publisher breadth" not in market or "independence" in market


def test_real_session_metadata_and_offline_unknown_interval(tmp_path):
    from tests.test_adaptive_discovery import feed_session
    from tradingagents.information.adaptive_discovery import research

    store = SQLiteInformationStore(tmp_path / "isolated.db")
    # Advancing clock models actual journal intervals; synthetic, not real collection.
    for index in range(2):
        start = T + timedelta(days=index)
        research(
            store,
            run_id=str(index),
            now=start,
            clock=lambda start=start: start + timedelta(seconds=1),
            session=feed_session(),
        )
    sessions = collection_sessions(store.view_at(T + timedelta(days=1, seconds=2)))
    assert len(sessions) == 2
    assert sessions[-1]["unchanged_retrievals"] > 0
    assert sessions[-1]["new_urls"] == 0
    assert any(h["missed_interval_seconds"] for h in sessions[-1]["health"])
    assert "UNKNOWN" in sessions[-1]["coverage"]
