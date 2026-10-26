"""Deterministic BTC spot state tests over point-in-time information views."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from tradingagents.information import (
    BINANCE_SPOT_SOURCE,
    BINANCE_USDM_FUNDING_SOURCE,
    BINANCE_USDM_OPEN_INTEREST_SOURCE,
    BLS_RELEASE_CALENDAR_SOURCE,
    BTCSpotMarketState,
    InformationView,
    MarketDataBatch,
    MarketDataGap,
    Observation,
    ScheduledMacroEvent,
    SQLiteInformationStore,
    build_btc_market_state,
    build_btc_spot_market_state,
)

BASE = datetime(2026, 1, 1, tzinfo=UTC)


def candle(index: int, close: str, available_at: datetime | None = None) -> Observation:
    event_time = BASE + timedelta(minutes=index)
    seen_at = available_at or event_time + timedelta(minutes=2)
    return Observation(
        observation_id=f"candle-{index}",
        source_id=BINANCE_SPOT_SOURCE.source_id,
        subject="BTCUSDT",
        metric="spot_ohlcv.1m",
        payload={
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "base_volume": "1.25",
            "quote_volume": "125.0",
            "trade_count": 7,
            "close_time": (
                event_time + timedelta(minutes=1) - timedelta(milliseconds=1)
            ).isoformat(),
        },
        event_time=event_time,
        first_seen_time=seen_at,
        retrieved_at=seen_at,
    )


def test_state_is_reproducible_and_reports_return_volatility_freshness_and_evidence():
    decision_time = BASE + timedelta(minutes=6)
    observations = (
        candle(0, "100", BASE + timedelta(minutes=1)),
        candle(1, "101", BASE + timedelta(minutes=2)),
        candle(2, "100", BASE + timedelta(minutes=3)),
    )
    view = InformationView(decision_time, observations, ())

    state = build_btc_spot_market_state(view)

    assert state == build_btc_spot_market_state(view)
    assert state.latest_close == Decimal("100")
    assert state.latest_open == Decimal("100")
    assert state.latest_high == Decimal("100")
    assert state.latest_low == Decimal("100")
    assert state.latest_base_volume == Decimal("1.25")
    assert state.latest_quote_volume == Decimal("125.0")
    assert state.latest_trade_count == 7
    assert state.one_bar_return_pct == Decimal("-100") / Decimal("101")
    assert state.realized_volatility_pct is not None
    assert state.volatility_return_count == 2
    assert state.freshness == "stale"
    assert state.unresolved_gap_count == 0
    assert state.evidence_observation_ids == ("candle-0", "candle-1", "candle-2")


def test_state_excludes_observations_unavailable_at_cutoff_even_when_event_time_is_old():
    decision_time = BASE + timedelta(minutes=3)
    late = candle(0, "100", BASE + timedelta(minutes=4))

    state = build_btc_spot_market_state(InformationView(decision_time, (late,), ()))

    assert state == BTCSpotMarketState(
        decision_time=decision_time,
        candle_count=0,
        latest_event_time=None,
        latest_available_at=None,
        latest_open=None,
        latest_high=None,
        latest_low=None,
        latest_close=None,
        latest_base_volume=None,
        latest_quote_volume=None,
        latest_trade_count=None,
        one_bar_return_pct=None,
        realized_volatility_pct=None,
        volatility_return_count=0,
        latest_bar_age=None,
        freshness="unknown",
        unresolved_gap_count=0,
        evidence_observation_ids=(),
    )


def test_state_excludes_unclosed_candles_and_marks_fresh_bar():
    decision_time = BASE + timedelta(minutes=2, seconds=30)
    closed = candle(0, "100", BASE + timedelta(minutes=1))
    unclosed = candle(2, "120", BASE + timedelta(minutes=2))

    state = build_btc_spot_market_state(
        InformationView(decision_time, (closed, unclosed), ()),
        stale_after=timedelta(minutes=3),
    )

    assert state.candle_count == 1
    assert state.latest_close == Decimal("100")
    assert state.freshness == "fresh"


def test_returns_do_not_bridge_missing_candle_intervals():
    decision_time = BASE + timedelta(minutes=5)
    observations = (
        candle(0, "100", BASE + timedelta(minutes=1)),
        candle(2, "102", BASE + timedelta(minutes=3)),
    )

    state = build_btc_spot_market_state(InformationView(decision_time, observations, ()))

    assert state.latest_close == Decimal("102")
    assert state.one_bar_return_pct is None
    assert state.realized_volatility_pct is None
    assert state.volatility_return_count == 0


def test_volatility_window_uses_only_the_contiguous_suffix_after_a_gap():
    decision_time = BASE + timedelta(minutes=7)
    observations = (
        candle(0, "100", BASE + timedelta(minutes=1)),
        candle(1, "110", BASE + timedelta(minutes=2)),
        candle(3, "90", BASE + timedelta(minutes=4)),
        candle(4, "99", BASE + timedelta(minutes=5)),
        candle(5, "108.9", BASE + timedelta(minutes=6)),
    )

    state = build_btc_spot_market_state(InformationView(decision_time, observations, ()))

    assert state.one_bar_return_pct == Decimal("10")
    assert state.volatility_return_count == 2
    assert state.realized_volatility_pct == Decimal(0)


def test_state_counts_only_btc_spot_gaps_and_rejects_invalid_parameters():
    decision_time = BASE + timedelta(minutes=3)
    btc_gap = MarketDataGap("BTCUSDT", "spot_ohlcv.1m", BASE, decision_time)
    other_gap = MarketDataGap("ETHUSDT", "spot_ohlcv.1m", BASE, decision_time)
    state = build_btc_spot_market_state(InformationView(decision_time, (), (btc_gap, other_gap)))

    assert state.unresolved_gap_count == 1
    with pytest.raises(ValueError, match="volatility_window"):
        build_btc_spot_market_state(InformationView(decision_time, (), ()), volatility_window=0)


def test_state_rejects_internally_inconsistent_ohlc():
    decision_time = BASE + timedelta(minutes=3)
    invalid = replace(
        candle(0, "100", BASE + timedelta(minutes=1)),
        payload={
            **candle(0, "100", BASE + timedelta(minutes=1)).payload,
            "high": "99",
        },
    )

    with pytest.raises(ValueError, match="high is inconsistent"):
        build_btc_spot_market_state(InformationView(decision_time, (invalid,), ()))


def test_combined_state_replays_funding_by_availability_and_open_interest_by_exchange_time():
    from tradingagents.information import (
        BINANCE_USDM_FUNDING_SOURCE,
        BINANCE_USDM_OPEN_INTEREST_SOURCE,
        TREASURY_DGS10_SOURCE,
    )

    decision_time = BASE + timedelta(days=1)
    old_funding_event = BASE + timedelta(hours=8)
    funding = Observation(
        observation_id="funding-backfill",
        source_id=BINANCE_USDM_FUNDING_SOURCE.source_id,
        subject="BTCUSDT",
        metric="derivatives.funding_rate.usdm",
        payload={"funding_rate": "-0.0001"},
        event_time=old_funding_event,
        first_seen_time=decision_time + timedelta(seconds=1),
        retrieved_at=decision_time + timedelta(seconds=1),
    )
    oi_time = decision_time - timedelta(minutes=1)
    open_interest = Observation(
        observation_id="oi-current",
        source_id=BINANCE_USDM_OPEN_INTEREST_SOURCE.source_id,
        subject="BTCUSDT",
        metric="derivatives.open_interest.usdm",
        payload={"open_interest": "123.45"},
        event_time=oi_time,
        first_seen_time=decision_time - timedelta(seconds=1),
        retrieved_at=decision_time - timedelta(seconds=1),
    )

    treasury_yield = Observation(
        observation_id="treasury-dgs10",
        source_id=TREASURY_DGS10_SOURCE.source_id,
        subject="US",
        metric="macro.treasury_10y_par_yield_pct",
        payload={"yield_pct": "4.25"},
        event_time=decision_time - timedelta(days=1),
        first_seen_time=decision_time - timedelta(seconds=1),
        retrieved_at=decision_time - timedelta(seconds=1),
    )
    state = build_btc_market_state(
        InformationView(decision_time, (funding, open_interest, treasury_yield), ())
    )

    assert state.funding.freshness == "unknown"
    assert state.funding.funding_rate is None
    assert state.open_interest.open_interest == Decimal("123.45")
    assert state.open_interest.evidence_observation_id == "oi-current"
    assert state.open_interest.freshness == "fresh"
    assert state.treasury_yield.yield_pct == Decimal("4.25")
    assert state.treasury_yield.evidence_observation_id == "treasury-dgs10"
    assert state.treasury_yield.freshness == "fresh"

    after_ingestion = build_btc_market_state(
        InformationView(decision_time + timedelta(seconds=2), (funding, open_interest), ())
    )
    assert after_ingestion.funding.funding_rate == Decimal("-0.0001")
    assert after_ingestion.funding.freshness == "stale"


def test_sqlite_replay_rebuilds_combined_btc_state_at_the_availability_cutoff(tmp_path):
    decision_time = BASE + timedelta(days=1)
    available_at = decision_time - timedelta(seconds=5)
    candle_time = decision_time - timedelta(minutes=2)
    candle_observation = Observation(
        observation_id="spot-available",
        source_id=BINANCE_SPOT_SOURCE.source_id,
        subject="BTCUSDT",
        metric="spot_ohlcv.1m",
        payload={
            "open": "100.00",
            "high": "100.00",
            "low": "100.00",
            "close": "100.00",
            "base_volume": "1.25",
            "quote_volume": "125.00",
            "trade_count": 7,
            "close_time": (
                candle_time + timedelta(minutes=1) - timedelta(milliseconds=1)
            ).isoformat(),
        },
        event_time=candle_time,
        first_seen_time=available_at,
        retrieved_at=available_at,
    )
    funding_observation = Observation(
        observation_id="funding-available",
        source_id=BINANCE_USDM_FUNDING_SOURCE.source_id,
        subject="BTCUSDT",
        metric="derivatives.funding_rate.usdm",
        payload={"funding_rate": "0.0002"},
        event_time=decision_time - timedelta(hours=8),
        first_seen_time=available_at,
        retrieved_at=available_at,
    )
    oi_observation = Observation(
        observation_id="oi-available",
        source_id=BINANCE_USDM_OPEN_INTEREST_SOURCE.source_id,
        subject="BTCUSDT",
        metric="derivatives.open_interest.usdm",
        payload={"open_interest": "123.45"},
        event_time=available_at,
        first_seen_time=available_at,
        retrieved_at=available_at,
    )
    scheduled_event = ScheduledMacroEvent(
        event_id="bls:cpi:2027-01",
        title="Consumer Price Index release",
        event_type="cpi_release",
        scheduled_at=decision_time + timedelta(days=10),
        source=BLS_RELEASE_CALENDAR_SOURCE,
        raw_reference="https://www.bls.gov/schedule/news_release/cpi.htm",
    ).to_observation(retrieved_at=available_at)
    store = SQLiteInformationStore(tmp_path / "combined.sqlite3")
    store.append(
        MarketDataBatch(
            (candle_observation, funding_observation, oi_observation, scheduled_event),
            (),
            available_at,
        )
    )

    reopened = SQLiteInformationStore(tmp_path / "combined.sqlite3")
    before = build_btc_market_state(reopened.view_at(available_at - timedelta(microseconds=1)))
    after = build_btc_market_state(reopened.view_at(decision_time))

    assert before.spot.candle_count == 0
    assert before.funding.freshness == "unknown"
    assert before.open_interest.freshness == "unknown"
    assert before.upcoming_macro_events == ()
    assert after == build_btc_market_state(reopened.view_at(decision_time))
    assert after.spot.latest_close == Decimal("100.00")
    assert after.funding.funding_rate == Decimal("0.0002")
    assert after.open_interest.open_interest == Decimal("123.45")
    assert after.upcoming_macro_events == (scheduled_event,)
