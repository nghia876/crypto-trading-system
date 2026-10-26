"""Deterministic BTC spot market state derived from a point-in-time view."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from itertools import pairwise

from tradingagents.information.binance_spot import BINANCE_SPOT_SOURCE
from tradingagents.information.observations import Observation
from tradingagents.information.scheduled_events import upcoming_macro_events
from tradingagents.information.store import InformationView

_BTC = "BTCUSDT"
_OHLCV_1M = "spot_ohlcv.1m"


@dataclass(frozen=True, slots=True)
class BTCSpotMarketState:
    """A reproducible spot snapshot with source evidence and freshness."""

    decision_time: datetime
    candle_count: int
    latest_event_time: datetime | None
    latest_available_at: datetime | None
    latest_open: Decimal | None
    latest_high: Decimal | None
    latest_low: Decimal | None
    latest_close: Decimal | None
    latest_base_volume: Decimal | None
    latest_quote_volume: Decimal | None
    latest_trade_count: int | None
    one_bar_return_pct: Decimal | None
    realized_volatility_pct: Decimal | None
    volatility_return_count: int
    latest_bar_age: timedelta | None
    freshness: str
    unresolved_gap_count: int
    evidence_observation_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BTCFundingState:
    funding_rate: Decimal | None
    event_time: datetime | None
    available_at: datetime | None
    age: timedelta | None
    freshness: str
    evidence_observation_id: str | None


@dataclass(frozen=True, slots=True)
class BTCOpenInterestState:
    open_interest: Decimal | None
    event_time: datetime | None
    available_at: datetime | None
    age: timedelta | None
    freshness: str
    evidence_observation_id: str | None


@dataclass(frozen=True, slots=True)
class BTCMarketState:
    """Initial combined BTC state; each layer retains independent evidence."""

    decision_time: datetime
    spot: BTCSpotMarketState
    funding: BTCFundingState
    open_interest: BTCOpenInterestState
    treasury_yield: TreasuryYieldState
    upcoming_macro_events: tuple[Observation, ...]


def _decimal_close(observation_id: str, value: object) -> Decimal:
    try:
        close = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"observation {observation_id} has an invalid close") from exc
    if not close.is_finite() or close <= 0:
        raise ValueError(f"observation {observation_id} close must be finite and positive")
    return close


def _decimal_value(observation_id: str, value: object, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"observation {observation_id} has an invalid {field}") from exc
    if not result.is_finite():
        raise ValueError(f"observation {observation_id} {field} must be finite")
    return result


def _nonnegative_decimal(observation_id: str, value: object, field: str) -> Decimal:
    result = _decimal_value(observation_id, value, field)
    if result < 0:
        raise ValueError(f"observation {observation_id} {field} must be non-negative")
    return result


def _nonnegative_int(observation_id: str, value: object, field: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"observation {observation_id} has an invalid {field}") from exc
    if isinstance(value, bool) or str(result) != str(value) or result < 0:
        raise ValueError(f"observation {observation_id} {field} must be a non-negative integer")
    return result


def build_btc_spot_market_state(
    view: InformationView,
    *,
    stale_after: timedelta = timedelta(minutes=2),
    volatility_window: int = 20,
) -> BTCSpotMarketState:
    """Build a BTC spot snapshot using only closed, eligible Binance candles.

    ``view`` should come from ``SQLiteInformationStore.view_at(T)``. Eligibility
    is checked again here, while candle ``close_time`` prevents an incomplete
    interval from contributing to state. Event time never substitutes for
    recorded observation availability.
    """
    if view.decision_time.tzinfo is None or view.decision_time.utcoffset() is None:
        raise ValueError("decision_time must be timezone-aware")
    if stale_after < timedelta(0):
        raise ValueError("stale_after must be non-negative")
    if volatility_window < 1:
        raise ValueError("volatility_window must be positive")

    eligible = []
    for observation in view.observations:
        if (
            observation.source_id != BINANCE_SPOT_SOURCE.source_id
            or observation.subject != _BTC
            or observation.metric != _OHLCV_1M
            or not observation.is_available_at(view.decision_time)
            or observation.event_time > view.decision_time
        ):
            continue
        close_time_value = observation.payload.get("close_time")
        if not isinstance(close_time_value, str):
            raise ValueError(f"observation {observation.observation_id} is missing close_time")
        try:
            close_time = datetime.fromisoformat(close_time_value)
        except ValueError as exc:
            raise ValueError(
                f"observation {observation.observation_id} has invalid close_time"
            ) from exc
        if close_time.tzinfo is None or close_time.utcoffset() is None:
            raise ValueError(
                f"observation {observation.observation_id} close_time must be timezone-aware"
            )
        if close_time <= view.decision_time:
            observation_id = observation.observation_id
            prices = {
                name: _decimal_close(observation_id, observation.payload.get(name))
                for name in ("open", "high", "low", "close")
            }
            if prices["high"] < max(prices["open"], prices["close"], prices["low"]):
                raise ValueError(
                    f"observation {observation_id} high is inconsistent with OHLC values"
                )
            if prices["low"] > min(prices["open"], prices["close"], prices["high"]):
                raise ValueError(
                    f"observation {observation_id} low is inconsistent with OHLC values"
                )
            eligible.append(
                (
                    observation,
                    {
                        **prices,
                        "base_volume": _nonnegative_decimal(
                            observation_id, observation.payload.get("base_volume"), "base volume"
                        ),
                        "quote_volume": _nonnegative_decimal(
                            observation_id, observation.payload.get("quote_volume"), "quote volume"
                        ),
                        "trade_count": _nonnegative_int(
                            observation_id, observation.payload.get("trade_count"), "trade count"
                        ),
                    },
                )
            )

    eligible.sort(
        key=lambda item: (item[0].event_time, item[0].available_at, item[0].observation_id)
    )
    if not eligible:
        gap_count = sum(
            gap.subject == _BTC
            and gap.metric == _OHLCV_1M
            and gap.observed_at <= view.decision_time
            for gap in view.gaps
        )
        return BTCSpotMarketState(
            decision_time=view.decision_time,
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
            unresolved_gap_count=gap_count,
            evidence_observation_ids=(),
        )

    observations = [item[0] for item in eligible]
    measurements = [item[1] for item in eligible]
    returns = []
    latest_return = None
    contiguous_suffix = [eligible[-1]]
    for item in reversed(eligible[:-1]):
        if contiguous_suffix[0][0].event_time - item[0].event_time != timedelta(minutes=1):
            break
        contiguous_suffix.insert(0, item)
    for previous_item, current_item in pairwise(contiguous_suffix):
        previous_observation, previous_measurements = previous_item
        current_observation, current_measurements = current_item
        previous_close = previous_measurements["close"]
        current_close = current_measurements["close"]
        if current_observation.event_time - previous_observation.event_time != timedelta(minutes=1):
            continue
        with localcontext() as context:
            context.prec = 28
            value = (current_close - previous_close) * Decimal(100) / previous_close
            returns.append(value)
            if current_observation is eligible[-1][0]:
                latest_return = value
    window_returns = returns[-volatility_window:]

    realized_volatility = None
    if len(window_returns) >= 2:
        with localcontext() as context:
            context.prec = 28
            average = sum(window_returns, Decimal(0)) / Decimal(len(window_returns))
            variance = sum(
                ((value - average) ** 2 for value in window_returns), Decimal(0)
            ) / Decimal(len(window_returns))
            realized_volatility = variance.sqrt()

    latest = observations[-1]
    latest_close_time = datetime.fromisoformat(str(latest.payload["close_time"]))
    age = view.decision_time - latest_close_time
    freshness = "fresh" if age <= stale_after else "stale"
    gap_count = sum(
        gap.subject == _BTC and gap.metric == _OHLCV_1M and gap.observed_at <= view.decision_time
        for gap in view.gaps
    )
    return BTCSpotMarketState(
        decision_time=view.decision_time,
        candle_count=len(observations),
        latest_event_time=latest.event_time,
        latest_available_at=latest.available_at,
        latest_open=measurements[-1]["open"],
        latest_high=measurements[-1]["high"],
        latest_low=measurements[-1]["low"],
        latest_close=measurements[-1]["close"],
        latest_base_volume=measurements[-1]["base_volume"],
        latest_quote_volume=measurements[-1]["quote_volume"],
        latest_trade_count=measurements[-1]["trade_count"],
        one_bar_return_pct=latest_return,
        realized_volatility_pct=realized_volatility,
        volatility_return_count=len(window_returns),
        latest_bar_age=age,
        freshness=freshness,
        unresolved_gap_count=gap_count,
        evidence_observation_ids=tuple(item.observation_id for item in observations),
    )


def build_btc_market_state(
    view: InformationView,
    *,
    spot_stale_after: timedelta = timedelta(minutes=2),
    funding_stale_after: timedelta = timedelta(hours=12),
    open_interest_stale_after: timedelta = timedelta(minutes=5),
    volatility_window: int = 20,
) -> BTCMarketState:
    """Build the current spot plus USDⓈ-M derivatives state from one PIT view."""
    if funding_stale_after < timedelta(0) or open_interest_stale_after < timedelta(0):
        raise ValueError("derivatives freshness thresholds must be non-negative")

    decision_time = view.decision_time
    spot = build_btc_spot_market_state(
        view,
        stale_after=spot_stale_after,
        volatility_window=volatility_window,
    )
    latest_by_metric = {}
    metric_sources = {
        "derivatives.funding_rate.usdm": "derivatives.binance.usdm.funding",
        "derivatives.open_interest.usdm": "derivatives.binance.usdm.open_interest",
    }
    for observation in view.observations:
        expected_source = metric_sources.get(observation.metric)
        if (
            expected_source is None
            or observation.source_id != expected_source
            or observation.subject != _BTC
            or not observation.is_available_at(decision_time)
            or observation.event_time > decision_time
        ):
            continue
        current = latest_by_metric.get(observation.metric)
        order_key = (observation.event_time, observation.available_at, observation.observation_id)
        if current is None or order_key > (
            current.event_time,
            current.available_at,
            current.observation_id,
        ):
            latest_by_metric[observation.metric] = observation

    funding_observation = latest_by_metric.get("derivatives.funding_rate.usdm")
    if funding_observation is None:
        funding = BTCFundingState(None, None, None, None, "unknown", None)
    else:
        rate = _decimal_value(
            funding_observation.observation_id,
            funding_observation.payload.get("funding_rate"),
            "funding rate",
        )
        age = decision_time - funding_observation.event_time
        funding = BTCFundingState(
            rate,
            funding_observation.event_time,
            funding_observation.available_at,
            age,
            "fresh" if age <= funding_stale_after else "stale",
            funding_observation.observation_id,
        )

    oi_observation = latest_by_metric.get("derivatives.open_interest.usdm")
    if oi_observation is None:
        open_interest = BTCOpenInterestState(None, None, None, None, "unknown", None)
    else:
        value = _nonnegative_decimal(
            oi_observation.observation_id,
            oi_observation.payload.get("open_interest"),
            "open interest",
        )
        age = decision_time - oi_observation.event_time
        open_interest = BTCOpenInterestState(
            value,
            oi_observation.event_time,
            oi_observation.available_at,
            age,
            "fresh" if age <= open_interest_stale_after else "stale",
            oi_observation.observation_id,
        )

    return BTCMarketState(
        decision_time,
        spot,
        funding,
        open_interest,
        build_treasury_yield_state(view),
        upcoming_macro_events(view),
    )


@dataclass(frozen=True, slots=True)
class TreasuryYieldState:
    """Latest available U.S. 10-year Treasury par yield and its freshness."""

    decision_time: datetime
    yield_pct: Decimal | None
    event_time: datetime | None
    available_at: datetime | None
    age: timedelta | None
    freshness: str
    evidence_observation_id: str | None


def build_treasury_yield_state(
    view: InformationView, *, stale_after: timedelta = timedelta(days=3)
) -> TreasuryYieldState:
    """Build a Treasury rate state from only observations in the supplied PIT view."""
    if view.decision_time.tzinfo is None or view.decision_time.utcoffset() is None:
        raise ValueError("decision_time must be timezone-aware")
    if stale_after < timedelta(0):
        raise ValueError("stale_after must be non-negative")
    eligible = [
        item
        for item in view.observations
        if item.source_id == "macro.us.treasury.daily_par_yield"
        and item.metric == "macro.treasury_10y_par_yield_pct"
        and item.subject == "US"
        and item.is_available_at(view.decision_time)
        and item.event_time <= view.decision_time
    ]
    latest_by_event: dict[datetime, Observation] = {}
    for item in eligible:
        prior = latest_by_event.get(item.event_time)
        if prior is None or (item.available_at, item.observation_id) > (
            prior.available_at,
            prior.observation_id,
        ):
            latest_by_event[item.event_time] = item
    latest = max(
        latest_by_event.values(),
        key=lambda item: (item.event_time, item.available_at),
        default=None,
    )
    if latest is None:
        return TreasuryYieldState(view.decision_time, None, None, None, None, "unknown", None)
    try:
        value = Decimal(str(latest.payload["yield_pct"]))
    except (KeyError, InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"observation {latest.observation_id} has an invalid Treasury yield"
        ) from exc
    if not value.is_finite() or value < 0:
        raise ValueError(f"observation {latest.observation_id} has an invalid Treasury yield")
    age = view.decision_time - latest.event_time
    return TreasuryYieldState(
        view.decision_time,
        value,
        latest.event_time,
        latest.available_at,
        age,
        "stale" if age > stale_after else "fresh",
        latest.observation_id,
    )
