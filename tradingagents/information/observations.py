"""Canonical observation envelope with conservative point-in-time availability.

All timestamps are timezone-aware datetimes. A naive timestamp is rejected
rather than silently interpreted in the host's local timezone. Historical
backfills must record when this system first saw and retrieved the data; an
event timestamp alone never proves historical availability.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType


class ObservationQuality(StrEnum):
    VERIFIED = "verified"
    ESTIMATED = "estimated"
    LOW = "low"
    UNKNOWN = "unknown"


class ObservationAvailability(StrEnum):
    AVAILABLE = "available"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


def _require_aware(name: str, value: datetime | None) -> None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError(f"{name} must be timezone-aware")


def _freeze(value: object) -> object:
    """Copy JSON-like payload containers into recursively immutable forms."""
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("payload mapping keys must be strings")
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    if value is None or isinstance(value, (str, int, float, bool, bytes, datetime)):
        return value
    raise TypeError(f"unsupported mutable or non-value payload type: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class Transformation:
    """A reproducible transformation applied to an observation payload."""

    name: str
    version: str
    parameters: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class Observation:
    """Immutable observation envelope with explicit temporal and revision semantics.

    ``event_time`` is when a reported event/measurement occurred. ``publication_time``
    is when its source published it; ``first_seen_time`` is when this system first
    observed it; and ``retrieved_at`` is when this copy was fetched. ``effective_time``
    marks when the value applies in the modeled world. PIT availability is based on
    publication and system-observed times, never event/effective time alone.

    A correction or restatement is a new observation that names the prior version in
    ``supersedes_observation_id``. It does not erase the earlier value from history.
    """

    observation_id: str
    source_id: str
    subject: str
    metric: str
    payload: Mapping[str, object]
    event_time: datetime
    first_seen_time: datetime
    retrieved_at: datetime
    publication_time: datetime | None = None
    effective_time: datetime | None = None
    raw_reference: str | None = None
    transformations: tuple[Transformation, ...] = ()
    quality: ObservationQuality = ObservationQuality.UNKNOWN
    availability: ObservationAvailability = ObservationAvailability.AVAILABLE
    quality_notes: tuple[str, ...] = ()
    supersedes_observation_id: str | None = None
    schema_version: str = "1"
    unit: str = "unknown"

    def __post_init__(self) -> None:
        for name in ("observation_id", "source_id", "subject", "metric"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if not self.schema_version.strip() or not self.unit.strip():
            raise ValueError("schema_version and unit must not be empty")
        if not isinstance(self.payload, Mapping):
            raise TypeError("payload must be a mapping")
        if not self.payload:
            raise ValueError("payload must contain at least one domain value")
        object.__setattr__(self, "payload", _freeze(self.payload))
        object.__setattr__(self, "transformations", tuple(self.transformations))
        object.__setattr__(self, "quality_notes", tuple(self.quality_notes))
        if self.supersedes_observation_id is not None:
            if not self.supersedes_observation_id.strip():
                raise ValueError("supersedes_observation_id must not be empty")
            if self.supersedes_observation_id == self.observation_id:
                raise ValueError("an observation cannot supersede itself")
        for name in ("event_time", "first_seen_time", "retrieved_at", "publication_time", "effective_time"):
            _require_aware(name, getattr(self, name))
        if not isinstance(self.quality, ObservationQuality):
            object.__setattr__(self, "quality", ObservationQuality(self.quality))
        if not isinstance(self.availability, ObservationAvailability):
            object.__setattr__(self, "availability", ObservationAvailability(self.availability))

    @property
    def available_at(self) -> datetime:
        """Latest known release/acquisition bound for point-in-time eligibility.

        This conservative bound is max(first_seen_time, retrieved_at,
        publication_time when known). Event and effective times describe the
        world and do not establish when this system knew the value.
        """
        candidates = [self.first_seen_time, self.retrieved_at]
        if self.publication_time is not None:
            candidates.append(self.publication_time)
        return max(candidates)

    def is_available_at(self, decision_time: datetime) -> bool:
        """Whether this observation is eligible at a decision cutoff.

        event_time is deliberately not used: scheduled future events can be
        known in advance. Callers must separately apply effective_time
        according to the metric's validity semantics.
        """
        _require_aware("decision_time", decision_time)
        if self.availability is not ObservationAvailability.AVAILABLE:
            return False
        return self.available_at <= decision_time

    def supersedes(self, prior: Observation) -> bool:
        """Whether this version explicitly replaces ``prior`` by ID."""
        return self.supersedes_observation_id == prior.observation_id
