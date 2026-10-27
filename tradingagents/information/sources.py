"""Provider-neutral metadata for sources feeding the information layer.

This registry is separate from TradingAgents' vendor router: it describes
what a source can tell us and its timing/quality limitations, while the router
selects implementations for existing analyst tools.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class SourceStatus(StrEnum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Source:
    """A documented information source and its acquisition semantics."""

    source_id: str
    source_type: str
    provider: str
    endpoint: str
    collection_method: str
    version: str = "1"
    asset_scope: tuple[str, ...] = ()
    metric_scope: tuple[str, ...] = ()
    timezone: str = "UTC"
    historical_depth: str | None = None
    publication_semantics: str = "unknown"
    revision_behavior: str = "unknown"
    polling_frequency: str | None = None
    authentication_required: bool = False
    rate_limit: str | None = None
    reliability: str = "unknown"
    limitations: tuple[str, ...] = ()
    legal_constraints: tuple[str, ...] = ()
    fallback_source_id: str | None = None
    status: SourceStatus = SourceStatus.UNKNOWN
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in ("source_id", "version", "source_type", "provider", "endpoint", "collection_method"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if not isinstance(self.status, SourceStatus):
            object.__setattr__(self, "status", SourceStatus(self.status))


class SourceRegistry:
    """In-memory registry with unique, stable source identifiers."""

    def __init__(self, sources: tuple[Source, ...] = ()) -> None:
        self._sources: dict[str, Source] = {}
        for source in sources:
            self.register(source)

    def register(self, source: Source) -> None:
        """Register a source; duplicate IDs are rejected to prevent silent replacement."""
        if source.source_id in self._sources:
            raise ValueError(f"source_id already registered: {source.source_id}")
        self._sources[source.source_id] = source

    def get(self, source_id: str) -> Source:
        """Return a registered source or raise KeyError."""
        return self._sources[source_id]

    def all(self) -> tuple[Source, ...]:
        """Return sources in registration order."""
        return tuple(self._sources.values())

    def __contains__(self, source_id: object) -> bool:
        return source_id in self._sources

    def __len__(self) -> int:
        return len(self._sources)
