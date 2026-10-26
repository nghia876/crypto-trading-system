"""Public Binance force-order stream normalization tests."""

from datetime import UTC, datetime

import pytest

from tradingagents.information import (
    MarketDataCollectionError,
    parse_binance_usdm_liquidation_event,
)


def test_force_order_stream_snapshot_uses_exchange_event_and_local_availability():
    retrieved_at = datetime(2026, 10, 26, 12, tzinfo=UTC)
    message = {
        "e": "forceOrder",
        "E": 1793015999000,
        "o": {
            "s": "BTCUSDT",
            "S": "SELL",
            "o": "LIMIT",
            "q": "0.25",
            "p": "65000.00",
            "ap": "64950.00",
            "X": "FILLED",
            "l": "0.25",
            "z": "0.25",
            "T": 1793015998000,
            "i": 12345,
        },
    }

    observation = parse_binance_usdm_liquidation_event(
        {"stream": "!forceOrder@arr", "data": message},
        retrieved_at=retrieved_at,
    ).observations[0]

    assert observation.event_time == datetime.fromtimestamp(1793015998, UTC)
    assert observation.available_at == retrieved_at
    assert observation.metric == "derivatives.liquidation_snapshot.usdm"
    assert observation.payload["cumulative_filled_quantity"] == "0.25"
    assert "largest liquidation order" in observation.payload["snapshot_semantics"]


def test_force_order_parser_rejects_other_symbols_and_event_types():
    retrieved_at = datetime(2026, 10, 26, 12, tzinfo=UTC)
    base = {
        "e": "forceOrder",
        "E": 1793015999000,
        "o": {
            "s": "ETHUSDT",
            "S": "SELL",
            "o": "LIMIT",
            "q": "1",
            "p": "1",
            "ap": "1",
            "X": "FILLED",
            "l": "1",
            "z": "1",
            "T": 1793015998000,
            "i": 1,
        },
    }
    with pytest.raises(MarketDataCollectionError, match="not for BTCUSDT"):
        parse_binance_usdm_liquidation_event(base, retrieved_at=retrieved_at)

    with pytest.raises(MarketDataCollectionError, match="not a Binance force-order"):
        parse_binance_usdm_liquidation_event({"e": "aggTrade"}, retrieved_at=retrieved_at)
