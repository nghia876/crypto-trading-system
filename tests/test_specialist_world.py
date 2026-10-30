"""Specialist world sources share canonical polling/replay and bounded graph evidence."""

import json
from datetime import timedelta

import pytest
import requests

from tests.test_broad_news import T, rss, session_for
from tradingagents.information.binance_spot import MarketDataCollectionError
from tradingagents.information.consumer import (
    build_analysis_information,
    render_analysis_information,
)
from tradingagents.information.narrative_events import narrative_events
from tradingagents.information.news import parse_news_snapshot, poll_once
from tradingagents.information.polling import coordinate, source_gap_report
from tradingagents.information.sources import SPECIALIST_WORLD_CONFIG, WORLD_NEWS_CONFIG
from tradingagents.information.store import SQLiteInformationStore


@pytest.mark.parametrize("config", SPECIALIST_WORLD_CONFIG, ids=lambda c: c.domain)
def test_specialist_replay_correction_duplicate_provenance(tmp_path, config):
    path = tmp_path / "canonical.db"
    store = SQLiteInformationStore(path)
    text = rss("Drought flood crop energy disruption", url=config.source.endpoint + "?report=1")
    poll_once(store, (config,), poll_id="first", session=session_for(text), clock=lambda: T)
    assert not store.view_at(T - timedelta(microseconds=1)).observations
    old = store.view_at(T).observations[0]
    assert old.payload["event_occurrence_time"] is None
    assert old.payload["rights_reference"] and old.payload["attribution"] == config.source.provider
    assert old.payload["publisher_group"] == config.source.provider
    assert old.payload["independent_confirmation"] == "unknown"
    assert old.publication_time < old.first_seen_time == old.retrieved_at
    later = T + timedelta(hours=1)
    poll_once(store, (config,), poll_id="again", session=session_for(text), clock=lambda: later)
    assert len(narrative_events(store.view_at(later))) == 1
    poll_once(
        store,
        (config,),
        poll_id="fix",
        session=session_for(text.replace("disruption", "CORRECTION")),
        clock=lambda: later + timedelta(seconds=1),
    )
    reopened = SQLiteInformationStore(path)
    assert "CORRECTION" not in str(reopened.view_at(T).observations[0].payload)
    assert "CORRECTION" in str(
        narrative_events(reopened.view_at(later + timedelta(seconds=1)))[0].payload
    )
    assert len(reopened.view_at(T).source_definitions) == 1


@pytest.mark.parametrize("config", SPECIALIST_WORLD_CONFIG, ids=lambda c: c.domain)
def test_specialist_atomic_failures_missing_stale_and_future(tmp_path, config):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    with pytest.raises(MarketDataCollectionError):
        parse_news_snapshot("<rss>", config, retrieved_at=T)
    poll_once(
        store,
        (config,),
        poll_id="error",
        session=session_for(error=requests.Timeout()),
        clock=lambda: T,
    )
    report = source_gap_report(store.view_at(T), (config,))[config.domain]
    assert report["sources"][0]["poll_status"] == "unavailable"
    assert report["sources"][0]["eligible_items"] == 0
    text = rss(pub="Fri, 09 Jan 2026 13:00:00 GMT", url=config.source.endpoint)
    poll_once(store, (config,), poll_id="future", session=session_for(text), clock=lambda: T)
    assert not store.view_at(T).observations
    assert not store.view_at(T).coverage[-1].evidence_ids
    poll_once(
        store,
        (config,),
        poll_id="empty",
        session=session_for("<rss><channel/></rss>"),
        clock=lambda: T,
    )
    assert not store.view_at(T).observations
    poll_once(
        store,
        (config,),
        poll_id="old",
        session=session_for(rss(url=config.source.endpoint)),
        clock=lambda: T,
    )
    report = source_gap_report(store.view_at(T + timedelta(days=2)), (config,))[config.domain]
    assert report["sources"][0]["content_stale"] is True
    assert (
        source_gap_report(store.view_at(T - timedelta(seconds=1)), (config,))[config.domain][
            "sources"
        ][0]["poll_status"]
        == "never_polled"
    )


