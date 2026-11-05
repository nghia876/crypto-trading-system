"""Privacy-safe reproduction of mixed historical and 35 publisher candidates.

Synthetic text/IDs only. Preserve actual envelope shapes, source types, lane
sizes, conservative availability and the official-URL format preference.
"""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from tests.test_graph_end_to_end import PromptCapturingModel, _graph, offline  # noqa: F401
from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.consumer import (
    build_analysis_information,
    render_analysis_information,
)
from tradingagents.information.narrative_events import (
    _narrative_line,
    narrative_events,
    render_narrative_events,
    selected_narrative_events,
)
from tradingagents.information.observations import Observation
from tradingagents.information.store import InformationView, SQLiteInformationStore

T = datetime(2026, 11, 5, 3, 28, tzinfo=UTC)


def article(index, domain, source, *, publisher=False, age=1, available=T):
    stamp = T - timedelta(days=age)
    return Observation(
        observation_id=f"synthetic-{source}-{index}", source_id=source,
        subject=f"article:{source}-{index}", metric="narrative.event",
        payload={
            "claim": "Synthetic public discovery headline " + str(index),
            "domain": domain,
            "source_type": "publisher_rss" if publisher else "original_specialist_news",
            "publisher_group": source, "attribution": source,
            "credibility": "unmeasured", "independent_confirmation": "unknown",
            "lifecycle": "unconfirmed", "canonical_url": "https://example.test/story",
            "content_hash": "a" * 64, "version_id": "b" * 64,
        },
        event_time=stamp, publication_time=stamp,
        first_seen_time=available, retrieved_at=available,
        raw_reference=f"https://example.test/{'story' if publisher else 'government/news'}/{source}/{index}",
        schema_version="narrative-news-v1",
    )


def mixed_rows():
    historical = tuple(article(i, domain, f"agency-{i}", age=3, available=T - timedelta(days=2))
                       for i, domain in enumerate(("WAR_GEOPOLITICS", "TECHNOLOGY", "ENERGY_GRID",
                                                  "FLOOD_DISASTER", "PUBLIC_HEALTH", "DROUGHT_WATER",
                                                  "AGRICULTURE_FOOD")))
    new = tuple(article(i, "WORLD", source, publisher=True, age=1 + i / 100)
                for source, count in (("publisher-a", 22), ("publisher-b", 13))
                for i in range(count))
    return historical, new


def test_35_candidates_sample_both_publishers_without_losing_historical_domains():
    old, new = mixed_rows()
    view = InformationView(T, old + new, ())
    candidates, selected = narrative_events(view), selected_narrative_events(view)
    assert len(candidates) == 42
    assert {r.source_id for r in selected} >= {"publisher-a", "publisher-b"}
    assert len({r.payload['domain'] for r in selected if r in old}) >= 3
    text = '\n'.join(render_narrative_events(view))
    assert f"candidates=42, included={len(selected)}, OMITTED={42 - len(selected)}" in text
    assert f"publisher-a={sum(r.source_id == 'publisher-a' for r in selected)}/22" in text
    assert f"publisher-b={sum(r.source_id == 'publisher-b' for r in selected)}/13" in text
    assert len(text) <= 6000
    # Neither credibility nor repetition/attention is an unsupported salience score.
    changed = replace(view, observations=tuple(replace(r, payload={**r.payload,
                      "credibility": "official", "attention_count": 999999}) for r in view.observations))
    assert [r.observation_id for r in selected_narrative_events(changed)] == [r.observation_id for r in selected]
    assert [r.observation_id for r in selected_narrative_events(replace(view, observations=tuple(reversed(view.observations))))] == [r.observation_id for r in selected]


def test_official_format_preference_within_lane_and_recent_bucket_before_stale():
    report = article(1, "TECHNOLOGY", "agency", age=3)
    newer_notice = replace(article(2, "TECHNOLOGY", "agency", age=1), raw_reference="https://example.test/guidance/2")
    stale = article(3, "WORLD", "publisher-a", publisher=True, age=30)
    view = InformationView(T, (stale, newer_notice, report), ())
    selected = selected_narrative_events(view)
    assert selected[0] == report  # newest alone is not the ranking rule
    assert selected.index(stale) > selected.index(report)


def test_oversized_candidate_does_not_hide_later_fit_and_accounting_is_bounded():
    old, new = mixed_rows()
    oversized = replace(new[0], payload={**new[0].payload, "claim": "x" * 7000})
    view = InformationView(T, (oversized, *new[1:], *old), ())
    selected = selected_narrative_events(view)
    assert oversized not in selected and any(r.source_id == "publisher-a" for r in selected)
    assert len('\n'.join(render_narrative_events(view))) <= 6000
    compact = _narrative_line(new[0], view)
    assert 'content_hash' not in compact and new[0].observation_id in compact
    assert '"attribution": "publisher-a"' in compact


@pytest.mark.usefixtures("offline")
def test_actual_graph_pre_post_pit_and_core_context(tmp_path, monkeypatch):
    old, new = mixed_rows()
    store = SQLiteInformationStore(tmp_path / 'evidence.sqlite3')
    funding = Observation("core-funding", "derivatives.binance.usdm.funding", "BTCUSDT",
                          "derivatives.funding_rate.usdm", {"funding_rate": "0.001"}, T, T, T)
    store.append(MarketDataBatch((*old, *new, funding), (), T))
    before = T - timedelta(microseconds=1)
    assert not {r.observation_id for r in new} & {r.observation_id for r in narrative_events(store.view_at(before))}
    for cutoff in (before, T):
        model = PromptCapturingModel()
        graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
        state, _ = graph.propagate('BTCUSDT', T.date().isoformat(), asset_type='crypto', decision_time=cutoff)
        prompts = '\n'.join(p for p in model.prompts if 'get_verified_market_snapshot' in p)
        assert prompts and len(state['analysis_information']) <= 28000
        assert max(map(len, model.prompts)) <= 28000
        selected = selected_narrative_events(store.view_at(cutoff))
        assert all(r.observation_id in prompts for r in selected)
        if cutoff == before:
            assert all(r.observation_id not in prompts for r in new)
        else:
            assert 'publisher-a' in prompts and 'publisher-b' in prompts
            assert 'core-funding' in prompts and 'OMITTED=' in prompts
    rendered = render_analysis_information(build_analysis_information(store, T))
    assert 'Macro series:' in rendered and 'Original-publisher liquidity:' in rendered
