"""Public Binance Spot OHLCV collection with explicit point-in-time semantics."""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime

import requests

from tradingagents.information.observations import Observation, Transformation
from tradingagents.information.sources import Source, SourceRegistry

BINANCE_SPOT_SOURCE = Source(
    source_id="market.binance.spot",
    source_type="exchange_rest",
    provider="Binance Spot",
    endpoint="https://data-api.binance.vision/api/v3/klines",
    collection_method="Unauthenticated public REST polling",
    asset_scope=("BTCUSDT",),
    metric_scope=("spot_ohlcv",),
    timezone="UTC",
    historical_depth="Endpoint backfill; historical availability is the local ingestion time",
    publication_semantics="Kline open/close timestamps describe the measured interval, not publication time",
    revision_behavior="A changed candle is emitted as a new version superseding the prior observed version",
    polling_frequency="Caller controlled; 1m candles",
    authentication_required=False,
    rate_limit="Binance IP request weight; back off on HTTP 429/418 and honor Retry-After",
    reliability="UNKNOWN — not yet measured by this project",
    limitations=(
        "Exchange-local spot market only",
        "Historical REST rows do not establish historical system availability",
        "No durable storage or cross-process deduplication in this collector",
    ),
)

_INTERVAL = timedelta(minutes=1)
_INTERVAL_NAME = "1m"
_KLINE_URL = BINANCE_SPOT_SOURCE.endpoint
_MAX_LIMIT = 1000


class MarketDataCollectionError(RuntimeError):
    """A request failed or returned data that cannot safely enter the information layer."""


@dataclass(frozen=True, slots=True)
class MarketDataGap:
    """An expected candle open time absent from a successful source response."""

    subject: str
    metric: str
    event_time: datetime
    observed_at: datetime
    reason: str = "missing_from_source_response"
    freshness: str = "unknown"


@dataclass(frozen=True, slots=True)
class MarketDataBatch:
    observations: tuple[Observation, ...]
    gaps: tuple[MarketDataGap, ...]
    retrieved_at: datetime


