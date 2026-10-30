# Specialist WORLD discovery slice - 2026-10-30

Status: VERIFIED bounded implementation and sampled live acquisition. Phase 3
remains IN_PROGRESS. This is not complete world recall, continuous operation,
independent confirmation, quantitative hazard coverage or trading validation.

## Verified baseline and interruption audit

Work continues in `phase-3-event-narrative-slice`, starting at
`a253e754924b2d311efda9c21f33271fb8c6a4d9` in the existing repository. The prior
usage-limit rejection did not execute its blocked command. Saved source edits
were intact; the already-running full regression completed with one failing
combined-graph test and 1,507 passing tests. The failure exposed narrative crowding,
not a corrupted checkout. Resumption fixed that failure and a specialist rendering
edge case (claim-lifecycle annotations required a retained event identity).

No main branch exists in this local checkout; no branch other than the current
feature branch was changed. Canonical `sources/` and the pre-existing untracked
`.phase12-tools/` remain unmodified. No history rewrite, push, paid source, secret,
new database, new mandatory dependency, live LLM or trading operation.

## Inputs, output and dependencies

`SPECIALIST_WORLD_CONFIG` extends the existing Source definitions and versioned
news registry. `WORLD_NEWS_CONFIG` combines four existing BBC/GDELT configurations
with four specialist requests. Existing `poll_once` and recurring `coordinate`
now default to that combined configuration. The same Observation/MarketDataBatch,
SQLiteInformationStore, view_at, narrative selection and real Market Analyst graph
are used. No BTC keyword, price movement or anomaly trigger is required.

| Source ID / official endpoint | Scope | Live sample |
|---|---|---|
| news.usgs.drought / https://water.usgs.gov/alerts/rss/Drought.xml | USGS drought/water emergency reports; predominantly US, not worldwide water measurements | 8 rows |
| news.usgs.river_flood / https://water.usgs.gov/alerts/rss/River_Flooding.xml | USGS river-flood emergency reports; not all disasters | 370 rows |
| news.eia.today / https://www.eia.gov/rss/todayinenergy.xml | EIA energy analysis headlines; not a grid outage/incident stream | 21 rows in sampled snapshot; 22 current stored versions across live checks |
| news.nass.news / https://www.nass.usda.gov/rss/news.xml | NASS news/release headlines; not numerical crop conditions or food-security surveillance | 313 entries; 24 outside NASS host scope excluded; 288 unique retained articles (one duplicate collapses) |

Article host scope is `usgs.gov`, `eia.gov`, or `nass.usda.gov` and their subdomains.
An external link is excluded rather than treated as eligible agency material;
lookalike suffixes do not match. Excluded and total snapshot-entry counts accompany
retained rows, and poll coverage reports exclusions. If no eligible row remains,
coverage is UNKNOWN; exclusion counts are unknown in that empty-batch case.
Invalid schema/URLs, bounds, encoding or transport still reject the whole eligible
snapshot atomically. Exclusion is disclosed scope selection, not silent truncation.

## Eligibility and provenance

Reviewed 2026-10-30; bounded engineering eligibility, not blanket legal clearance.
Only agency-produced headline/link/date metadata is stored and used for local
inference. No article bodies, logos, photographs, protected graphics or linked
third-party content are collected. Attribution, date when supplied and original
link accompany evidence. Official source identity does not establish factual truth.

- [USGS reuse FAQ](https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted)
  permits agency-authored/produced data and information with acknowledgment, while
  excluding third-party protected material. Official feed directory:
  https://water.usgs.gov/alerts/index.html . FAQ search verification succeeded in
  the first work session; direct re-open timed out on resumption, not a policy reversal.
