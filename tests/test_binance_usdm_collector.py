"""Public USDⓈ-M funding and open-interest collector tests."""

from datetime import UTC, datetime, timedelta

import pytest

from tradingagents.information import BinanceUsdmDerivativesCollector
from tradingagents.information.binance_spot import MarketDataCollectionError


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, *, params, timeout):
        self.calls.append((url, params, timeout))
        return FakeResponse(self.payload)


def test_funding_backfill_keeps_settlement_time_separate_from_availability():
    retrieved_at = datetime(2026, 1, 2, tzinfo=UTC)
    funding_time = datetime(2026, 1, 1, tzinfo=UTC)
    session = FakeSession(
        [
            {
                "symbol": "BTCUSDT",
                "fundingTime": int(funding_time.timestamp() * 1000),
                "fundingRate": "-0.00012500",
                "markPrice": "90000.00",
                "rateType": "Regular",
            }
        ]
    )
    collector = BinanceUsdmDerivativesCollector(session=session, clock=lambda: retrieved_at)

    batch = collector.collect_funding(funding_time, funding_time)

    assert len(batch.observations) == 1
    observation = batch.observations[0]
    assert observation.event_time == funding_time
    assert observation.available_at == retrieved_at
    assert observation.payload["funding_rate"] == "-0.00012500"
    assert session.calls[0][1]["symbol"] == "BTCUSDT"
    assert session.calls[0][1]["limit"] == 1000


def test_current_open_interest_is_stamped_with_local_availability():
    retrieved_at = datetime(2026, 1, 2, tzinfo=UTC)
    exchange_time = retrieved_at - timedelta(milliseconds=400)
    session = FakeSession(
        {
            "symbol": "BTCUSDT",
            "time": int(exchange_time.timestamp() * 1000),
            "openInterest": "12345.67890000",
        }
    )
    collector = BinanceUsdmDerivativesCollector(session=session, clock=lambda: retrieved_at)

    batch = collector.collect_open_interest()

    observation = batch.observations[0]
    assert observation.event_time == exchange_time
    assert observation.available_at == retrieved_at
    assert observation.payload["open_interest"] == "12345.67890000"


def test_funding_response_outside_requested_bounds_is_rejected():
    start = datetime(2026, 1, 1, tzinfo=UTC)
    outside = start + timedelta(minutes=1)
    session = FakeSession(
        [{"symbol": "BTCUSDT", "fundingTime": int(outside.timestamp() * 1000), "fundingRate": "0"}]
    )
    collector = BinanceUsdmDerivativesCollector(session=session)

    with pytest.raises(MarketDataCollectionError, match="outside requested time bounds"):
        collector.collect_funding(start, start)


def test_mark_price_and_index_are_recorded_as_one_point_in_time_snapshot():
    retrieved_at = datetime(2026, 1, 2, tzinfo=UTC)
    market_time = retrieved_at - timedelta(milliseconds=250)
    session = FakeSession(
        {
            "symbol": "BTCUSDT",
            "time": int(market_time.timestamp() * 1000),
            "markPrice": "90100.00",
            "indexPrice": "90000.00",
            "lastFundingRate": "0.00010000",
            "nextFundingTime": int((retrieved_at + timedelta(hours=8)).timestamp() * 1000),
        }
    )
    collector = BinanceUsdmDerivativesCollector(session=session, clock=lambda: retrieved_at)

    observation = collector.collect_mark_price().observations[0]

    assert observation.metric == "derivatives.mark_price.usdm"
    assert observation.event_time == market_time
    assert observation.available_at == retrieved_at
    assert observation.payload["mark_price"] == "90100.00"
    assert observation.payload["index_price"] == "90000.00"
    assert session.calls[0][0].endswith("/fapi/v1/premiumIndex")


def test_contract_status_records_btc_perpetual_only():
    retrieved_at = datetime(2026, 1, 2, tzinfo=UTC)
    session = FakeSession(
        {
            "serverTime": int(retrieved_at.timestamp() * 1000),
            "symbols": [
                {"symbol": "BTCUSDT", "contractType": "PERPETUAL", "status": "TRADING"},
                {
                    "symbol": "BTCUSDT_260327",
                    "contractType": "CURRENT_QUARTER",
                    "status": "TRADING",
                },
            ],
        }
    )
    collector = BinanceUsdmDerivativesCollector(session=session, clock=lambda: retrieved_at)

    observation = collector.collect_contract_status().observations[0]

    assert observation.metric == "derivatives.contract_status.usdm"
    assert observation.payload["contract_status"] == "TRADING"
    assert observation.payload["contract_type"] == "PERPETUAL"
