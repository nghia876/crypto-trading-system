"""Public Binance USDⓈ-M funding and open-interest observations."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import requests

from tradingagents.information.binance_spot import MarketDataBatch, MarketDataCollectionError
from tradingagents.information.binance_usdm_streams import BINANCE_USDM_LIQUIDATION_STREAM_SOURCE
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

BINANCE_USDM_MARK_PRICE_SOURCE = Source(
    source_id="derivatives.binance.usdm.mark_price",
    source_type="exchange_rest",
    provider="Binance USDⓈ-M Futures",
    endpoint="https://fapi.binance.com/fapi/v1/premiumIndex",
    collection_method="Unauthenticated public REST polling",
    asset_scope=("BTCUSDT",),
    metric_scope=("mark_price", "index_price"),
    timezone="UTC",
    historical_depth="Current snapshot; prospective history requires caller-driven collection",
    publication_semantics="Exchange response time is event time; local retrieval bounds replay availability",
    revision_behavior="Repeated snapshots are append-only observations",
    authentication_required=False,
    rate_limit="IP-based request weight",
    reliability="UNKNOWN — not yet measured by this project",
    limitations=("USDⓈ-M venue only", "Mark-index basis is a current snapshot"),
)

BINANCE_USDM_CONTRACT_STATUS_SOURCE = Source(
    source_id="derivatives.binance.usdm.contract_status",
    source_type="exchange_rest",
    provider="Binance USDⓈ-M Futures",
    endpoint="https://fapi.binance.com/fapi/v1/exchangeInfo",
    collection_method="Unauthenticated public REST polling",
    asset_scope=("BTCUSDT",),
    metric_scope=("contract_status",),
    timezone="UTC",
    historical_depth="Current symbol metadata; prospective history requires caller-driven collection",
    publication_semantics="Server time is event time; local retrieval bounds replay availability",
    revision_behavior="Status changes are retained as later observations",
    authentication_required=False,
    rate_limit="IP request weight 1",
    reliability="UNKNOWN — not yet measured by this project",
    limitations=("Symbol trading status is not a complete exchange-wide health signal",),
)

_SYMBOL = "BTCUSDT"
_FUNDING_URL = BINANCE_USDM_FUNDING_SOURCE.endpoint
_OPEN_INTEREST_URL = BINANCE_USDM_OPEN_INTEREST_SOURCE.endpoint
_MARK_PRICE_URL = BINANCE_USDM_MARK_PRICE_SOURCE.endpoint
_EXCHANGE_INFO_URL = BINANCE_USDM_CONTRACT_STATUS_SOURCE.endpoint


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
            (
                BINANCE_USDM_FUNDING_SOURCE,
                BINANCE_USDM_OPEN_INTEREST_SOURCE,
                BINANCE_USDM_MARK_PRICE_SOURCE,
                BINANCE_USDM_CONTRACT_STATUS_SOURCE,
                BINANCE_USDM_LIQUIDATION_STREAM_SOURCE,
            )
        )
        for source in (
            BINANCE_USDM_FUNDING_SOURCE,
            BINANCE_USDM_OPEN_INTEREST_SOURCE,
            BINANCE_USDM_MARK_PRICE_SOURCE,
            BINANCE_USDM_CONTRACT_STATUS_SOURCE,
            BINANCE_USDM_LIQUIDATION_STREAM_SOURCE,
        ):
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

    def collect_mark_price(self) -> MarketDataBatch:
        """Fetch current mark/index prices used for futures basis state."""
        row = self._get(_MARK_PRICE_URL, {"symbol": _SYMBOL})
        if not isinstance(row, dict) or row.get("symbol") != _SYMBOL:
            raise MarketDataCollectionError("Binance mark-price response has an unexpected shape")
        event_time = _from_ms(row.get("time"), "mark-price")
        retrieved_at = _aware_utc(self._clock(), "clock")
        payload = {
            "mark_price": _decimal_string(row.get("markPrice"), "mark price", allow_zero=False),
            "index_price": _decimal_string(row.get("indexPrice"), "index price", allow_zero=False),
        }
        if row.get("lastFundingRate") not in (None, ""):
            payload["last_funding_rate"] = _decimal_string(
                row["lastFundingRate"], "last funding rate", allow_negative=True
            )
        if row.get("nextFundingTime") not in (None, ""):
            payload["next_funding_time"] = _from_ms(
                row["nextFundingTime"], "next funding"
            ).isoformat()
        observation = self._observation(
            source=BINANCE_USDM_MARK_PRICE_SOURCE,
            metric="derivatives.mark_price.usdm",
            event_time=event_time,
            retrieved_at=retrieved_at,
            payload=payload,
            raw_reference=f"{_MARK_PRICE_URL}?symbol={_SYMBOL}",
            transform="normalize_binance_usdm_mark_price",
        )
        return MarketDataBatch((observation,), (), retrieved_at)

    def collect_contract_status(self) -> MarketDataBatch:
        """Fetch the current BTCUSDT perpetual symbol status, not venue health."""
        response = self._get(_EXCHANGE_INFO_URL, {})
        if not isinstance(response, dict) or not isinstance(response.get("symbols"), list):
            raise MarketDataCollectionError(
                "Binance exchange-info response has an unexpected shape"
            )
        row = next(
            (
                item
                for item in response["symbols"]
                if isinstance(item, dict)
                and item.get("symbol") == _SYMBOL
                and item.get("contractType") == "PERPETUAL"
            ),
            None,
        )
        if row is None or not isinstance(row.get("status"), str) or not row["status"].strip():
            raise MarketDataCollectionError(
                "Binance exchange-info omitted BTCUSDT perpetual status"
            )
        event_time = _from_ms(response.get("serverTime"), "exchange-info")
        retrieved_at = _aware_utc(self._clock(), "clock")
        observation = self._observation(
            source=BINANCE_USDM_CONTRACT_STATUS_SOURCE,
            metric="derivatives.contract_status.usdm",
            event_time=event_time,
            retrieved_at=retrieved_at,
            payload={
                "contract_status": row["status"],
                "contract_type": row["contractType"],
                "quote_asset": row.get("quoteAsset", ""),
            },
            raw_reference=_EXCHANGE_INFO_URL,
            transform="normalize_binance_usdm_contract_status",
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
