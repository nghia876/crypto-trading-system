"""Synthetic acquisition contracts; no live election or price-impact evidence."""

import json
from dataclasses import replace
from datetime import timedelta

import pytest

from tests.test_adaptive_discovery import feed_session, manual_doc
from tests.test_broad_news import T, rss
from tests.test_graph_end_to_end import PromptCapturingModel, _graph, offline  # noqa: F401
from tests.test_narrative_visibility import article
from tradingagents.information.adaptive_discovery import import_search, research
from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.discovery_sources import DISCOVERY_CONFIGS
from tradingagents.information.narrative_events import (
    narrative_events,
    render_narrative_events,
    selected_narrative_events,
)
from tradingagents.information.news import parse_news_snapshot
from tradingagents.information.political_intelligence import (
    POLITICAL_QUERY_SEEDS,
    political_identity_conflicts,
    political_link_candidates,
    political_prompt,
    political_queries,
    political_topics,
    record_political_context,
)
from tradingagents.information.sources import NewsDiscoveryConfig
from tradingagents.information.store import SQLiteInformationStore


def intake(store, title="US midterm 2026 Senate vote counting continues", url="race", at=T):
    config = DISCOVERY_CONFIGS[0]
    batch = parse_news_snapshot(rss(title, url="https://globalvoices.org/" + url),
                                config, retrieved_at=at)
    store.append(batch)
    return batch.observations[0]


@pytest.mark.parametrize("title,topic", [
    ("US midterm election calendar 2026", "ELECTION_CALENDAR"),
    ("Kenya vote counting continues", "VOTE_COUNT_REPORTING"),
    ("Brazil official election results reported", "REPORTED_ELECTION_RESULTS"),
    ("Opinion polling of adults fieldwork October 1", "REPORTED_POLLING"),
    ("Germany coalition parliament control changes", "GOVERNMENT_CONTROL"),
    ("Japan fiscal tax budget legislation", "FISCAL_TAX_CRYPTO_POLICY"),
    ("European sanctions and trade tariffs", "INTERNATIONAL_RELATIONS"),
    ("Correction: false claim of election result denied", "POLITICAL_PUBLIC_CLAIMS"),
    ("Việt Nam bầu cử kiểm phiếu", "VOTE_COUNT_REPORTING"),
    ("Brasil eleições apuração", "ELECTION_CALENDAR"),
])
def test_non_btc_political_admission_and_expansion(tmp_path, title, topic):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    row = intake(store, title)
    assert topic in political_topics(title)
    assert row in narrative_events(store.view_at(T))
    query = political_queries([row])[0]
    assert title in query["query"] and query["input_evidence_ids"] == [row.observation_id]
    assert "BTC" not in title and row.payload["independent_confirmation"] == "unknown"
    assert row.payload["evidence_level"] == "HEADLINE_METADATA_ONLY"
    assert row.payload["domain"] == "WORLD"  # search labels never rewrite intake identity
    assert row in selected_narrative_events(store.view_at(T))


def test_queries_seeds_rotate_bounded_provenance_and_manual_rights(tmp_path):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    report = research(store, run_id="political-seeds", now=T, clock=lambda: T,
                      session=feed_session())
    assert len(report["political_queries"]) == 2
    assert report["max_feed_requests"] == 3 and report["query_budget"] == 8
    previous = {q["query_id"] for q in report["political_queries"]}
    following = political_queries([], previous=previous)
    assert not previous & {q["query_id"] for q in following}
    assert political_queries([], budget=0) == []
    assert len(POLITICAL_QUERY_SEEDS) == 10
    q = report["political_queries"][0]
    assert q["status"] == "pending" and q["fanout"] == 0
    assert q["run_id"] == report["run_id"] and q["generated_at"] == report["completed_at"]
    doc = dict(manual_doc(report), query_id=q["query_id"], query=q["query"],
               channels_covered=["synthetic manual search channel"],
               channels_missed=["official commission results not accessed"])
    doc["results"][0]["title"] = "Reported election count remains unverified"
    later = T + timedelta(hours=1)
    receipt = import_search(store, doc, imported_at=later)
    row = next(r for r in store.view_at(later).observations
               if r.observation_id in receipt["evidence_ids"])
    assert row.payload["manual_search_query"] == q["query"]
    assert row.available_at == later and row.first_seen_time == later
    assert row.payload["attribution"] == "Global Voices"
    assert row.payload["licence_attribution"]
    assert row not in store.view_at(T).observations
    assert import_search(store, doc, imported_at=later) == receipt
    invalid = json.loads(json.dumps(doc))
    invalid["results"][0]["source_id"] = "news.bbc.world"
    with pytest.raises(ValueError, match="rights review"):
        import_search(store, invalid, imported_at=later)
    with pytest.raises(ValueError, match="searched channel"):
        import_search(store, dict(doc, channels_covered=[]), imported_at=later)


