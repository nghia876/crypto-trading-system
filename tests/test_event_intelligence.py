from dataclasses import replace
from datetime import timedelta

import pytest

from tests.test_claim_lifecycle import T, article, persist
from tradingagents.information.claim_lifecycle import record_claim_assertion
from tradingagents.information.event_intelligence import (
    incident_prompt,
    incident_state,
    record_incident_membership,
    research_once,
    research_plan,
)
from tradingagents.information.store import SQLiteInformationStore


def link(store, ids, key="flood:delta:2026-01-09", time=T, retract=()):
    return record_incident_membership(
        store,
        incident_id=key,
        evidence_ids=ids,
        recorded_at=time,
        rationale="Reviewed location and episode evidence",
        retract_ids=retract,
    )


def test_incident_identity_replay_reopen_and_competing_claims(tmp_path):
    store = SQLiteInformationStore(tmp_path / "info.db")
    persist(
        store,
        article("a", "Delta flood reported"),
        article("b", "Delta flood denied"),
        article("c", "Delta flood reported"),
    )
    first = link(store, ("a", "b"))
    link(store, ("c",), key="flood:other-delta:2026-01-09")
    record_claim_assertion(
        store,
        claim_id="a",
        kind="contradiction",
        evidence_ids=("b",),
        recorded_at=T + timedelta(seconds=1),
        rationale="Competing reported claim",
    )
    second = link(store, ("a",), time=T + timedelta(seconds=2), retract=(first.observation_id,))
    reopened = SQLiteInformationStore(store.path)
    early = incident_state(reopened.view_at(T), "flood:delta:2026-01-09")
    assert early["evidence_ids"] == ["a", "b"]
    assert early["first_known"] == T and early["available_at"] == T
    assert early["claims"]["a"]["status"] == "unconfirmed"
    late = incident_state(reopened.view_at(T + timedelta(seconds=2)), "flood:delta:2026-01-09")
    assert late["evidence_ids"] == ["a"]
    assert late["claims"]["a"]["status"] == "contested"
    assert late["membership_history"] == (first, second)
    assert late["occurrence_time"] is None and late["factual_truth"] == "unknown"
    assert incident_prompt(reopened.view_at(T), article("c"))[0]["id"].startswith("flood:other")
    assert (
        incident_state(reopened.view_at(T - timedelta(seconds=1)), early["incident_id"])["claims"]
        == {}
    )


def test_membership_validation_and_idempotence(tmp_path):
    store = SQLiteInformationStore(tmp_path / "info.db")
    persist(store, article("a"), article("future", time=T + timedelta(days=1)))
    with pytest.raises(ValueError):
        link(store, ("future",))
    with pytest.raises(ValueError):
        link(store, ("missing",))
    first = link(store, ("a",))
    assert link(store, ("a",)) == first
    with pytest.raises(ValueError):
        link(store, ("a",), key="another", retract=(first.observation_id,))


def test_research_missing_domain_no_request(tmp_path):
    store = SQLiteInformationStore(tmp_path / "info.db")
    persist(store, article("a"))
    link(store, ("a",))
    plan, outcomes = research_once(store, "flood:delta:2026-01-09", now=T)
    assert plan["missing_domains"] == ["GEOPOLITICS"]
    assert outcomes == () and plan["contradiction_search"] == "not_performed"


def test_research_failure_and_durable_cooldown(tmp_path):
    import requests

    class Failed:
        calls = 0

        def get(self, *args, **kwargs):
            self.calls += 1
            raise requests.ConnectionError("private remote message")

    store = SQLiteInformationStore(tmp_path / "info.db")
    row = article("a")
    row = replace(row, payload=dict(row.payload) | {"domain": "FLOOD_DISASTER"})
    persist(store, row)
    link(store, ("a",))
    assert research_plan(store.view_at(T), "flood:delta:2026-01-09")["source_ids"] == [
        "news.usgs.river_flood"
    ]
    session = Failed()
    plan, outcomes = research_once(
        store, "flood:delta:2026-01-09", now=T, session=session, clock=lambda: T
    )
    assert session.calls == 1 and outcomes
    assert "private remote message" not in str(outcomes)
    reopened = SQLiteInformationStore(store.path)
    research_once(
        reopened,
        plan["incident_id"],
        now=T + timedelta(seconds=10),
        session=session,
        clock=lambda: T,
    )
    assert session.calls == 1