def _decimal(value: object, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise MarketDataCollectionError(f"invalid {field} value: {value!r}") from exc
    if not number.is_finite():
        raise MarketDataCollectionError(f"non-finite {field} value")
    return number


def _utc_from_ms(value: object, field: str) -> datetime:
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
    except (TypeError, ValueError, OverflowError, OSError) as exc:
        raise MarketDataCollectionError(f"invalid {field} timestamp: {value!r}") from exc


def _retry_after(response: requests.Response) -> float | None:
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                date = date.replace(tzinfo=UTC)
            return max(0.0, (date - datetime.now(UTC)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


class BinanceSpotOHLCVCollector:
    """Collect closed BTC/USDT one-minute bars from Binance's public spot API.

    ``start`` is inclusive and ``end`` is exclusive by candle open time. All
    source timestamps and caller bounds must be timezone-aware. The collector
    records local retrieval time as the conservative PIT availability bound;
    it never backdates old REST candles to their event time.
    """

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        clock: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_retries: int = 3,
        backoff_seconds: float = 0.5,
        max_retry_after_seconds: float = 30.0,
        registry: SourceRegistry | None = None,
    ) -> None:
        if max_retries < 0 or backoff_seconds < 0 or max_retry_after_seconds < 0:
            raise ValueError("retry settings must be non-negative")
        self._session = session or requests.Session()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sleep = sleep
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._max_retry_after_seconds = max_retry_after_seconds
        self.registry = registry or SourceRegistry((BINANCE_SPOT_SOURCE,))
        if BINANCE_SPOT_SOURCE.source_id not in self.registry:
            self.registry.register(BINANCE_SPOT_SOURCE)
        elif self.registry.get(BINANCE_SPOT_SOURCE.source_id) != BINANCE_SPOT_SOURCE:
            raise ValueError("registry contains conflicting metadata for the Binance source ID")
        self._latest: dict[tuple[str, datetime], Observation] = {}

    def collect(
        self,
        start: datetime,
        end: datetime,
        *,
        symbol: str = "BTCUSDT",
    ) -> MarketDataBatch:
        """Fetch closed candles with open times in ``[start, end)``."""
        self._validate_bounds(start, end)
        start = start.astimezone(UTC)
        end = end.astimezone(UTC)
        if symbol != "BTCUSDT":
            raise ValueError("Phase 1.2 collector supports BTCUSDT only")
        first_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)
        if first_ms % 60_000 or end_ms % 60_000:
            raise ValueError("start and end must align to UTC minute boundaries")

        raw_rows: list[object] = []
        cursor_ms = first_ms
        while cursor_ms < end_ms:
            params = {
                "symbol": symbol,
                "interval": _INTERVAL_NAME,
                "startTime": cursor_ms,
                "endTime": end_ms - 1,
                "limit": min(_MAX_LIMIT, max(1, (end_ms - cursor_ms + 59_999) // 60_000)),
            }
            rows = self._get_klines(params)
            if not isinstance(rows, list):
                raise MarketDataCollectionError("Binance response must be a JSON list")
            if not rows:
                break
            parsed_opens = []
            for row in rows:
                if not isinstance(row, list) or len(row) < 11:
                    raise MarketDataCollectionError("Binance kline row must contain at least 11 fields")
                try:
                    parsed_opens.append(int(row[0]))
                except (TypeError, ValueError) as exc:
                    raise MarketDataCollectionError("Binance kline has an invalid open timestamp") from exc
            if parsed_opens != sorted(set(parsed_opens)):
                raise MarketDataCollectionError("Binance response contains duplicate or unordered candles")
            raw_rows.extend(rows)
            next_cursor = parsed_opens[-1] + 60_000
            if next_cursor <= cursor_ms:
                raise MarketDataCollectionError("Binance pagination did not advance")
            cursor_ms = next_cursor
            if len(rows) < params["limit"]:
                break

        retrieved_at = self._aware_utc(self._clock(), "clock")
        by_open: dict[datetime, Observation] = {}
        for row in raw_rows:
            observation = self._normalize_row(row, symbol, retrieved_at)
            opened = observation.event_time
            close_time = datetime.fromisoformat(str(observation.payload["close_time"]))
            if start <= opened < end and close_time < retrieved_at:
                by_open[opened] = self._version(observation)

        expected_count = int((end - start) / _INTERVAL)
        latest_closed_open = retrieved_at.replace(second=0, microsecond=0) - _INTERVAL
        expected = (start + index * _INTERVAL for index in range(expected_count))
        gaps = tuple(
            MarketDataGap(
                symbol,
                f"spot_ohlcv.{_INTERVAL_NAME}",
                opened,
                retrieved_at,
                freshness="stale" if opened == latest_closed_open else "unknown",
            )
            for opened in expected
            if opened not in by_open
        )
        observations = tuple(by_open[key] for key in sorted(by_open))
        return MarketDataBatch(observations, gaps, retrieved_at)

    @staticmethod
    def _validate_bounds(start: datetime, end: datetime) -> None:
        for name, value in (("start", start), ("end", end)):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if end <= start:
            raise ValueError("end must be after start")

    @staticmethod
    def _aware_utc(value: datetime, name: str) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise MarketDataCollectionError(f"{name} must return a timezone-aware datetime")
        return value.astimezone(UTC)

    def _get_klines(self, params: dict[str, object]) -> object:
        for attempt in range(self._max_retries + 1):
            try:
                response = self._session.get(_KLINE_URL, params=params, timeout=(3.05, 10.0))
            except requests.RequestException as exc:
                if attempt == self._max_retries:
                    raise MarketDataCollectionError(f"Binance request failed: {exc}") from exc
                self._sleep(self._backoff_seconds * (2**attempt))
                continue

            if response.status_code in (418, 429):
                delay = _retry_after(response)
                if delay is None:
                    delay = self._backoff_seconds * (2**attempt)
                if attempt == self._max_retries or delay > self._max_retry_after_seconds:
                    raise MarketDataCollectionError(
                        f"Binance rate limited the request (HTTP {response.status_code}); "
                        f"retry after {delay:g}s"
                    )
                self._sleep(delay)
                continue
            if response.status_code >= 500:
                if attempt == self._max_retries:
                    raise MarketDataCollectionError(f"Binance server error: HTTP {response.status_code}")
                self._sleep(self._backoff_seconds * (2**attempt))
                continue
            try:
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                raise MarketDataCollectionError(f"Binance returned an invalid response: {exc}") from exc
        raise MarketDataCollectionError("Binance request exhausted retries")

    def _normalize_row(self, row: list[object], symbol: str, retrieved_at: datetime) -> Observation:
        try:
            open_ms = int(row[0])
            trade_count = int(row[8])
        except (TypeError, ValueError) as exc:
            raise MarketDataCollectionError("Binance kline has an invalid integer field") from exc
        event_time = _utc_from_ms(open_ms, "open")
        close_time = _utc_from_ms(row[6], "close")
        if close_time < event_time or close_time >= event_time + _INTERVAL:
            raise MarketDataCollectionError("candle close timestamp is outside its one-minute interval")
        values = {
            "open": _decimal(row[1], "open"),
            "high": _decimal(row[2], "high"),
            "low": _decimal(row[3], "low"),
            "close": _decimal(row[4], "close"),
            "base_volume": _decimal(row[5], "base volume"),
            "quote_volume": _decimal(row[7], "quote volume"),
            "trade_count": trade_count,
            "taker_buy_base_volume": _decimal(row[9], "taker buy base volume"),
            "taker_buy_quote_volume": _decimal(row[10], "taker buy quote volume"),
        }
        if min(values[name] for name in ("open", "high", "low", "close")) <= 0:
            raise MarketDataCollectionError("OHLC prices must be positive")
        if values["high"] < max(values["open"], values["close"], values["low"]):
            raise MarketDataCollectionError("candle high is inconsistent with OHLC values")
        if values["low"] > min(values["open"], values["close"], values["high"]):
            raise MarketDataCollectionError("candle low is inconsistent with OHLC values")
        if any(values[name] < 0 for name in ("base_volume", "quote_volume", "taker_buy_base_volume", "taker_buy_quote_volume")):
            raise MarketDataCollectionError("volume fields must be non-negative")
        if values["trade_count"] < 0:
            raise MarketDataCollectionError("trade count must be non-negative")
        payload = {name: (int(value) if name == "trade_count" else str(value)) for name, value in values.items()}
        payload["close_time"] = close_time.isoformat()
        payload["interval"] = _INTERVAL_NAME
        content = json.dumps(payload, sort_keys=True).encode()
        fingerprint = hashlib.sha256(content).hexdigest()[:16]
        return Observation(
            observation_id=(
                f"binance:{symbol}:{_INTERVAL_NAME}:{open_ms}:{fingerprint}:"
                f"{retrieved_at.isoformat()}"
            ),
            source_id=BINANCE_SPOT_SOURCE.source_id,
            subject=symbol,
            metric=f"spot_ohlcv.{_INTERVAL_NAME}",
            payload=payload,
            event_time=event_time,
            effective_time=event_time,
            first_seen_time=retrieved_at,
            retrieved_at=retrieved_at,
            raw_reference=f"{_KLINE_URL}?symbol={symbol}&interval={_INTERVAL_NAME}&startTime={open_ms}",
            transformations=(Transformation("normalize_binance_spot_kline", "1"),),
            quality="unknown",
        )

    def _version(self, observation: Observation) -> Observation:
        key = (observation.subject, observation.event_time)
        prior = self._latest.get(key)
        if prior is not None:
            old_values = dict(prior.payload)
            if old_values == dict(observation.payload):
                return prior
            observation = Observation(
                observation_id=observation.observation_id,
                source_id=observation.source_id,
                subject=observation.subject,
                metric=observation.metric,
                payload=observation.payload,
                event_time=observation.event_time,
                first_seen_time=observation.first_seen_time,
                retrieved_at=observation.retrieved_at,
                effective_time=observation.effective_time,
                raw_reference=observation.raw_reference,
                transformations=observation.transformations,
                quality=observation.quality,
                supersedes_observation_id=prior.observation_id,
            )
        self._latest[key] = observation
        return observation