def test_review_rumor_correction_poll_unknowns_and_reopen_pit(tmp_path):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    row = intake(store, "Rumor claims election result; officials deny it")
    later, correction = T + timedelta(hours=1), T + timedelta(hours=2)
    review = record_political_context(store, evidence_id=row.observation_id, recorded_at=later,
                                      reviewer="fixture", provenance="synthetic source attribution",
                                      statement_kind="rumor", result_status="developing_unverified_count",
                                      jurisdiction="US:state-A", race="Senate", election_date="2026-11-03")
    assert political_prompt(store.view_at(T), row) is None
    assert political_prompt(store.view_at(later), row)["statement_kind"] == "rumor"
    updated = record_political_context(store, evidence_id=row.observation_id, recorded_at=correction,
                                       reviewer="fixture", provenance="synthetic correction notice",
                                       statement_kind="correction", supersedes=review.observation_id)
    view = SQLiteInformationStore(store.path, read_only=True).view_at(correction)
    assert political_prompt(view, row)["statement_kind"] == "correction"
    assert political_prompt(store.view_at(later), row)["statement_kind"] == "rumor"
    assert review in view.evidence_history and updated in view.observations
    poll = intake(store, "Opinion polling measured", url="poll")
    record_political_context(store, evidence_id=poll.observation_id, recorded_at=later,
                             reviewer="fixture", provenance="synthetic poll report",
                             statement_kind="reported_poll_measurement")
    context = political_prompt(store.view_at(later), poll)
    assert context["polling_completeness"].startswith("population/date incomplete")
    assert "poll_population" not in context and "election_date" not in context
    with pytest.raises(ValueError, match="available narrative"):
        record_political_context(store, evidence_id="missing", recorded_at=T,
                                 reviewer="fixture", provenance="fixture")
    with pytest.raises(ValueError, match="statement kind"):
        record_political_context(store, evidence_id=row.observation_id, recorded_at=T,
                                 reviewer="fixture", provenance="fixture", statement_kind="predicted_winner")


@pytest.mark.parametrize("kind,status", [
    ("factual_claim", "documented_official_result"),
    ("opinion", "not_applicable"), ("speculation", "unknown"),
    ("denial", "developing_unverified_count"),
    ("reported_poll_measurement", "not_applicable"),
])
def test_attributed_context_does_not_upgrade_truth(tmp_path, kind, status):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    row = intake(store)
    record_political_context(store, evidence_id=row.observation_id, recorded_at=T,
                             reviewer="synthetic reviewer", provenance="synthetic attributed document",
                             statement_kind=kind, result_status=status,
                             poll_population="registered adults" if kind == "reported_poll_measurement" else None,
                             poll_fieldwork_date="2026-01-01/2026-01-03" if kind == "reported_poll_measurement" else None)
    prompt = "\n".join(render_narrative_events(store.view_at(T)))
    assert kind in prompt and status in prompt
    assert row.payload["fact_status"] == "source_reported_claim"
    assert row.payload["verified_facts"] == ()
    assert "attributed_reviewer_not_verified_truth" in prompt