def test_shared_publisher_channels_never_independent(tmp_path):
    store = SQLiteInformationStore(tmp_path / "info.db")
    rows = [
        replace(article(k), payload=dict(article(k).payload) | {"publisher_group": "agency"})
        for k in ("a", "b")
    ]
    persist(store, *rows)
    record_claim_assertion(
        store,
        claim_id="a",
        kind="support",
        evidence_ids=("a", "b"),
        recorded_at=T,
        rationale="Reports",
    )
    record_claim_assertion(
        store,
        claim_id="a",
        kind="independence",
        evidence_ids=("a",),
        target_ids=("b",),
        recorded_at=T,
        rationale="Different channels are insufficient",
    )
    from tradingagents.information.claim_lifecycle import claim_lifecycle

    assert claim_lifecycle(store.view_at(T), "a")["independence"] == "unknown"


def test_success_candidates_are_review_only_and_persisted(tmp_path):
    from tests.test_broad_news import rss, session_for

    store = SQLiteInformationStore(tmp_path / "info.db")
    row = replace(
        article("a", "Delta river flood warning"),
        payload={"claim": "Delta river flood warning", "domain": "FLOOD_DISASTER"},
    )
    persist(store, row)
    link(store, ("a",))
    plan, _ = research_once(
        store,
        "flood:delta:2026-01-09",
        now=T,
        clock=lambda: T,
        session=session_for(
            rss("Delta river flood correction", url="https://water.usgs.gov/alerts/delta")
        ),
    )
    assert len(plan["candidate_evidence_ids"]) == 1
    reopened = SQLiteInformationStore(store.path)
    assert incident_state(reopened.view_at(T), plan["incident_id"])["evidence_ids"] == ["a"]
    assert any(r.metric == "narrative.research_attempt" for r in reopened.view_at(T).observations)
    assert not any(
        r.metric == "narrative.research_attempt"
        for r in reopened.view_at(T - timedelta(seconds=1)).observations
    )


def test_combined_context_preserves_world_macro_and_btc(tmp_path):
    from tests.test_broad_news import rss
    from tests.test_liquidity import NOW, PARSERS, h41, rrp
    from tests.test_original_macro import bls
    from tradingagents.information.binance_spot import MarketDataBatch
    from tradingagents.information.consumer import (
        build_analysis_information,
        render_analysis_information,
    )
    from tradingagents.information.news import parse_news_snapshot
    from tradingagents.information.observations import Observation
    from tradingagents.information.original_macro import parse_bls_json
    from tradingagents.information.sources import SPECIALIST_WORLD_CONFIG

    store = SQLiteInformationStore(tmp_path / "combined.db")
    store.append(PARSERS[0](h41(), NOW))
    store.append(PARSERS[1](rrp(), NOW))
    store.append(parse_bls_json(bls(), retrieved_at=NOW))
    persist(
        store,
        article("world-flood", "Flood disrupts agriculture and energy infrastructure"),
        article(
            "world-radar",
            "War and drought strain agriculture; energy grid disruption; technology and cyber incident",
        ),
    )
    link(store, ("world-flood",), key="delta-flood-episode", time=NOW)
    for config in SPECIALIST_WORLD_CONFIG:
        store.append(
            parse_news_snapshot(
                rss(config.domain + " specialist warning", url=config.source.endpoint),
                config,
                retrieved_at=NOW,
            )
        )
    btc = Observation(
        observation_id="btc-core",
        source_id="derivatives.binance.usdm.funding",
        subject="BTCUSDT",
        metric="derivatives.funding_rate.usdm",
        payload={"funding_rate": "0.001"},
        event_time=NOW,
        first_seen_time=NOW,
        retrieved_at=NOW,
    )
    store.append(MarketDataBatch((btc,), (), NOW))
    text = render_analysis_information(build_analysis_information(store, NOW))
    assert len(text) <= 28000
    for value in (
        "delta-flood-episode",
        "btc-core",
        "War and drought",
        "technology and cyber",
        "DROUGHT_WATER",
        "AGRICULTURE_FOOD",
        "ENERGY_GRID",
        "FLOOD_DISASTER",
        "6745635 million USD",
        "353000000 USD",
        "325.5 index",
    ):
        assert value in text


def test_revised_article_requires_new_identity_review(tmp_path):
    store = SQLiteInformationStore(tmp_path / "info.db")
    first = article("a", "Delta flood")
    persist(store, first)
    link(store, ("a",))
    later = T + timedelta(hours=1)
    revised = replace(article("a", "Different episode", time=later), observation_id="a-v2")
    persist(store, revised)
    view = SQLiteInformationStore(store.path).view_at(later)
    assert incident_prompt(view, first)
    assert incident_prompt(view, revised) == []
