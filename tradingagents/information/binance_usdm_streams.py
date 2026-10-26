"""Normalizers for public Binance USDⓈ-M market streams."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from tradingagents.information.binance_spot import MarketDataBatch, MarketDataCollectionError
from tradingagents.information.observations import Observation, Transformation
from tradingagents.information.sources import Source

BINANCE_USDM_LIQUIDATION_STREAM_SOURCE = Source(
    source_id="derivatives.binance.usdm.liquidation_stream",
    source_type="exchange_websocket",
    provider="Binance USDⓈ-M Futures",
    endpoint="wss://fstream.binance.com/ws/!forceOrder@arr",
    collection_method="Public all-market liquidation WebSocket stream; caller manages connection",
    asset_scope=("BTCUSDT",),
    metric_scope=("liquidation_snapshot",),
    timezone="UTC",
    historical_depth="Prospective stream only; no maintained public REST history",
    publication_semantics=(
        "Exchange transaction/event times describe the order; local first-seen and retrieval times bound replay availability"
    ),
    revision_behavior="Stream snapshots are append-only observations",
    authentication_required=False,
    reliability="UNKNOWN — stream connection continuity is not measured",
    limitations=(
        "Binance sends at most one largest liquidation order per symbol per second; snapshots are not a complete order tape",
        "This module normalizes messages but does not open, reconnect, or schedule a WebSocket connection",
    ),
)


def _timestamp_ms(value: object, field: str) -> datetime:
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
    except (TypeError, ValueError, OverflowError, OSError) as exc:
        raise MarketDataCollectionError(f"invalid liquidation {field} timestamp") from exc


def _decimal_text(value: object, field: str) -> str:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise MarketDataCollectionError(f"invalid liquidation {field}") from exc
    if not parsed.is_finite() or parsed < 0:
        raise MarketDataCollectionError(f"liquidation {field} must be finite and non-negative")
    return format(parsed, "f")


def parse_binance_usdm_liquidation_event(
    message: dict[str, Any], *, retrieved_at: datetime
) -> MarketDataBatch:
    """Normalize one public force-order stream snapshot without extrapolating totals."""
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")
    retrieved_at = retrieved_at.astimezone(UTC)
    if not isinstance(message, dict):
        raise MarketDataCollectionError("liquidation stream message must be a JSON object")
    data = message.get("data", message)
    if not isinstance(data, dict) or data.get("e") != "forceOrder":
        raise MarketDataCollectionError("message is not a Binance force-order event")
    order = data.get("o")
    if not isinstance(order, dict) or order.get("s") != "BTCUSDT":
        raise MarketDataCollectionError("force-order event is not for BTCUSDT")
    side = order.get("S")
    if side not in {"BUY", "SELL"}:
        raise MarketDataCollectionError("force-order event has an invalid side")
    event_time = _timestamp_ms(order.get("T", data.get("E")), "event")
    payload: dict[str, object] = {
        "order_id": str(order.get("i", "")),
        "side": side,
        "order_type": str(order.get("o", "")),
        "status": str(order.get("X", "")),
        "quantity": _decimal_text(order.get("q"), "quantity"),
        "price": _decimal_text(order.get("p"), "price"),
        "average_price": _decimal_text(order.get("ap"), "average price"),
        "last_filled_quantity": _decimal_text(order.get("l"), "last filled quantity"),
        "cumulative_filled_quantity": _decimal_text(order.get("z"), "cumulative filled quantity"),
        "snapshot_semantics": "largest liquidation order observed for symbol in the stream interval",
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    observation = Observation(
        observation_id=(
            f"binance:{order.get('i', 'unknown')}:liquidation:{int(event_time.timestamp() * 1000)}:"
            f"{digest}:{retrieved_at.isoformat()}"
        ),
        source_id=BINANCE_USDM_LIQUIDATION_STREAM_SOURCE.source_id,
        subject="BTCUSDT",
        metric="derivatives.liquidation_snapshot.usdm",
        payload=payload,
        event_time=event_time,
        effective_time=event_time,
        first_seen_time=retrieved_at,
        retrieved_at=retrieved_at,
        raw_reference=BINANCE_USDM_LIQUIDATION_STREAM_SOURCE.endpoint,
        transformations=(Transformation("normalize_binance_usdm_force_order", "1"),),
        quality="unknown",
        quality_notes=(
            "Public stream snapshots only the largest liquidation order per symbol per second; not a complete liquidation tape",
        ),
    )
    return MarketDataBatch((observation,), (), retrieved_at)
