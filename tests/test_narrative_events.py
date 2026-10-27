"""Deterministic official announcement parsing, replay and prompt bounds."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
import requests

from tradingagents.information.binance_spot import MarketDataCollectionError
from tradingagents.information.consumer import (
    build_analysis_information,
    render_analysis_information,
)
from tradingagents.information.narrative_events import (
    FedMonetaryCollector,
    narrative_events,
    parse_fed_monetary_feed,
)
from tradingagents.information.store import SQLiteInformationStore

T = datetime(2026, 1, 9, 12, tzinfo=UTC)


def feed(title="Federal Reserve issues FOMC statement", suffix="20260109a", pub=None):
    pub = pub or "Fri, 09 Jan 2026 10:00:00 GMT"
    return (
        f'<rss version="2.0"><channel><item><title>{title}</title>'
        f"<link>https://www.federalreserve.gov/newsevents/pressreleases/monetary{suffix}.htm</link>"
        f"<pubDate>{pub}</pubDate></item></channel></rss>"
    )


def test_identity_dedup_versions_and_persistent_replay(tmp_path):
    store = SQLiteInformationStore(tmp_path / "events.db")
    first = parse_fed_monetary_feed(feed(), retrieved_at=T)
    duplicate = feed().replace(
        "</channel>", feed().split("<channel>")[1].split("</channel>")[0] + "</channel>"
    )
    assert len(parse_fed_monetary_feed(duplicate, retrieved_at=T).observations) == 1
    store.append(first)
    store.append(first)  # idempotent snapshot
    later = T + timedelta(hours=1)
    revision = parse_fed_monetary_feed(feed("Corrected policy headline"), retrieved_at=later)
    store.append(revision)
    store.append(revision)  # retry after automatic revision linkage
    store = SQLiteInformationStore(tmp_path / "events.db")
    assert not narrative_events(store.view_at(T - timedelta(microseconds=1)))
    assert narrative_events(store.view_at(T))[0] == first.observations[0]
    current = narrative_events(store.view_at(later))[0]
    assert current.observation_id == revision.observations[0].observation_id
    assert current.supersedes_observation_id == first.observations[0].observation_id
    assert first.observations[0].subject == revision.observations[0].subject
    assert first.observations[0].observation_id != revision.observations[0].observation_id
    assert len(store.view_at(later).observations) == 1
    text = render_analysis_information(build_analysis_information(store, T))
    assert "Corrected policy" not in text
    assert first.observations[0].observation_id in text
    assert first.observations[0].payload["verified_facts"] == ()
    assert "UNKNOWN" in text and "No causal price inference" in text


def test_future_publication_and_repetition_never_confirm(tmp_path):
    store = SQLiteInformationStore(tmp_path / "events.db")
    future = parse_fed_monetary_feed(feed(pub="Sat, 10 Jan 2026 10:00:00 GMT"), retrieved_at=T)
    store.append(future)
    assert not narrative_events(store.view_at(T))
    rendered = render_analysis_information(build_analysis_information(store, T))
    assert future.observations[0].observation_id not in rendered
    assert future.observations[0].payload["claim"] not in rendered
    store.append(parse_fed_monetary_feed(feed(), retrieved_at=T))
    store.append(parse_fed_monetary_feed(feed(), retrieved_at=T + timedelta(seconds=1)))
    events = narrative_events(store.view_at(T + timedelta(seconds=1)))
    assert len(events) == 1
    view = store.view_at(T + timedelta(seconds=1))
    import sqlite3

    with sqlite3.connect(store.path) as connection:
        persisted_ids = {
            row[0] for row in connection.execute("SELECT observation_id FROM observations")
        }
    assert all(
        evidence in persisted_ids
        for coverage in view.coverage
        for evidence in coverage.evidence_ids
    )
    assert events[0].payload["independent_confirmation"] == "unknown"
    assert events[0].payload["confirmed_at"] is None
    assert events[0].payload["reaction_at"] is None


@pytest.mark.parametrize(
    "xml",
    [
        "bad xml",
        "<html/>",
        "<!DOCTYPE rss><rss><channel/></rss>",
        feed(pub="unknown"),
        feed(pub="Fri, 09 Jan 2026 10:00:00"),
        feed().replace("www.federalreserve.gov", "evil.test"),
        feed("x" * 2001),
        "x" * 2_000_001,
        "<rss><channel>"
        + feed().split("<channel>")[1].split("</channel>")[0] * 201
        + "</channel></rss>",
    ],
    ids=["xml", "html", "dtd", "bad-date", "naive-date", "host", "title", "size", "items"],
)
def test_invalid_snapshot_rejected(xml):
    with pytest.raises(MarketDataCollectionError):
        parse_fed_monetary_feed(xml, retrieved_at=T)


def test_naive_retrieval_rejected_and_empty_is_unknown():
    with pytest.raises(ValueError):
        parse_fed_monetary_feed(feed(), retrieved_at=T.replace(tzinfo=None))
    batch = parse_fed_monetary_feed("<rss><channel/></rss>", retrieved_at=T)
    assert not batch.observations
    assert batch.coverage[0].status.value == "unknown"


def test_collector_stream_limits_and_errors():
    session = MagicMock()
    response = session.get.return_value.__enter__.return_value
    response.iter_content.return_value = [feed().encode()]
    collector = FedMonetaryCollector(session=session, clock=lambda: T)
    assert len(collector.collect().observations) == 1
    assert session.get.call_args.kwargs["stream"] is True
    response.iter_content.return_value = [b"x" * 2_000_001]
    with pytest.raises(MarketDataCollectionError, match="oversized"):
        collector.collect()
    session.get.side_effect = requests.Timeout("offline")
    with pytest.raises(MarketDataCollectionError, match="request failed"):
        collector.collect()


def test_large_events_fit_total_budget_and_omit_whole_records(tmp_path):
    store = SQLiteInformationStore(tmp_path / "events.db")
    for i in range(40):
        store.append(
            parse_fed_monetary_feed(feed("x" * 1000, str(i)), retrieved_at=T + timedelta(seconds=i))
        )
    info = build_analysis_information(store, T + timedelta(minutes=1))
    text = render_analysis_information(info)
    assert text == render_analysis_information(info)
    assert len(text) <= 28000
    section = text.split("Narrative events:")[1].split("Recorded coverage:")[0]
    assert "OMITTED" in section
    assert '"event_id"' in section
    assert len(section) <= 4000


def test_query_variants_correlate_but_distinct_releases_do_not(tmp_path):
    store = SQLiteInformationStore(tmp_path / "identity.db")
    original = parse_fed_monetary_feed(feed(), retrieved_at=T)
    variant = parse_fed_monetary_feed(
        feed().replace(".htm</link>", ".htm?utm_source=rss#copy</link>"),
        retrieved_at=T + timedelta(seconds=1),
    )
    distinct = parse_fed_monetary_feed(feed(suffix="20260109b"), retrieved_at=T)
    assert original.observations[0].subject == variant.observations[0].subject
    assert original.observations[0].subject != distinct.observations[0].subject
    for batch in (original, variant, distinct):
        store.append(batch)
    events = narrative_events(store.view_at(T + timedelta(seconds=1)))
    assert len(events) == 2
    assert {row.payload["publisher_group"] for row in events} == {"federal_reserve_board"}
    assert all(row.payload["independent_confirmation"] == "unknown" for row in events)


def test_future_revision_appended_first_cannot_hide_past(tmp_path):
    store = SQLiteInformationStore(tmp_path / "order.db")
    future = parse_fed_monetary_feed(feed("Future correction"), retrieved_at=T + timedelta(days=1))
    past = parse_fed_monetary_feed(feed(), retrieved_at=T)
    store.append(future)
    store.append(past)
    assert (
        narrative_events(store.view_at(T))[0].observation_id == past.observations[0].observation_id
    )
    assert (
        narrative_events(store.view_at(T + timedelta(days=1)))[0].observation_id
        == future.observations[0].observation_id
    )
