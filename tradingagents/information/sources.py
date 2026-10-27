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
        for name in (
            "source_id",
            "version",
            "source_type",
            "provider",
            "endpoint",
            "collection_method",
        ):
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


@dataclass(frozen=True, slots=True)
class NewsDiscoveryConfig:
    """Versioned public discovery request; domains never depend on market moves."""

    source: Source
    domain: str
    format: str = "rss"
    query: str = ""
    version: str = "1"
    max_items: int = 100
    max_bytes: int = 2_000_000

    def __post_init__(self):
        from urllib.parse import urlsplit

        if self.domain not in {"WAR_GEOPOLITICS", "TECHNOLOGY"}:
            raise ValueError("unsupported discovery domain")
        if self.format not in {"rss", "atom", "gdelt"}:
            raise ValueError("unsupported discovery format")
        url = urlsplit(self.source.endpoint)
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            raise ValueError("public HTTPS endpoint required")
        if self.source.authentication_required:
            raise ValueError("news discovery requires FREE public access")
        if (
            not self.version.strip()
            or not 1 <= self.max_items <= 250
            or not 1 <= self.max_bytes <= 2_000_000
        ):
            raise ValueError("invalid version or discovery bounds")
        if self.format == "gdelt" and (
            url.hostname != "api.gdeltproject.org" or not self.query.strip()
        ):
            raise ValueError("GDELT requires its public endpoint and an explicit query")

    @property
    def source_definition(self) -> Source:
        from dataclasses import replace

        return replace(
            self.source,
            version=f"{self.source.version}:news-{self.version}:{self.fingerprint[:16]}",
            metadata=self.source.metadata
            + (
                ("config_fingerprint", self.fingerprint),
                ("domain", self.domain),
                ("format", self.format),
                ("query", self.query),
                ("max_items", str(self.max_items)),
                ("max_bytes", str(self.max_bytes)),
            ),
        )

    @property
    def fingerprint(self) -> str:
        import hashlib
        import json
        from dataclasses import asdict

        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


def _news_source(source_id, provider, endpoint):
    return Source(
        source_id=source_id,
        source_type="public_news_discovery",
        provider=provider,
        endpoint=endpoint,
        collection_method="Bounded caller-independent public polling",
        metric_scope=("narrative.event",),
        publication_semantics="Source reported; may be unknown",
        revision_behavior="Immutable local article versions; never backdated",
        historical_depth="Rolling discovery, not historical vintages",
        polling_frequency="Caller controlled",
        rate_limit="One bounded request per poll; no automatic retry; honor provider access policy",
        limitations=(
            "Incomplete coverage",
            "Origin and syndication unverified",
            "No independent corroboration",
        ),
        legal_constraints=(
            "Public feed/API only; no article body crawling or access bypass",
        ),
    )


BROAD_NEWS_CONFIG = (
    NewsDiscoveryConfig(
        _news_source("news.bbc.world", "BBC", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        "WAR_GEOPOLITICS",
    ),
    NewsDiscoveryConfig(
        _news_source(
            "news.bbc.technology", "BBC", "https://feeds.bbci.co.uk/news/technology/rss.xml"
        ),
        "TECHNOLOGY",
    ),
    NewsDiscoveryConfig(
        _news_source(
            "news.gdelt.geopolitics",
            "GDELT discovery",
            "https://api.gdeltproject.org/api/v2/doc/doc",
        ),
        "WAR_GEOPOLITICS",
        "gdelt",
        "(war OR conflict OR diplomacy OR sanctions)",
    ),
    NewsDiscoveryConfig(
        _news_source(
            "news.gdelt.technology",
            "GDELT discovery",
            "https://api.gdeltproject.org/api/v2/doc/doc",
        ),
        "TECHNOLOGY",
        "gdelt",
        '(technology OR semiconductor OR "artificial intelligence" OR cybersecurity)',
    ),
)
