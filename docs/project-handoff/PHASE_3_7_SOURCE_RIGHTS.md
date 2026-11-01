# Phase 3.7 bounded source eligibility — 2026-11-01

Agent policy review, not human incident adjudication or a legal opinion. Scope is
free, keyless publisher RSS/Atom headline, original link and supplied dates,
plus local acquisition/configuration/response-hash provenance. No bodies,
summaries, attachments, images, logos, third-party-host links or article crawling.
Public availability alone is not permission. Public-domain/OGL reuse is the
basis for local archival and factual AI inference; no AI-specific permission or
model-training permission was discovered or invented. No model training occurs.
US public-domain status does not settle rights in every foreign jurisdiction.

## Reviewed original publishers

| Exact configured access | Rights and storage/processing basis | Conditions and observed access |
|---|---|---|
| `water.usgs.gov/alerts/rss/Drought.xml`, `River_Flooding.xml`; `earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.atom` | [USGS copyrights/credits](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits): USGS-produced information is US public domain; protected third-party material is excepted. [Official Atom documentation](https://earthquake.usgs.gov/earthquakes/feed/v1.0/atom.php) advertises the earthquake feeds. | Attribute USGS and original link/date. Agency-host metadata only; not blanket clearance of linked works. Robots allowed the exact paths; requests succeeded. Water reports stale; earthquake update Oct 30. |
| `www.eia.gov/rss/todayinenergy.xml` | [EIA reuse](https://www.eia.gov/about/copyrights_reuse.php) permits use/distribution of its information products, with acknowledgement/date; third-party protected items excepted. [RSS directory](https://www.eia.gov/tools/rssfeeds/) advertises polling. | **Blocked operationally**: current robots explicitly disallows `/rss`. The radar refused the feed request despite the RSS directory invitation. No workaround, alternate identity or bypass. Clarification or another explicitly allowed official endpoint is needed. |
| `www.nass.usda.gov/rss/news.xml` | [NASS citation policy](https://data.nass.usda.gov/Data_and_Statistics/Citation_Request/index.php): public-domain NASS web information may be downloaded/reproduced, acknowledgement requested. | Retain USDA-NASS attribution, date and link; other-host links excluded (24 in parsed feed). Robots allowed. Latest supplied publication in entire eligible parsed snapshot Sep 24, 2025; stale, not food-disruption coverage. |
| `www.nasa.gov/technology/feed/`, `www.nasa.gov/feed/` | [NASA usage guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) permit factual informational use with acknowledgement and no endorsement; third-party protected media excepted. [Official RSS directory](https://www.nasa.gov/rss-feeds/) advertises news/recent/technology feeds. | Agency-authored headline/link/date metadata only. No protected image/media downloaded or reused. Robots allowed. Technology feed last publication Oct 22; main feed recent through Nov 1. Main feed includes photo notices and astronomy, not ten verified technology incidents. |
| `www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom`, `department-for-business-and-trade.atom`, `uk-health-security-agency.atom` | [GOV.UK reuse policy](https://www.gov.uk/help/reuse-govuk-content) applies [OGL v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). OGL permits copying, adaptation and commercial/noncommercial exploitation. This supports bounded metadata storage and factual processing; it is not a special AI grant. | Include source/link and “Contains public sector information licensed under the Open Government Licence v3.0.” Retained in payload and rendered analyst record. Excludes third-party rights, personal datasets, logos and endorsement. Robots allowed exact Atom paths. Only one GOV.UK feed per job/host cooldown. All three succeeded. Atom supplies **updated**, not publication/occurrence dates. All departments share conservative **UK Government** publisher group. |

OGL page failed with 403 in the web research surface, but a bounded direct official
policy request returned HTTP 200; its actual copying/adaptation/commercial-use,
attribution, exemptions and non-endorsement provisions were read. This is not a
claim that every policy page was available through every access surface.

## Investigated and withheld

- CDC [agency reuse](https://www.cdc.gov/other/agencymaterials.html) generally allows
  public-domain reuse, with contractor/third-party/international exceptions.
  However the [specific media-library syndication guidelines](https://tools.cdc.gov/medialibrary/index.html)
  prohibit redistribution and require unchanged wording, intact links/attribution,
  and separate logo permission. Their implications for durable transformed AI
  evidence/export remain unresolved. The initial bounded newsroom RSS check
  returned content that failed the RSS/Atom parser; no observation retained.
  CDC was removed from the operational configurations. Neither general government
  status nor the existence of RSS overrules the specific restrictions.
- CISA policy and advisories returned 403 through research; specialist cyber
  rights/access not cleared. No arbitrary alternative crawling.
- Current State RSS directory returned 403; archived 2021–2025 State rights/feed
  pages cannot establish current feed freshness or current-service eligibility.
- BBC/GDELT legacy configuration remains for compatibility/offline contracts.
  Neither BBC business/AI reuse nor publishers indexed by GDELT are newly cleared.
  The operational CLIs use the reviewed agency subset and **do not poll these**.
- Dedicated original AI/cyber, timely food/agriculture, drought, grid outages and
  global non-English/regional reporting remain gaps. NASA science and government
  statements do not establish general AI/cyber or independent conflict coverage.

## Access enforcement and provenance

`world_radar.PolicySession` checks exact reviewed configurations and exact feed
endpoints before access, requests robots once per host/job, fails closed on
unavailable/invalid/denied robots and redirects, and bounds bytes/time. HTTP 404/410
robots means no file, not a licence. Nonzero crawl delays defer acquisition;
there is no sleep/retry bypass. Normal coordinator enforces 30-second host cooldown,
one feed per host/job, 900-second intervals and exponential error/Retry-After
backoff. Default six feed requests/job, 12 retained records/feed; parser byte/item
limits still apply to entire responses. Robots checks add at most one request per
selected host. Jobs persist failures and health in the same canonical SQLite.

Live reports archive robots status, hashes, check times, config hashes, response
hashes, exclusions and retention omissions in
`tests/fixtures/phase37/operational_results.json`. A deliberate NASS-only check
after correcting hash-ordered retention also succeeded with robots hash
`cd9900dc2b2835f53e80842230316109ec0fa1071adcd5e2a63acd40d9568874`;
12 retained, 276 eligible omitted, 24 external links excluded. Its polling attempt
is durable in canonical SQLite. No complete response XML or article is archived.
New source registry helpers inherited the older specialist review-date metadata;
the actual expanded-scope policy review date is **Nov 1**, as recorded here and in
the operational rights scope. Historical source definitions are not rewritten.

Permission can change; source policies and robots need re-review before expanding
scope or public redistribution. Different hosts/departments are not independent
incident origins. Claims and suggested incident links remain unverified.
