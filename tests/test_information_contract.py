"""Unit tests for the source registry and canonical observation contract."""

from datetime import UTC, datetime, timedelta

import pytest

from tradingagents.information import (
    Observation,
    ObservationAvailability,
    Source,
    SourceRegistry,
    SourceStatus,
    Transformation,
)


@pytest.mark.unit
def test_source_registry_keeps_unique_ids_and_registration_order():
    first = Source("market.binance", "market", "Binance", "https://api.example.test", "REST",
                   asset_scope=("BTCUSDT",), metric_scope=("ohlcv",), status=SourceStatus.AVAILABLE)
    second = Source("macro.fred", "macro", "FRED", "https://api.example.test", "REST")
    registry = SourceRegistry((first, second))

    assert registry.get("market.binance") == first
    assert registry.all() == (first, second)
    assert "macro.fred" in registry
    assert len(registry) == 2
    with pytest.raises(ValueError, match="already registered"):
        registry.register(first)


@pytest.mark.unit
def test_source_registry_rejects_empty_identity_fields():
    with pytest.raises(ValueError, match="provider"):
        Source("x", "market", " ", "endpoint", "poll")


def make_observation(**overrides):
    base = {
        "observation_id": "obs-1",
        "source_id": "market.binance",
        "subject": "BTCUSDT",
        "metric": "ohlcv.1m",
        "payload": {"close": 65000.0},
        "event_time": datetime(2026, 1, 1, tzinfo=UTC),
        "first_seen_time": datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        "retrieved_at": datetime(2026, 1, 1, 0, 1, 1, tzinfo=UTC),
        "publication_time": datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        "effective_time": datetime(2026, 1, 1, tzinfo=UTC),
        "raw_reference": "archive://market.binance/obs-1",
        "transformations": (Transformation("normalize_ohlcv", "1"),),
    }
    return Observation(**(base | overrides))


@pytest.mark.unit
def test_observation_uses_latest_known_availability_timestamp():
    observation = make_observation()
    assert observation.available_at == datetime(2026, 1, 1, 0, 1, 1, tzinfo=UTC)
    assert observation.is_available_at(datetime(2026, 1, 1, 0, 1, 1, tzinfo=UTC))
    assert not observation.is_available_at(datetime(2026, 1, 1, 0, 1, tzinfo=UTC))


@pytest.mark.unit
def test_future_event_can_be_known_before_event_time():
    decision_time = datetime(2026, 1, 1, 0, 2, tzinfo=UTC)
    observation = make_observation(
        event_time=datetime(2026, 1, 2, tzinfo=UTC),
        publication_time=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        first_seen_time=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        retrieved_at=datetime(2026, 1, 1, 0, 1, 2, tzinfo=UTC),
    )
    assert observation.is_available_at(decision_time)


@pytest.mark.unit
def test_unavailable_observations_never_enter_pit_view():
    observation = make_observation(availability=ObservationAvailability.UNAVAILABLE)
    assert not observation.is_available_at(datetime(2026, 1, 1, 1, tzinfo=UTC))


@pytest.mark.unit
def test_naive_timestamps_are_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        make_observation(event_time=datetime(2026, 1, 1))


@pytest.mark.unit
def test_empty_payload_is_rejected():
    with pytest.raises(ValueError, match="payload"):
        make_observation(payload={})
