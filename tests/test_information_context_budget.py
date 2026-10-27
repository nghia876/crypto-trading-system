"""Analyst context retains core evidence under large replay histories."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from tradingagents.information import (
    BLS_RELEASE_CALENDAR_SOURCE,
    FRED_SERIES,
    CoverageRecord,
    CoverageStatus,
    InformationView,
    Observation,
    ScheduledMacroEvent,
    Source,
    SourceStatus,
    build_btc_market_state,
    parse_fred_graph_csv,
)
from tradingagents.information.consumer import (
    MAX_ANALYSIS_INFORMATION_CHARS,
    AnalysisInformationInput,
    render_analysis_information,
)


def test_large_histories_are_bounded_deterministic_and_keep_core_evidence():
    cutoff = datetime(2026, 1, 9, 12, tzinfo=UTC)
    funding = Observation(
        observation_id="core-funding",
        source_id="derivatives.binance.usdm.funding",
        subject="BTCUSDT",
        metric="derivatives.funding_rate.usdm",
        payload={"funding_rate": "0.001"},
        event_time=cutoff - timedelta(days=1),
        first_seen_time=cutoff,
        retrieved_at=cutoff,
    )
    spec = FRED_SERIES[0]
    macro = parse_fred_graph_csv(
        f"observation_date,{spec.series_id}\n2026-01-08,100\n",
        spec=spec,
        retrieved_at=cutoff,
    ).observations[0]
    event = ScheduledMacroEvent(
        event_id="core-event",
        title="CPI",
        event_type="cpi_release",
        scheduled_at=cutoff + timedelta(days=1),
        source=BLS_RELEASE_CALENDAR_SOURCE,
        raw_reference="https://example.test",
    ).to_observation(retrieved_at=cutoff)
    coverage = tuple(
        CoverageRecord(
            f"coverage-{i}",
            "source",
            "BTCUSDT",
            "metric",
            cutoff,
            CoverageStatus.STALE if i % 2 else CoverageStatus.UNKNOWN,
            "detail" * 100,
            (funding.observation_id,),
        )
        for i in range(1000)
    )
    sources = tuple(
        (
            Source(
                f"source-{i:04d}",
                "test",
                "provider",
                "https://example.test",
                "caller-driven",
                status=SourceStatus.UNAVAILABLE,
                limitations=("limitation" * 100,),
            ),
            cutoff,
        )
        for i in range(1000)
    )
    sources += (
        (
            Source(
                funding.source_id,
                "exchange",
                "core funding provider",
                "https://example.test",
                "caller-driven",
                version="core-version",
                status=SourceStatus.DEGRADED,
                limitations=("core source limitation",),
            ),
            cutoff,
        ),
    )
    extra_events = tuple(
        replace(
            event,
            observation_id=f"extra-event-{i:04d}",
            payload={
                **event.payload,
                "event_id": f"extra-{i}",
                "scheduled_at": (cutoff + timedelta(days=2)).isoformat(),
                "title": "large event " * 30,
            },
        )
        for i in range(1000)
    )
    view = InformationView(cutoff, (funding, macro, event, *extra_events), (), coverage, sources)
    state = build_btc_market_state(view)
    rendered = render_analysis_information(AnalysisInformationInput(view, state))
    assert len(rendered) <= MAX_ANALYSIS_INFORMATION_CHARS
    assert "OMITTED" in rendered
    assert "stale=500" in rendered and "unknown=500" in rendered
    assert "unavailable=1000" in rendered
    assert "core-version" in rendered and "core source limitation" in rendered
    assert "Funding rate: 0.001; freshness: stale" in rendered
    assert "BTC spot close: unknown" in rendered
    for observation in (funding, macro, event):
        assert f"- {observation.observation_id}: {observation.source_id}" in rendered
    reversed_view = replace(
        view,
        coverage=coverage[::-1],
        source_definitions=sources[::-1],
        observations=view.observations[::-1],
    )
    assert render_analysis_information(AnalysisInformationInput(reversed_view, state)) == rendered


def test_oversized_record_is_omitted_whole_with_disclosure():
    cutoff = datetime(2026, 1, 9, tzinfo=UTC)
    record = CoverageRecord("huge", "s", "BTCUSDT", "m", cutoff, CoverageStatus.STALE, "x" * 100000)
    view = InformationView(cutoff, (), (), (record,))
    rendered = render_analysis_information(
        AnalysisInformationInput(view, build_btc_market_state(view))
    )
    assert len(rendered) <= MAX_ANALYSIS_INFORMATION_CHARS
    assert "OMITTED 1 of 1 records" in rendered
    assert "stale=1" in rendered
    assert "omission does not establish absence" in rendered


def test_spot_history_keeps_latest_evidence_and_discloses_sampling():
    cutoff = datetime(2026, 1, 9, tzinfo=UTC)
    view = InformationView(cutoff, (), ())
    state = build_btc_market_state(view)
    state = replace(
        state,
        spot=replace(
            state.spot,
            evidence_observation_ids=tuple(f"spot-{i}" for i in range(100)),
        ),
    )
    rendered = render_analysis_information(AnalysisInformationInput(view, state))
    assert len(rendered) <= MAX_ANALYSIS_INFORMATION_CHARS
    assert "evidence IDs (latest 21 of 100)" in rendered
    assert "spot-99" in rendered
    assert "spot-78," not in rendered
