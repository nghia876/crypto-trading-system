"""Unit tests for the source registry and canonical observation contract."""

from datetime import UTC, datetime
from types import MappingProxyType

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
def test_late_arriving_observation_is_not_available_at_event_time():
    observation = make_observation(
        event_time=datetime(2026, 1, 1, tzinfo=UTC),
        first_seen_time=datetime(2026, 1, 3, tzinfo=UTC),
        retrieved_at=datetime(2026, 1, 3, 0, 1, tzinfo=UTC),
    )
    assert not observation.is_available_at(datetime(2026, 1, 2, tzinfo=UTC))
    assert observation.is_available_at(datetime(2026, 1, 3, 0, 1, tzinfo=UTC))


@pytest.mark.unit
def test_revision_is_a_new_observation_and_only_available_after_its_cutoff():
    original = make_observation()
    revision = make_observation(
        observation_id="obs-2",
        payload={"close": 65001.0},
        supersedes_observation_id="obs-1",
        first_seen_time=datetime(2026, 1, 2, tzinfo=UTC),
        retrieved_at=datetime(2026, 1, 2, 0, 1, tzinfo=UTC),
        publication_time=datetime(2026, 1, 2, tzinfo=UTC),
    )
    before_revision = datetime(2026, 1, 2, 0, 1, tzinfo=UTC)
    assert original.is_available_at(before_revision)
    assert not revision.is_available_at(datetime(2026, 1, 2, tzinfo=UTC))
    assert revision.is_available_at(before_revision)
    assert revision.supersedes(original)
    assert original.payload["close"] == 65000.0


@pytest.mark.unit
def test_payload_is_recursively_immutable_and_detached_from_input():
    payload = {"nested": {"items": [1, 2]}}
    observation = make_observation(payload=payload)
    payload["nested"]["items"].append(3)
    assert observation.payload["nested"]["items"] == (1, 2)
    assert isinstance(observation.payload, MappingProxyType)
    with pytest.raises(TypeError):
        observation.payload["close"] = 1.0
    with pytest.raises(TypeError):
        observation.payload["nested"]["new"] = True


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
def test_naive_pit_cutoff_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        make_observation().is_available_at(datetime(2026, 1, 1, 1))


@pytest.mark.unit
def test_invalid_revision_identity_is_rejected():
    with pytest.raises(ValueError, match="cannot supersede itself"):
        make_observation(supersedes_observation_id="obs-1")


@pytest.mark.unit
def test_empty_payload_is_rejected():
    with pytest.raises(ValueError, match="payload"):
        make_observation(payload={})
