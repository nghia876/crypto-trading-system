"""Public Binance USDⓈ-M funding and open-interest observations."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import requests

from tradingagents.information.binance_spot import MarketDataBatch, MarketDataCollectionError
from tradingagents.information.observations import Observation, Transformation
from tradingagents.information.sources import Source, SourceRegistry

BINANCE_USDM_FUNDING_SOURCE = Source(
    source_id="derivatives.binance.usdm.funding",
    source_type="exchange_rest",
    provider="Binance USDⓈ-M Futures",
    endpoint="https://fapi.binance.com/fapi/v1/fundingRate",
    collection_method="Unauthenticated public REST polling",
    asset_scope=("BTCUSDT",),
    metric_scope=("funding_rate",),
    timezone="UTC",
    historical_depth=(
        "Funding rows can be queried by time bounds; official documentation does not state archive depth"
    ),
    publication_semantics=(
        "fundingTime is the settlement event time; the historical endpoint does not establish when this "
        "system first knew the rate"
    ),
    revision_behavior="A changed same-time row is stored as a later observation revision",
    authentication_required=False,
    rate_limit="IP-based; shares 500 requests per 5 minutes with /fapi/v1/fundingInfo",
    reliability="UNKNOWN — not yet measured by this project",
    limitations=(
        "USDⓈ-M venue only",
        "Historical backfills are available to replay only from local ingestion time",
        "No automated scheduler or cross-exchange aggregation",
    ),
)

BINANCE_USDM_OPEN_INTEREST_SOURCE = Source(
    source_id="derivatives.binance.usdm.open_interest",
    source_type="exchange_rest",
    provider="Binance USDⓈ-M Futures",
    endpoint="https://fapi.binance.com/fapi/v1/openInterest",
    collection_method="Unauthenticated public REST polling",
    asset_scope=("BTCUSDT",),
    metric_scope=("open_interest",),
    timezone="UTC",
    historical_depth="Current snapshot only; prospective history requires caller-driven collection",
    publication_semantics=(
        "Response time is exchange transaction time; local first-seen and retrieval times define "
        "conservative replay availability"
    ),
    revision_behavior="A changed same-time snapshot is stored as a later observation revision",
    authentication_required=False,
    rate_limit="IP request weight 1 per request",
    reliability="UNKNOWN — not yet measured by this project",
    limitations=(
        "USDⓈ-M venue only",
        "This collector does not call the separate one-month sampled history endpoint",
        "No automated scheduler or cross-exchange aggregation",
    ),
)

_SYMBOL = "BTCUSDT"
_FUNDING_URL = BINANCE_USDM_FUNDING_SOURCE.endpoint
_OPEN_INTEREST_URL = BINANCE_USDM_OPEN_INTEREST_SOURCE.endpoint


def _aware_utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _from_ms(value: object, field: str) -> datetime:
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
    except (TypeError, ValueError, OverflowError, OSError) as exc:
        raise MarketDataCollectionError(f"invalid {field} timestamp: {value!r}") from exc


def _decimal_string(
    value: object,
    field: str,
    *,
    allow_zero: bool = True,
    allow_negative: bool = False,
) -> str:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise MarketDataCollectionError(f"invalid {field} value: {value!r}") from exc
    if (
        not number.is_finite()
        or (number < 0 and not allow_negative)
        or (number == 0 and not allow_zero)
    ):
        qualifier = (
            "negative, zero or positive" if allow_negative and allow_zero else "non-negative"
        )
        if not allow_zero:
            qualifier = "negative or positive" if allow_negative else "positive"
        raise MarketDataCollectionError(f"{field} must be finite and {qualifier}")
    return str(number)


class BinanceUsdmDerivativesCollector:
    """Caller-driven collector for BTCUSDT funding history and current OI."""

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        clock: Callable[[], datetime] | None = None,
        registry: SourceRegistry | None = None,
    ) -> None:
        self._session = session or requests.Session()
        self._clock = clock or (lambda: datetime.now(UTC))
        self.registry = registry or SourceRegistry(
            (BINANCE_USDM_FUNDING_SOURCE, BINANCE_USDM_OPEN_INTEREST_SOURCE)
        )
        for source in (BINANCE_USDM_FUNDING_SOURCE, BINANCE_USDM_OPEN_INTEREST_SOURCE):
            if source.source_id not in self.registry:
                self.registry.register(source)
            elif self.registry.get(source.source_id) != source:
                raise ValueError(f"registry contains conflicting metadata for {source.source_id}")

    def collect_funding(self, start: datetime, end: datetime) -> MarketDataBatch:
        """Fetch funding rows whose fundingTime is within inclusive UTC bounds."""
        start = _aware_utc(start, "start")
        end = _aware_utc(end, "end")
        if end < start:
            raise ValueError("end must be at or after start")
        rows = self._get(
            _FUNDING_URL,
            {
                "symbol": _SYMBOL,
                "startTime": int(start.timestamp() * 1000),
                "endTime": int(end.timestamp() * 1000),
                "limit": 1000,
            },
        )
        if not isinstance(rows, list):
            raise MarketDataCollectionError("Binance funding response must be a JSON list")
        retrieved_at = _aware_utc(self._clock(), "clock")
        observations = []
        last_time = None
        for row in rows:
            if not isinstance(row, dict) or row.get("symbol") != _SYMBOL:
                raise MarketDataCollectionError(
                    "Binance funding row has an unexpected symbol or shape"
                )
            event_time = _from_ms(row.get("fundingTime"), "funding")
            if not start <= event_time <= end:
                raise MarketDataCollectionError(
                    "Binance funding row is outside requested time bounds"
                )
            if last_time is not None and event_time <= last_time:
                raise MarketDataCollectionError("Binance funding rows are duplicate or unordered")
            last_time = event_time
            payload = {
                "funding_rate": _decimal_string(
                    row.get("fundingRate"), "funding rate", allow_negative=True
                ),
                "funding_time": event_time.isoformat(),
            }
            if row.get("markPrice") not in (None, ""):
                payload["mark_price"] = _decimal_string(
                    row["markPrice"], "mark price", allow_zero=False
                )
            if row.get("rateType") is not None:
                payload["rate_type"] = str(row["rateType"])
            observations.append(
                self._observation(
                    source=BINANCE_USDM_FUNDING_SOURCE,
                    metric="derivatives.funding_rate.usdm",
                    event_time=event_time,
                    retrieved_at=retrieved_at,
                    payload=payload,
                    raw_reference=f"{_FUNDING_URL}?symbol={_SYMBOL}&fundingTime={int(event_time.timestamp() * 1000)}",
                    transform="normalize_binance_usdm_funding",
                )
            )
        return MarketDataBatch(tuple(observations), (), retrieved_at)

    def collect_open_interest(self) -> MarketDataBatch:
        """Fetch the current open-interest snapshot for BTCUSDT."""
        row = self._get(_OPEN_INTEREST_URL, {"symbol": _SYMBOL})
        if not isinstance(row, dict) or row.get("symbol") != _SYMBOL:
            raise MarketDataCollectionError(
                "Binance open-interest response has an unexpected symbol or shape"
            )
        event_time = _from_ms(row.get("time"), "open-interest")
        retrieved_at = _aware_utc(self._clock(), "clock")
        payload = {"open_interest": _decimal_string(row.get("openInterest"), "open interest")}
        observation = self._observation(
            source=BINANCE_USDM_OPEN_INTEREST_SOURCE,
            metric="derivatives.open_interest.usdm",
            event_time=event_time,
            retrieved_at=retrieved_at,
            payload=payload,
            raw_reference=f"{_OPEN_INTEREST_URL}?symbol={_SYMBOL}",
            transform="normalize_binance_usdm_open_interest",
        )
        return MarketDataBatch((observation,), (), retrieved_at)

    def _get(self, url: str, params: dict[str, object]) -> object:
        try:
            response = self._session.get(url, params=params, timeout=(3.05, 10.0))
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            raise MarketDataCollectionError(f"Binance derivatives request failed: {exc}") from exc

    @staticmethod
    def _observation(
        *,
        source: Source,
        metric: str,
        event_time: datetime,
        retrieved_at: datetime,
        payload: dict[str, object],
        raw_reference: str,
        transform: str,
    ) -> Observation:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
        return Observation(
            observation_id=(
                f"binance:{_SYMBOL}:{metric}:{int(event_time.timestamp() * 1000)}:"
                f"{digest}:{retrieved_at.isoformat()}"
            ),
            source_id=source.source_id,
            subject=_SYMBOL,
            metric=metric,
            payload=payload,
            event_time=event_time,
            effective_time=event_time,
            first_seen_time=retrieved_at,
            retrieved_at=retrieved_at,
            raw_reference=raw_reference,
            transformations=(Transformation(transform, "1"),),
            quality="unknown",
        )
