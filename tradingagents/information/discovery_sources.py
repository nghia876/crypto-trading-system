"""Exact metadata-only non-government pilot scope, reviewed 2026-11-02.

Reuse basis is distinct from access: every live request still needs robots.
No summary grant: bylines, exceptions and snippet-specific terms remain gated.
"""

from tradingagents.information.sources import NewsDiscoveryConfig, Source


def _channel(key, publisher, endpoint, host, rights, licence):
    return NewsDiscoveryConfig(Source(
        source_id="news.discovery." + key, source_type="publisher_rss",
        provider=publisher, endpoint=endpoint, collection_method="Public RSS metadata only",
        metric_scope=("narrative.event",), polling_frequency="User invoked; >=1 hour",
        rate_limit="Publisher quota UNKNOWN; local <=2 feeds per host per run, >=1 hour per config; robots delay honored",
        limitations=("Rolling feed; omissions unknown", "Original reporting lineage unknown",
                     "English feed is not global or multilingual completeness"),
        legal_constraints=("Robots preflight required; no redirects or article fetches",
                           "Headlines, links and supplied dates only; no bodies/media",
                           "Summary author/exception clearance pending"),
        metadata=(("article_host_suffix", host), ("publisher_group", publisher),
                  ("rights_reference", rights), ("rights_review_date", "2026-11-02"),
                  ("licence_attribution", licence + "; " + publisher + "; original URL retained"),
                  ("summary_access", "unknown"), ("summary_retention", "unknown"),
                  ("summary_inference", "unknown"), ("summary_redistribution", "unknown")),
    ), "WORLD", max_items=100)


SCIDEV_CANDIDATE = _channel(
    "scidev", "SciDev.Net", "https://www.scidev.net/global/feed/", "scidev.net",
    "https://www.scidev.net/content/media.html",
    "CC BY 2.0 https://creativecommons.org/licenses/by/2.0/")

# IPS RSS terms explicitly permit downloading/publishing attributed headlines.
# Full articles require agreement; no snippets, media, training or body grant.
DISCOVERY_CONFIGS = (
    _channel("globalvoices", "Global Voices", "https://globalvoices.org/feed/",
             "globalvoices.org", "https://globalvoices.org/about/global-voices-attribution-policy/",
             "CC BY 3.0 https://creativecommons.org/licenses/by/3.0/"),
    _channel("ips", "Inter Press Service", "https://www.ipsnews.net/feed/",
             "ipsnews.net", "https://www.ipsnews.net/rss-feeds/",
             "IPS RSS headline permission; full articles excluded; https://www.ipsnews.net/reprinting-articles/"),
)

# Directory https://globalvoices.org/feeds/ documents topic RSS subscriptions.
RELATED_CONFIGS = (
    _channel("globalvoices.environment", "Global Voices",
             "https://globalvoices.org/-/topics/environment/feed/", "globalvoices.org",
             "https://globalvoices.org/about/global-voices-attribution-policy/",
             "CC BY 3.0 https://creativecommons.org/licenses/by/3.0/"),
    _channel("globalvoices.technology", "Global Voices",
             "https://globalvoices.org/-/topics/technology/feed/", "globalvoices.org",
             "https://globalvoices.org/about/global-voices-attribution-policy/",
             "CC BY 3.0 https://creativecommons.org/licenses/by/3.0/"),
)
