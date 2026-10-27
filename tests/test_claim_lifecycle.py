"""Claim correlation, evidence lifecycle, persistence and context integration."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.claim_lifecycle import (
    claim_lifecycle,
    correlation_candidates,
    record_claim_assertion,
)
from tradingagents.information.consumer import (
    build_analysis_information,
    render_analysis_information,
)
from tradingagents.information.observations import Observation
from tradingagents.information.store import SQLiteInformationStore

T = datetime(2026, 1, 9, 12, tzinfo=UTC)


def article(key, title="Ceasefire agreed", time=T, source=None):
    return Observation(
        key,
        source or key,
        key,
        "narrative.event",
        {"claim": title, "domain": "GEOPOLITICS", "fact_status": "source_reported_claim"},
        time,
        time,
        time,
        publication_time=time - timedelta(hours=1),
        raw_reference="https://example.org/" + key,
        schema_version="narrative-news-v1",
        unit="event_record",
    )


def persist(store, *rows):
    store.append(MarketDataBatch(rows, (), max(r.retrieved_at for r in rows)))


def assertion(store, kind, evidence=("a",), time=T, targets=()):
    return record_claim_assertion(
        store,
        claim_id="a",
        kind=kind,
        evidence_ids=evidence,
        recorded_at=time,
        rationale="Fixture curated relationship",
        target_ids=targets,
    )


def test_t1_t2_t3_reopen_correction_and_post_t(tmp_path):
    store = SQLiteInformationStore(tmp_path / "claims.db")
    persist(store, article("a"), article("b", "Ceasefire denied", T + timedelta(hours=1)))
    first = assertion(store, "official_report")
    second = assertion(store, "contradiction", ("b",), T + timedelta(hours=1))
    third = assertion(store, "correction", ("a",), T + timedelta(hours=2), (second.observation_id,))
    reopened = SQLiteInformationStore(store.path)
    s1 = claim_lifecycle(reopened.view_at(T), "a")
    assert s1["status"] == "unconfirmed" and s1["official_report"]
    assert s1["factual_truth"] == s1["independence"] == "unknown"
    assert s1["assertions"] == (first,)
    assert claim_lifecycle(reopened.view_at(T + timedelta(hours=1)), "a")["status"] == "contested"
    s3 = claim_lifecycle(reopened.view_at(T + timedelta(hours=2)), "a")
    assert not s3["opposing"] and second.observation_id in s3["retired"]
    assert len(s3["assertions"]) == 3 and third in s3["assertions"]
    before = render_analysis_information(build_analysis_information(reopened, T))
    assert "Ceasefire denied" not in before and second.observation_id not in before
    assert len(before) <= 28000


def test_syndication_and_independence_unknown_until_evidenced(tmp_path):
    store = SQLiteInformationStore(tmp_path / "claims.db")
    persist(store, article("a"), article("b"), article("c"))
    assert correlation_candidates(store.view_at(T)) == (("a", "b", "c"),)
    assertion(store, "support", ("a", "b", "c"))
    assert claim_lifecycle(store.view_at(T), "a")["independence"] == "unknown"
    assertion(store, "independence", ("a",), targets=("b",))
    assert (
        claim_lifecycle(store.view_at(T), "a")["status"] == "independently_corroborated_reporting"
    )
    assertion(store, "syndication", ("a",), targets=("b",))
    assert claim_lifecycle(store.view_at(T), "a")["independence"] == "unknown"
    assertion(store, "origin", ("b",), targets=("c",))
    assertion(store, "independence", ("a",), targets=("c",))
    assert claim_lifecycle(store.view_at(T), "a")["independence"] == "unknown"


def test_supersession_resolution_reopened_by_opposition(tmp_path):
    store = SQLiteInformationStore(tmp_path / "claims.db")
    persist(store, article("a", "New semiconductor process"), article("b", "Process disputed"))
    first = assertion(store, "confirmation")
    second = assertion(store, "supersession", targets=(first.observation_id,))
    assertion(store, "resolution", time=T + timedelta(seconds=1), targets=(second.observation_id,))
    assert (
        claim_lifecycle(store.view_at(T + timedelta(seconds=1)), "a")["status"]
        == "reported_resolved"
    )
    assertion(store, "opposition", ("b",), T + timedelta(seconds=2))
    assert claim_lifecycle(store.view_at(T + timedelta(seconds=2)), "a")["status"] == "contested"


def test_source_history_survives_article_revision(tmp_path):
    store = SQLiteInformationStore(tmp_path / "claims.db")
    original = article("a")
    persist(store, original)
    assertion(store, "support")
    persist(
        store,
        replace(
            original,
            observation_id="new",
            payload={"claim": "Corrected ceasefire"},
            retrieved_at=T + timedelta(seconds=1),
        ),
    )
    view = store.view_at(T + timedelta(seconds=1))
    assert "a" not in {r.observation_id for r in view.observations}
    assert claim_lifecycle(view, "a")["evidence"] == (original,)


@pytest.mark.parametrize(
    "kind,evidence,targets",
    [
        ("invented", ("a",), ()),
        ("support", (), ()),
        ("support", ("missing",), ()),
        ("correction", ("a",), ()),
        ("independence", ("a",), ("a",)),
        ("resolution", ("a",), ("b",)),
    ],
)
def test_invalid_relationships_rejected(tmp_path, kind, evidence, targets):
    store = SQLiteInformationStore(tmp_path / "claims.db")
    persist(store, article("a"), article("b"))
    with pytest.raises(ValueError):
        assertion(store, kind, evidence, targets=targets)


def test_future_evidence_rejected_and_idempotent(tmp_path):
    store = SQLiteInformationStore(tmp_path / "claims.db")
    persist(store, article("a"), article("b", time=T + timedelta(seconds=1)))
    with pytest.raises(ValueError):
        assertion(store, "support", ("b",))
    first = assertion(store, "support")
    assert assertion(store, "support") == first
    assert len(claim_lifecycle(store.view_at(T), "a")["assertions"]) == 1


def test_prompt_support_opposition_and_whole_record_budget(tmp_path):
    store = SQLiteInformationStore(tmp_path / "claims.db")
    persist(store, article("a"), article("b", "Ceasefire denied"))
    assertion(store, "support")
    assertion(store, "opposition", ("b",))
    prompt = render_analysis_information(build_analysis_information(store, T))
    assert '"opposing": ["b"]' in prompt and '"supporting": ["a"]' in prompt
    assert "Ceasefire denied" in prompt and '"factual_truth": "unknown"' in prompt
    for n in range(25):
        assertion(store, "support", time=T + timedelta(seconds=n))
    prompt = render_analysis_information(
        build_analysis_information(store, T + timedelta(seconds=30))
    )
    assert len(prompt) <= 28000 and "OMITTED" in prompt


def test_real_acquisition_ids_fit_support_opposition_prompt(tmp_path):
    from tradingagents.information.news import parse_news_snapshot
    from tradingagents.information.sources import BROAD_NEWS_CONFIG

    store = SQLiteInformationStore(tmp_path / "real.db")

    def snapshot(title, url, config):
        return parse_news_snapshot(
            f"<rss><channel><item><title>{title}</title><link>{url}</link></item></channel></rss>",
            config,
            retrieved_at=T,
        )

    a = snapshot("Ceasefire agreed", "https://example.org/a", BROAD_NEWS_CONFIG[0])
    b = snapshot("Ceasefire denied", "https://other.org/b", BROAD_NEWS_CONFIG[1])
    store.append(a)
    store.append(b)
    root = a.observations[0]
    for kind, rows in (("support", a), ("opposition", b)):
        record_claim_assertion(
            store,
            claim_id=root.subject,
            kind=kind,
            evidence_ids=(rows.observations[0].observation_id,),
            recorded_at=T,
            rationale="Curated relationship",
        )
    prompt = render_analysis_information(build_analysis_information(store, T))
    assert '"claim_lifecycle"' in prompt and '"opposing"' in prompt
    assert root.observation_id in prompt and b.observations[0].observation_id in prompt
    assert len(prompt) <= 28000


def test_fed_official_reporting_preserved_with_lifecycle(tmp_path):
    store = SQLiteInformationStore(tmp_path / "fed.db")
    row = replace(
        article("a"),
        schema_version="narrative-event-v1",
        payload={"claim": "Policy statement", "lifecycle": "officially_reported"},
    )
    persist(store, row)
    assertion(store, "support")
    state = claim_lifecycle(store.view_at(T), "a")
    assert state["official_report"] and state["independence"] == "unknown"
    assert state["factual_truth"] == "unknown"