- [EIA reuse policy](https://www.eia.gov/about/copyrights_reuse.php) permits its
  information products and asks for acknowledgment including publication date;
  licensed material and marks have separate restrictions. Official RSS directory:
  https://www.eia.gov/tools/rssfeeds/ . Both inspected; no blanket clearance of
  linked publishers or model training is claimed.
- [NASS citation policy](https://data.nass.usda.gov/Data_and_Statistics/Citation_Request/index.php)
  permits downloading/reproducing public-domain information with acknowledgment.
  [Official syndication page](https://data.nass.usda.gov/Newsroom/Syndication/News/index.php)
  describes free feeds. Other USDA/agcensus host links in this feed are excluded
  from this slice's narrower review; that does not assert they are prohibited.

Rights references, review date, publisher group, attribution, source type,
configuration fingerprint, snapshot/content/version hashes and raw URL are retained.
Two USGS channels share one publisher group; channels and repeated polls never add
independent votes. Origin/syndication and independent confirmation remain UNKNOWN;
accuracy is unmeasured, verified facts empty, contradiction search not performed.
Existing claim relationships/credibility guards remain in the canonical pipeline;
source reporting does not automatically confirm a claim or resolve a contradiction.

## Time, revisions, bounds and context

Occurrence date remains UNKNOWN (`event_occurrence_time=null`); event_time is the
explicitly labeled publication/retrieval proxy. Supplied publication and update,
local first-known and each retrieval remain separate. Retrieval is response
completion. Unknown/naive dates are not guessed; future publication/update evidence
is hidden until eligible. Immutable corrections and first-known semantics use
existing store revision logic. Historical headlines fetched now do not become
pre-acquisition knowledge. No historical vintage archive is claimed.

All feeds retain the 2 MB response cap. Drought/EIA allow 100 entries; river-flood
and NASS explicitly allow 500 after live samples exceeded the previous 250 ceiling.
Excess entries fail instead of silently selecting a prefix. Declared UTF-8,
ISO-8859-1 and Windows-1252 are decoded strictly; unsupported encodings fail.
Existing timeouts, elapsed streaming checks, no redirects/retry, durable poll IDs,
backoff/Retry-After, store lock and host cooldown remain. Caller-coordinated recurring
jobs prioritize oldest-due domains, preventing alphabetical domain starvation.
No unattended scheduler was installed or operational service-level claim made.

Narrative reservation is now 6,000 characters, independently of BLS/H.4.1/RRP;
whole evidence records and IDs remain intact, with omissions explicit. Total
information context stays 28,000 characters. The extra 2,000 comes from scheduled
calendar detail (2,500 -> 2,000), coverage detail (2,000 -> 1,500) and source-definition
detail (2,000 -> 1,000). BTC and numerical macro reservations are unchanged. Full
lineage stays stored. This is a character limit, not tokens or entire conversation.
Specialist records use concise rendering while retaining times, identity, agency
attribution, link and uncertainty. Domain rotation mitigates concentration but
cannot guarantee every domain/headline fits; oversized whole rows can be omitted.

`source_gap_report(view)` powers both CLI health and poll-once output, with all ten
targeted configured/missing domains, specialist gaps, last attempt/status, eligible
row count, unknown publication counts and stale content/collection. Content uses
a one-day heuristic; collection uses 30 minutes, not source release calendars.
Reports use only the supplied point-in-time view and current configuration; this
is not a historical registry-version reconstruction or event-absence assertion.

## Verification

- Final full offline suite: **1,510 passed + 99 subtests**, four skipped, one
  integration test deselected, 20 existing model-name warnings, **50.95 seconds**.
  Skips: three Windows/POSIX-mode checks and optional langchain_aws not installed.
- Focused specialist/news/polling/narrative/actual-graph suite: **97 passed** before
  final full-suite verification. New fixtures cover revisions/reopen, duplicates,
  provenance, source-group nonconfirmation, missing/stale/future evidence, atomic
  malformed/network/interrupted/encoding failures, external-host exclusion,
  oldest-due fairness and specialist lifecycle rendering.
- Actual TradingAgentsGraph simultaneously retains broad war/technology/cyber
  fixture evidence, four specialist domains, BTC funding, BLS values/calendar,
  H.4.1 and RRP, excluding later macro/liquidity corrections, under 28k characters.
- Project Ruff (`tradingagents tests cli main.py`), changed-file syntax parsing
  and `git diff --check` passed. A recursive root lint also scanned the excluded
  untracked dependency bundle and reported third-party issues; no bundle files
  were changed. Project-owned paths are the relevant passing lint scope.
- Bounded live acquisition persisted into the SAME configured
  `local-runtime/information.sqlite3`; integrity_check=ok after reopen. All **129
  BLS rows preserved**. Combined stored renderer **15,703 characters**. Newly
  acquired rows absent before acquisition. Final NASS acquisition completed at
  **2026-10-30T09:56:16.343015Z** (16:56:16 Asia/Saigon).
- Earlier live diagnostic failures (encoding, item cap, then host-scope mismatch)
  remain append-only unavailable coverage; later success does not erase them.
  Reports: local-runtime/world-specialist-live-report.json,
  world-specialist-resumed-report.json, world-specialist-final-report.json and
  world-regression-final.txt, outside Git. No continuous completeness/freshness,
  measured recall, latency performance or predictive efficacy claim.

## Remaining work and synchronization

Specialist wildfire/storm/global-disaster, public-health, cyber, trade/sanctions,
regional/language and original technology/chips sources remain missing/unvalidated.
Existing broad BBC/GDELT war and technology discovery remains enabled, including
cyber/AI/chips terms, but does not prove the missing domains. EIA news is not a
live grid incident feed; NASS news is not quantitative agriculture/food surveillance.
Drought/flood coverage is geographically limited; measurement and regional recall
remain open. Regulation/crypto breadth also remains a separate existing Phase 3 gap.

OPEN macro gates preserved: daily Treasury TGA gated; Treasury 2y/10y XML parsing
exists but collection/analyst use rights-gated; BEA GDP/PCE/core PCE numerical
integration incomplete; BLS live release calendar unavailable; FRED disabled.

Next: review a free original wildfire/health/cyber source subset and grid-operator
incident notices, then validate cadence/recall and prospective correction/incident
semantics through this same pipeline. Do not substitute macro work for world radar.

This slice and M2A.2 remain LOCAL ONLY. Remote last reported at `82c6ba6`; no fresh
remote verification or push was attempted in this session. Previously authorized
push scope remains ONLY M2A.1 `72a7273`. The inspected workspace Push-M2A1.ps1 pins
that full SHA, checks parent/branch/remote/clean tracked files and verifies the
result; it cannot push HEAD/M2A.2/this slice. Do not retry the failing MSYS credential
helper. GitHub synchronization is independent and requires new authorization for
newer commits.
