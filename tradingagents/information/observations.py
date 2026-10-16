"""Canonical observation envelope with conservative point-in-time availability.

All timestamps are timezone-aware datetimes. A naive timestamp is rejected
rather than silently interpreted in the host's local timezone. Historical
backfills must record when this system first saw and retrieved the data; an
event timestamp alone never proves historical availability.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Mapping


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


@dataclass(frozen=True, slots=True)
class Transformation:
    """A reproducible transformation applied to an observation payload."""

    name: str
    version: str
    parameters: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class Observation:
    """Small stable envelope; domain-specific values live in the payload."""

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

    def __post_init__(self) -> None:
        for name in ("observation_id", "source_id", "subject", "metric"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if not self.payload:
            raise ValueError("payload must contain at least one domain value")
        for name in ("event_time", "first_seen_time", "retrieved_at", "publication_time", "effective_time"):
            _require_aware(name, getattr(self, name))
        if not isinstance(self.quality, ObservationQuality):
            object.__setattr__(self, "quality", ObservationQuality(self.quality))
        if not isinstance(self.availability, ObservationAvailability):
            object.__setattr__(self, "availability", ObservationAvailability(self.availability))

    @property
    def available_at(self) -> datetime:
        """Earliest defensible time this system could use the observation.

        Retrieval and first-seen timestamps bound availability from below.
        A known publication timestamp can move the bound later, never earlier.
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