def test_distinct_races_years_instruments_and_copy_lineage(tmp_path):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    rows = [intake(store, "Reported election result", url=key)
            for key in ("us-2026-senate", "us-2024-senate", "kenya-2026", "tax-bill-a", "tax-bill-b")]
    for row, jurisdiction, race, date, instrument in zip(
        rows, ("US", "US", "KE", "US", "US"), ("Senate", "Senate", "President", None, None),
        ("2026", "2024", "2026", None, None), (None, None, None, "bill:a", "bill:b"), strict=True
    ):
        record_political_context(store, evidence_id=row.observation_id, recorded_at=T,
                                 reviewer="fixture", provenance="synthetic report", jurisdiction=jurisdiction,
                                 race=race, election_date=date, instrument=instrument)
    assert len({r.subject for r in narrative_events(store.view_at(T))}) == 5
    contexts = {row.observation_id: political_prompt(store.view_at(T), row) for row in rows}
    assert "political_election_date" in political_identity_conflicts(contexts[rows[0].observation_id], contexts[rows[1].observation_id])
    assert "political_jurisdiction" in political_identity_conflicts(contexts[rows[0].observation_id], contexts[rows[2].observation_id])
    assert "political_instrument" in political_identity_conflicts(contexts[rows[3].observation_id], contexts[rows[4].observation_id])
    assert all(r.payload["origin"] == "unknown" for r in rows)
    # Cross-channel copies keep evidence/source lineage, not extra independent votes.
    config = replace(DISCOVERY_CONFIGS[0], source=replace(DISCOVERY_CONFIGS[0].source,
                     source_id="synthetic.other.channel"))
    copy = parse_news_snapshot(rss("Reported election result", url=rows[0].raw_reference),
                               config, retrieved_at=T).observations[0]
    assert copy.subject == rows[0].subject and copy.observation_id != rows[0].observation_id
    assert copy.source_id != rows[0].source_id and copy.payload["independent_confirmation"] == "unknown"
    for domain in ("POLITICS_ELECTIONS", "FISCAL_REGULATORY_POLICY", "INTERNATIONAL_RELATIONS"):
        assert NewsDiscoveryConfig(config.source, domain).domain == domain
    # Exercise the real existing matcher through the acquisition overlay. Its
    # historical code/manifests stay frozen; review conflicts only remove links.
    from tradingagents.information.event_intelligence import suggest_event_links

    pair_store = SQLiteInformationStore(tmp_path / "pair.db")
    pair = [intake(pair_store, "US Senate regulation election result reported", url=key)
            for key in ("2024", "2026")]
    for evidence, date in zip(pair, ("2024", "2026"), strict=True):
        record_political_context(pair_store, evidence_id=evidence.observation_id, recorded_at=T,
                                 reviewer="fixture", provenance="synthetic race report", election_date=date)
    view = pair_store.view_at(T)
    assert suggest_event_links(view)["candidates"]
    overlay = political_link_candidates(view)
    assert not overlay["candidates"] and overlay["political_vetoes"]


@pytest.mark.usefixtures("offline")
def test_actual_market_graph_political_evidence_and_existing_lanes(tmp_path, monkeypatch):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    row = intake(store, "Synthetic Kenya election commission vote counting update")
    stamp = row.available_at
    record_political_context(store, evidence_id=row.observation_id, recorded_at=stamp,
                             reviewer="fixture", provenance="synthetic commission report",
                             jurisdiction="KE", race="national", result_status="developing_unverified_count")
    others = tuple(replace(article(i, domain, "agency" + str(i), available=stamp),
                           event_time=stamp, publication_time=stamp)
                   for i, domain in enumerate(("FLOOD_DISASTER", "ENERGY_GRID", "TECHNOLOGY")))
    store.append(MarketDataBatch(others, (), stamp))
    view = store.view_at(stamp)
    selected = selected_narrative_events(view)
    assert {r.observation_id for r in (row, *others)} <= {r.observation_id for r in selected}
    assert len("\n".join(render_narrative_events(view))) <= 6000
    assert not store.view_at(stamp - timedelta(microseconds=1)).observations
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
    state, _ = graph.propagate("BTCUSDT", stamp.date().isoformat(), asset_type="crypto", decision_time=stamp)
    market = "\n".join(p for p in model.prompts if "get_verified_market_snapshot" in p)
    assert row.observation_id in market and row.payload["claim"] in market
    assert "developing_unverified_count" in market and "political_context" in market
    assert all(r.observation_id in market for r in others)
    assert len(state["analysis_information"]) <= 28000 and max(map(len, model.prompts)) <= 28000


def test_political_volume_does_not_take_other_domain_reservations(tmp_path):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    for index in range(60):
        intake(store, "Synthetic election count update " + str(index), url="race-" + str(index))
    others = tuple(replace(article(i, domain, "agency" + str(i), available=T),
                           event_time=T, publication_time=T)
                   for i, domain in enumerate(("FLOOD_DISASTER", "ENERGY_GRID", "TECHNOLOGY")))
    store.append(MarketDataBatch(others, (), T))
    view = store.view_at(T)
    selected = selected_narrative_events(view)
    assert all(row in selected for row in others)
    assert any(r.payload["domain"] == "WORLD" for r in selected)
    text = "\n".join(render_narrative_events(view))
    assert "candidates=63" in text and "OMITTED=" in text and len(text) <= 6000
