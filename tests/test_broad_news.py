"""Broad discovery, durable polling, conservative provenance and time-bound replay."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
import requests

from tradingagents.information.binance_spot import CoverageStatus, MarketDataCollectionError
from tradingagents.information.consumer import (
    build_analysis_information,
    render_analysis_information,
)
from tradingagents.information.narrative_events import (
    narrative_events,
    parse_fed_monetary_feed,
    selected_narrative_events,
)
from tradingagents.information.news import canonical_article_url, parse_news_snapshot, poll_once
from tradingagents.information.sources import BROAD_NEWS_CONFIG
from tradingagents.information.store import SQLiteInformationStore

T = datetime(2026, 1, 9, 12, tzinfo=UTC)
WAR, TECH, G_WAR, G_TECH = BROAD_NEWS_CONFIG


def rss(
    title="Ceasefire talks resume",
    url="https://example.org/story?id=7",
    pub="Fri, 09 Jan 2026 10:00:00 GMT",
):
    return f"<rss><channel><item><title>{title}</title><link>{url}</link><pubDate>{pub}</pubDate></item></channel></rss>"


def atom(title="New semiconductor fabrication process", updated="2026-01-09T11:00:00Z"):
    return (
        f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>{title}</title>'
        '<link href="https://example.org/chips"/><published>2026-01-09T10:00:00Z</published>'
        f"<updated>{updated}</updated></entry></feed>"
    )


def session_for(text=None, error=None, status=200):
    session = MagicMock()
    if error:
        session.get.side_effect = error
    else:
        response = session.get.return_value.__enter__.return_value
        response.status_code = status
        response.iter_content.return_value = [text.encode()]
    return session


def test_non_btc_discovery_defaults_and_atom():
    assert {x.domain for x in BROAD_NEWS_CONFIG} == {"WAR_GEOPOLITICS", "TECHNOLOGY"}
    assert all(
        not x.source.authentication_required and not x.source.asset_scope for x in BROAD_NEWS_CONFIG
    )
    assert all(
        "btc" not in x.query.lower() and "price" not in x.query.lower() for x in BROAD_NEWS_CONFIG
    )
    war = parse_news_snapshot(rss(), WAR, retrieved_at=T).observations[0]
    tech = parse_news_snapshot(atom(), replace(TECH, format="atom"), retrieved_at=T).observations[0]
    assert war.payload["domain"] == "WAR_GEOPOLITICS"
    assert tech.payload["domain"] == "TECHNOLOGY"
    assert tech.payload["updated_at"] == "2026-01-09T11:00:00+00:00"
    for row in (war, tech):
        assert row.payload["origin"] == row.payload["syndication"] == "unknown"
        assert row.payload["verified_facts"] == ()
        assert row.payload["independent_confirmation"] == "unknown"
        assert row.payload["snapshot_hash"] and row.payload["content_hash"]
        assert row.transformations[0].version == "1"


def test_url_identity_preserves_queries_and_original():
    a = canonical_article_url("https://EXAMPLE.org/story?id=1&utm_source=x#part")
    assert a == "https://example.org/story?id=1&utm_source=x"
    assert a != canonical_article_url("https://example.org/story?id=2&utm_source=x")
    row = parse_news_snapshot(
        rss(url="https://EXAMPLE.org/story?id=1#part"), WAR, retrieved_at=T
    ).observations[0]
    assert row.raw_reference.endswith("#part")
    assert row.payload["canonical_url"].endswith("?id=1")


def test_gdelt_overlap_is_one_candidate_not_confirmation(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    a = parse_news_snapshot(rss(), WAR, retrieved_at=T)
    text = '{"articles":[{"title":"Ceasefire talks resume","url":"https://example.org/story?id=7","seendate":"20260108T010000Z","domain":"example.org"}]}'
    b = parse_news_snapshot(text, G_WAR, retrieved_at=T + timedelta(seconds=1))
    store.append(a)
    store.append(b)
    assert a.observations[0].subject == b.observations[0].subject
    assert (
        a.observations[0].payload["version_id"] != b.observations[0].payload["version_id"]
    )  # different supplied date fields
    assert b.observations[0].publication_time is None  # seendate is NOT publication
    assert b.observations[0].available_at == T + timedelta(seconds=1)
    selected = narrative_events(store.view_at(T + timedelta(seconds=1)))
    assert len(selected) == 1
    assert selected[0].payload["independent_confirmation"] == "unknown"
    assert len(store.view_at(T + timedelta(seconds=1)).observations) == 2


@pytest.mark.parametrize(
    "pub",
    ["", "nonsense", "2026-01-09T10:00:00", "Fri, 09 Jan 2026 10:00:00"],
    ids=["missing", "bad", "naiveiso", "naiverss"],
)
def test_unknown_publication_never_backdates(pub):
    row = parse_news_snapshot(rss(pub=pub), WAR, retrieved_at=T).observations[0]
    assert row.publication_time is None
    assert row.payload["publication_status"] == "unknown_missing_or_invalid"
    assert row.available_at == T


def test_future_dates_and_anomalies_replay(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    future = parse_news_snapshot(atom(updated="2026-01-09T13:00:00Z"), TECH, retrieved_at=T)
    store.append(future)
    assert not narrative_events(store.view_at(T))
    assert not narrative_events(store.view_at(T + timedelta(hours=1) - timedelta(microseconds=1)))
    assert narrative_events(store.view_at(T + timedelta(hours=1)))
    assert "future_update" in future.observations[0].payload["date_anomalies"]
    old_update = parse_news_snapshot(atom(updated="2026-01-08T13:00:00Z"), TECH, retrieved_at=T)
    assert "update_before_publication" in old_update.observations[0].payload["date_anomalies"]
    published_future = parse_news_snapshot(
        rss(pub="Fri, 09 Jan 2026 13:00:00 GMT"), WAR, retrieved_at=T
    )
    assert published_future.observations[0].available_at == T + timedelta(hours=1)


@pytest.mark.parametrize(
    "text,config",
    [
        ("<rss>", WAR),
        ("<!DOCTYPE rss><rss/>", WAR),
        ("<!ENTITY x 'oops'><rss/>", WAR),
        ('{"error":"rate limit"}', G_WAR),
        ('{"articles":{}}', G_WAR),
        (rss(url="file:///secret"), WAR),
        (rss(title="x" * 2001), WAR),
        (rss(), replace(WAR, max_bytes=5)),
        (
            rss().replace(
                "</channel>", rss().split("<channel>")[1].split("</channel>")[0] + "</channel>"
            ),
            replace(WAR, max_items=1),
        ),
    ],
    ids=["xml", "dtd", "entity", "gdelt-error", "gdelt-shape", "url", "title", "bytes", "items"],
)
def test_atomic_rejections(text, config):
    with pytest.raises(MarketDataCollectionError):
        parse_news_snapshot(text, config, retrieved_at=T)


def test_poll_outcomes_reopen_retry_correction_and_local_first_seen(tmp_path):
    path = tmp_path / "e.db"
    store = SQLiteInformationStore(path)
    first_session = session_for(rss())
    first = poll_once(store, (WAR,), poll_id="one", session=first_session, clock=lambda: T)[0]
    assert first.status == CoverageStatus.PRESENT
    assert first_session.get.call_count == 1
    assert first_session.get.call_args.kwargs["timeout"] == (3.05, 10)
    assert first_session.get.call_args.kwargs["allow_redirects"] is False
    store = SQLiteInformationStore(path)
    retry_session = MagicMock()
    assert poll_once(store, (WAR,), poll_id="one", session=retry_session, clock=lambda: T) == (
        first,
    )
    retry_session.get.assert_not_called()
    later = T + timedelta(microseconds=1)
    poll_once(
        store,
        (WAR,),
        poll_id="two",
        session=session_for(rss("Corrected ceasefire claim")),
        clock=lambda: later,
    )
    current = narrative_events(store.view_at(later))[0]
    assert current.first_seen_time == T and current.retrieved_at == later
    assert current.payload["claim"] == "Corrected ceasefire claim"
    assert narrative_events(store.view_at(T))[0].payload["claim"] == "Ceasefire talks resume"
    assert not narrative_events(store.view_at(T - timedelta(microseconds=1)))
    third = T + timedelta(seconds=1)
    poll_once(
        store,
        (WAR,),
        poll_id="three",
        session=session_for(rss("Corrected ceasefire claim")),
        clock=lambda: third,
    )
    repeated = narrative_events(store.view_at(third))[0]
    assert repeated.payload["version_id"] == current.payload["version_id"]
    assert repeated.payload["independent_confirmation"] == "unknown"
    empty = poll_once(
        store,
        (TECH,),
        poll_id="empty",
        session=session_for("<rss><channel/></rss>"),
        clock=lambda: third,
    )[0]
    assert empty.status == CoverageStatus.UNKNOWN and '"outcome": "empty"' in empty.detail
    failed = poll_once(
        store,
        (TECH,),
        poll_id="failed",
        session=session_for(error=requests.Timeout()),
        clock=lambda: third,
    )[0]
    assert failed.status == CoverageStatus.UNAVAILABLE
    assert not failed.evidence_ids
    bad = poll_once(
        store, (TECH,), poll_id="bad", session=session_for("<invalid/>"), clock=lambda: third
    )[0]
    assert bad.status == CoverageStatus.UNAVAILABLE
    assert SQLiteInformationStore(path).coverage_by_id(failed.coverage_id) == failed


def test_gdelt_query_and_failure_isolation_and_limits(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    session = session_for('{"articles":[]}')
    poll_once(store, (G_WAR,), poll_id="gdelt", session=session, clock=lambda: T)
    params = session.get.call_args.kwargs["params"]
    assert params["query"] == G_WAR.query and params["maxrecords"] == G_WAR.max_items
    for label, session in (
        ("redirect", session_for("", status=302)),
        ("bytes", session_for("x" * 11)),
    ):
        config = replace(WAR, max_bytes=10)
        result = poll_once(store, (config,), poll_id=label, session=session, clock=lambda: T)[0]
        assert result.status == CoverageStatus.UNAVAILABLE
    sequence = MagicMock()
    good = session_for("<rss><channel/></rss>").get.return_value
    sequence.get.side_effect = [requests.HTTPError("429"), good]
    results = poll_once(store, (WAR, TECH), poll_id="partial", session=sequence, clock=lambda: T)
    assert [x.status for x in results] == [CoverageStatus.UNAVAILABLE, CoverageStatus.UNKNOWN]
    assert sequence.get.call_count == 2
    # Changed request config is a different durable outcome even with the same caller ID.
    assert replace(WAR, version="2").fingerprint != WAR.fingerprint


def test_mixed_fed_news_domain_budget_and_exact_metadata(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    fed = "<rss><channel><item><title>Fed policy</title><link>https://www.federalreserve.gov/newsevents/pressreleases/monetary20260109.htm</link><pubDate>Fri, 09 Jan 2026 10:00:00 GMT</pubDate></item></channel></rss>"
    store.append(parse_fed_monetary_feed(fed, retrieved_at=T))
    for config in (WAR, TECH):
        for i in range(20):
            store.append(
                parse_news_snapshot(
                    rss(
                        f"{config.domain} headline {i}", f"https://example.org/{config.domain}/{i}"
                    ),
                    config,
                    retrieved_at=T,
                )
            )
    info = build_analysis_information(store, T)
    selected = selected_narrative_events(info.view)
    assert {x.payload.get("domain", "MONETARY") for x in selected} == {
        "MONETARY",
        "WAR_GEOPOLITICS",
        "TECHNOLOGY",
    }
    rendered = render_analysis_information(info)
    assert len(rendered) <= 28000 and "OMITTED" in rendered
    narrative = rendered.split("Narrative events:\n")[1].split("\nRecorded coverage:")[0]
    assert len(narrative) < 6000
    metadata = rendered.split("Evidence metadata (schema and unit):\n")[1]
    for row in selected:
        assert row.observation_id in narrative and row.observation_id in metadata
    assert rendered == render_analysis_information(info)


def test_aware_validation(tmp_path):
    with pytest.raises(ValueError, match="timezone-aware"):
        parse_news_snapshot(rss(), WAR, retrieved_at=T.replace(tzinfo=None))
    for kwargs in ({"max_items": 0}, {"max_bytes": 2_000_001}, {"domain": "BTC"}):
        with pytest.raises(ValueError):
            replace(WAR, **kwargs)


def test_out_of_order_append_and_changed_publication_correction(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    early = parse_news_snapshot(rss(), WAR, retrieved_at=T)
    late = parse_news_snapshot(
        rss("Changed timestamp claim", pub="Fri, 09 Jan 2026 09:00:00 GMT"),
        WAR,
        retrieved_at=T + timedelta(seconds=1),
    )
    store.append(late)
    store.append(early)
    assert narrative_events(store.view_at(T))[0].payload["claim"] == "Ceasefire talks resume"
    assert (
        narrative_events(store.view_at(T + timedelta(seconds=1)))[0].payload["claim"]
        == "Changed timestamp claim"
    )
    assert early.observations[0].subject == late.observations[0].subject
    assert early.observations[0].payload["version_id"] != late.observations[0].payload["version_id"]


def test_config_definition_and_future_coverage_evidence(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    future = rss(pub="Fri, 09 Jan 2026 13:00:00 GMT")
    outcome = poll_once(
        store, (WAR,), poll_id="future", session=session_for(future), clock=lambda: T
    )[0]
    assert outcome.status == CoverageStatus.UNKNOWN and not outcome.evidence_ids
    assert not store.view_at(T - timedelta(microseconds=1)).coverage
    source, observed = store.view_at(T).source_definitions[0]
    assert dict(source.metadata)["config_fingerprint"] == WAR.fingerprint
    assert dict(source.metadata)["max_items"] == str(WAR.max_items)
    assert observed == T
    assert replace(WAR, query="different").source_definition.version != source.version
    empty = poll_once(
        store,
        (WAR,),
        poll_id="changed",
        session=session_for("<rss><channel/></rss>"),
        clock=lambda: T,
    )[0]
    assert empty.coverage_id != outcome.coverage_id