def test_domain_gaps_and_poll_fairness(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    before = source_gap_report(store.view_at(T))
    assert before["WILDFIRE"]["adapter_status"] == "missing_adapter"
    assert before["PUBLIC_HEALTH"]["specialist_gap"]
    assert len(WORLD_NEWS_CONFIG) <= 16
    assert all(
        not c.source.asset_scope and not c.source.authentication_required for c in WORLD_NEWS_CONFIG
    )
    first, _ = coordinate(
        store,
        SPECIALIST_WORLD_CONFIG,
        now=T,
        clock=lambda: T,
        session=session_for(rss()),
        max_sources=2,
    )
    second, _ = coordinate(
        store,
        SPECIALIST_WORLD_CONFIG,
        now=T + timedelta(minutes=16),
        clock=lambda: T + timedelta(minutes=16),
        session=session_for(rss()),
        max_sources=2,
    )
    assert len(first) == len(second) == 2
    assert {r.source_id for r in first}.isdisjoint(r.source_id for r in second)


def test_specialists_survive_macro_prompt_pressure(tmp_path):
    from tests.test_liquidity import NOW, PARSERS, h41, rrp
    from tests.test_original_macro import bls
    from tradingagents.information.original_macro import parse_bls_json

    store = SQLiteInformationStore(tmp_path / "canonical.db")
    store.append(PARSERS[0](h41(), NOW))
    store.append(PARSERS[1](rrp(), NOW))
    store.append(parse_bls_json(bls(), retrieved_at=NOW))
    for config in SPECIALIST_WORLD_CONFIG:
        store.append(
            parse_news_snapshot(
                rss(config.domain, url=config.source.endpoint), config, retrieved_at=NOW
            )
        )
    text = render_analysis_information(build_analysis_information(store, NOW))
    assert len(text) <= 28000
    # Domain rotation has a separate reservation from macro evidence.
    assert "DROUGHT_WATER" in text and "AGRICULTURE_FOOD" in text
    assert "ENERGY_GRID" in text and "FLOOD_DISASTER" in text
    assert "325.5 index" in text
    assert json.dumps(source_gap_report(store.view_at(NOW)))


def test_declared_encoding_and_interrupted_snapshot(tmp_path):
    from tradingagents.information.news import fetch_news_snapshot

    config = SPECIALIST_WORLD_CONFIG[2]
    text = '<?xml version="1.0" encoding="ISO-8859-1"?>' + rss(
        "Energy caf\u00e9", url=config.source.endpoint
    )
    session = session_for("unused")
    response = session.get.return_value.__enter__.return_value
    response.iter_content.return_value = [text.encode("iso-8859-1")]
    decoded = fetch_news_snapshot(config, session)
    assert (
        parse_news_snapshot(decoded, config, retrieved_at=T).observations[0].payload["claim"]
        == "Energy caf\u00e9"
    )
    response.iter_content.return_value = [text.replace("ISO-8859-1", "UTF-16").encode()]
    with pytest.raises(MarketDataCollectionError, match="encoding"):
        fetch_news_snapshot(config, session)

    def broken(_):
        yield b"<rss><channel>"
        raise requests.ConnectionError("interrupted")

    response.iter_content.side_effect = broken
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    result = poll_once(store, (config,), poll_id="interrupted", session=session, clock=lambda: T)
    assert result[0].status.value == "unavailable"
    assert not SQLiteInformationStore(store.path).view_at(T).observations


def test_specialist_lifecycle_annotation_keeps_identity(tmp_path, monkeypatch):
    import importlib

    module = importlib.import_module("tradingagents.information.narrative_events")
    config = SPECIALIST_WORLD_CONFIG[0]
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    batch = parse_news_snapshot(rss(url=config.source.endpoint), config, retrieved_at=T)
    store.append(batch)
    monkeypatch.setattr(module, "lifecycle_prompt", lambda view, subject: {"status": "unconfirmed"})
    text = module._narrative_line(batch.observations[0], store.view_at(T))
    assert batch.observations[0].subject in text and "claim_lifecycle" in text


def test_specialist_excludes_external_article_hosts():
    config = SPECIALIST_WORLD_CONFIG[0]
    for host in ("example.org", "usgs.gov.example.org"):
        external = rss(url="https://" + host + "/story")
        batch = parse_news_snapshot(external, config, retrieved_at=T)
        assert not batch.observations
        combined = rss(url=config.source.endpoint).replace(
            "</channel>", external.split("<channel>")[1].split("</channel>")[0] + "</channel>"
        )
        batch = parse_news_snapshot(combined, config, retrieved_at=T)
        assert len(batch.observations) == 1
        assert batch.observations[0].payload["excluded_article_count"] == 1
        assert batch.observations[0].payload["snapshot_item_count"] == 2
