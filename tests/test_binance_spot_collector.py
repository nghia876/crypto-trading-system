"""Isolated tests for the public Binance Spot OHLCV collector."""

from datetime import UTC, datetime

import pytest
import requests

from tradingagents.information import (
    BINANCE_SPOT_SOURCE,
    BinanceSpotOHLCVCollector,
    MarketDataCollectionError,
)


def kline(minute: int, close: str = "100.5"):
    opened = 1_767_225_600_000 + minute * 60_000  # 2026-01-01 00:00 UTC
    return [opened, "100", "101", "99", close, "2.5", opened + 59_999,
            "250.0", 10, "1.1", "110.0", "0"]


class Response:
    def __init__(self, rows=None, status=200, headers=None):
        self.rows = rows
        self.status_code = status
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self.rows


class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, *, params, timeout):
        self.calls.append((url, params, timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def collector(responses, *, now=datetime(2026, 1, 1, 0, 3, 30, tzinfo=UTC), sleeps=None):
    return BinanceSpotOHLCVCollector(
        session=Session(responses),
        clock=lambda: now,
        sleep=(sleeps.append if sleeps is not None else lambda _: None),
    )


def test_collect_normalizes_closed_bars_with_ingestion_time_availability():
    client = collector([Response([kline(0), kline(1), kline(2)])])
    batch = client.collect(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, 0, 3, tzinfo=UTC))

    assert BINANCE_SPOT_SOURCE.source_id == batch.observations[0].source_id
    assert [item.event_time.minute for item in batch.observations] == [0, 1, 2]
    assert batch.observations[0].available_at == batch.retrieved_at
    assert not batch.observations[0].is_available_at(datetime(2026, 1, 1, 0, 3, 29, tzinfo=UTC))
    assert batch.observations[0].is_available_at(batch.retrieved_at)
    assert batch.observations[0].payload["base_volume"] == "2.5"
    assert batch.gaps == ()


def test_missing_and_latest_stale_candles_are_explicit():
    batch = collector([Response([kline(0), kline(2)])]).collect(
        datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, 0, 3, tzinfo=UTC)
    )
    assert [(gap.event_time.minute, gap.freshness) for gap in batch.gaps] == [(1, "unknown")]

    stale = collector([Response([kline(0), kline(1)])]).collect(
        datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, 0, 3, tzinfo=UTC)
    )
    assert [(gap.event_time.minute, gap.freshness) for gap in stale.gaps] == [(2, "stale")]


def test_identical_duplicate_is_suppressed_and_changed_candle_supersedes_prior():
    client = collector([Response([kline(0)]), Response([kline(0)]), Response([kline(0, "100.6")])])
    start, end = datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, 0, 1, tzinfo=UTC)
    original = client.collect(start, end).observations[0]
    duplicate = client.collect(start, end).observations[0]
    revised = client.collect(start, end).observations[0]

    assert duplicate.observation_id == original.observation_id
    assert revised.observation_id != original.observation_id
    assert revised.supersedes_observation_id == original.observation_id


def test_rate_limit_retry_honors_retry_after():
    sleeps = []
    client = collector([Response(status=429, headers={"Retry-After": "2"}), Response([])], sleeps=sleeps)
    batch = client.collect(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, 0, 1, tzinfo=UTC))
    assert sleeps == [2.0]
    assert len(batch.observations) == 0
    assert len(batch.gaps) == 1


def test_rate_limit_with_long_retry_after_fails_without_retrying_early():
    client = collector([Response(status=418, headers={"Retry-After": "600"})])
    with pytest.raises(MarketDataCollectionError, match="retry after 600s"):
        client.collect(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, 0, 1, tzinfo=UTC))


@pytest.mark.parametrize("row", [[1, 2], kline(0, "NaN"), kline(0)])
def test_bad_or_out_of_range_kline_is_not_silently_accepted(row):
    if row == kline(0):
        row[2] = "99"  # high below open/close
    client = collector([Response([row])])
    with pytest.raises(MarketDataCollectionError):
        client.collect(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, 0, 1, tzinfo=UTC))


def test_rejects_naive_bounds_and_unsupported_symbol():
    client = collector([Response([])])
    with pytest.raises(ValueError, match="timezone-aware"):
        client.collect(datetime(2026, 1, 1), datetime(2026, 1, 1, 0, 1))
    with pytest.raises(ValueError, match="BTCUSDT only"):
        client.collect(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, 0, 1, tzinfo=UTC), symbol="ETHUSDT")
