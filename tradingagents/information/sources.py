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


WORLD_DISCOVERY_DOMAINS = (
    "WAR_GEOPOLITICS",
    "TRADE",
    "DROUGHT_WATER",
    "FLOOD_DISASTER",
    "WILDFIRE",
    "AGRICULTURE_FOOD",
    "ENERGY_GRID",
    "PUBLIC_HEALTH",
    "TECHNOLOGY",
    "CYBERSECURITY",
)


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

        if self.domain not in WORLD_DISCOVERY_DOMAINS:
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
            or not 1 <= self.max_items <= 500
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
        legal_constraints=("Public feed/API only; no article body crawling or access bypass",),
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


def _specialist_source(source_id, provider, endpoint, rights_url):
    from dataclasses import replace

    return replace(
        _news_source(source_id, provider, endpoint),
        source_type="original_specialist_news",
        legal_constraints=(
            "Agency-produced headline/link/date fields only; no bodies, images or logos",
            "Attribute agency, publication date when supplied, and original link; no endorsement",
            "Third-party protected content excluded; eligibility is bounded, not blanket clearance",
        ),
        metadata=(
            ("rights_review_date", "2026-10-30"),
            ("rights_reference", rights_url),
            (
                "article_host_suffix",
                {
                    "U.S. Geological Survey": "usgs.gov",
                    "U.S. Energy Information Administration": "eia.gov",
                    "USDA-NASS": "nass.usda.gov",
                    "NASA": "nasa.gov",
                    "CDC": "cdc.gov",
                    "UK Government": "www.gov.uk",
                }[provider],
            ),
            ("publisher_group", provider),
            ("credibility_basis", "original agency reporting; accuracy unmeasured"),
        ),
    )


SPECIALIST_WORLD_CONFIG = (
    NewsDiscoveryConfig(
        _specialist_source(
            "news.usgs.drought",
            "U.S. Geological Survey",
            "https://water.usgs.gov/alerts/rss/Drought.xml",
            "https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted",
        ),
        "DROUGHT_WATER",
    ),
    NewsDiscoveryConfig(
        _specialist_source(
            "news.usgs.river_flood",
            "U.S. Geological Survey",
            "https://water.usgs.gov/alerts/rss/River_Flooding.xml",
            "https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted",
        ),
        "FLOOD_DISASTER",
        max_items=500,
    ),
    NewsDiscoveryConfig(
        _specialist_source(
            "news.eia.today",
            "U.S. Energy Information Administration",
            "https://www.eia.gov/rss/todayinenergy.xml",
            "https://www.eia.gov/about/copyrights_reuse.php",
        ),
        "ENERGY_GRID",
    ),
    NewsDiscoveryConfig(
        _specialist_source(
            "news.nass.news",
            "USDA-NASS",
            "https://www.nass.usda.gov/rss/news.xml",
            "https://data.nass.usda.gov/Data_and_Statistics/Citation_Request/index.php",
        ),
        "AGRICULTURE_FOOD",
        max_items=500,
    ),
)

# Existing broad discovery remains intact. All recurring jobs use this same registry/store.
OPERATIONAL_ADDITIONS = (
    NewsDiscoveryConfig(
        _specialist_source(
            "news.nasa.recent", "NASA", "https://www.nasa.gov/feed/",
            "https://www.nasa.gov/nasa-brand-center/images-and-media/",
        ), "TECHNOLOGY",
    ),
    NewsDiscoveryConfig(
        _specialist_source(
            "news.nasa.technology", "NASA",
            "https://www.nasa.gov/technology/feed/",
            "https://www.nasa.gov/nasa-brand-center/images-and-media/",
        ), "TECHNOLOGY",
    ),
    NewsDiscoveryConfig(
        _specialist_source(
            "news.usgs.earthquakes", "U.S. Geological Survey",
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.atom",
            "https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits",
        ), "FLOOD_DISASTER", "atom",
    ),
)


def _uk_config(source_id, organisation, domain, reviewed_at="2026-11-01"):
    from dataclasses import replace

    source = _specialist_source(
        source_id, "UK Government",
        f"https://www.gov.uk/government/organisations/{organisation}.atom",
        "https://www.gov.uk/help/reuse-govuk-content",
    )
    return NewsDiscoveryConfig(replace(source, metadata=source.metadata + (
        ("licence_attribution", "Contains public sector information licensed under the Open Government Licence v3.0."),
        ("licence_url", "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"),
        ("rights_review_date", reviewed_at),
    ), legal_constraints=(
        "Open Government Licence v3.0; attribution and original link required",
        "Headline/link/date only; no third-party content, personal data, logos or endorsement",
    )), domain, "atom")


UK_WORLD_CONFIG = (
    _uk_config("news.uk.fcdo", "foreign-commonwealth-development-office", "WAR_GEOPOLITICS"),
    _uk_config("news.uk.trade", "department-for-business-and-trade", "TRADE"),
    _uk_config("news.uk.health", "uk-health-security-agency", "PUBLIC_HEALTH"),
)
# Explicit operational subset; legacy broad configs remain unchanged for replay.
# Same OGL metadata scope; these are policy/agency streams, not outage telemetry.
OPERATIONAL_REPAIR_CONFIG = (
    _uk_config("news.uk.food", "department-for-environment-food-rural-affairs", "AGRICULTURE_FOOD", "2026-11-02"),
    _uk_config("news.uk.water", "environment-agency", "DROUGHT_WATER", "2026-11-02"),
    _uk_config("news.uk.energy", "department-for-energy-security-and-net-zero", "ENERGY_GRID", "2026-11-02"),
)
WORLD_NEWS_CONFIG = (BROAD_NEWS_CONFIG + SPECIALIST_WORLD_CONFIG
                     + OPERATIONAL_ADDITIONS + UK_WORLD_CONFIG)
