# M2A.2 bounded implementation — 2026-10-30

Status: VERIFIED BLS numeric subset; PARTIAL M2A.2. This is not whole-source,
continuous-operational, historical-vintage or Phase 3 completion.

## Verified state and changed components

Starting branch `phase-3-event-narrative-slice`, M2A.1 HEAD
`72a72730f9830f0b2ff6134e14be391332930ce5`; parent
`82c6ba6e4abc209dee605cda1b05ef74fc23dd2e`. Tracked files initially clean;
pre-existing untracked `.phase12-tools/` retained untouched. No changes to main,
synced sources or tools. M2A.2 is a local-only implementation commit.

`tradingagents/information/original_macro.py` uses the existing SourceRegistry,
Source, Observation, MarketDataBatch, CoverageRecord, SQLiteInformationStore and
view_at. It reuses the existing acquisition-time/coverage helpers from liquidity
and the existing BLS annual schedule parser and scheduled-event schema. No new
database, dependency, alternate app or financial-only graph. Consumer selection
and rendering use the same immutable view as BTC and world narrative evidence.

| Component / inputs | Output and implementation status | Limitations / acceptance evidence |
|---|---|---|
| BLS keyless v1 API, CUSR0000SA0 | VERIFIED CPI-U all items US city average SA level, index 1982–84=100, monthly | Not NSA headline year-over-year inflation; no growth arithmetic inferred |
| CUSR0000SA0L1E | VERIFIED CPI-U less food and energy US city average SA level, same base/frequency | Not spending or an inflation surprise |
| CES0000000001 | VERIFIED total nonfarm payroll employment SA level, thousand employees, monthly | Not monthly jobs change; retains preliminary/other footnotes |
| LNS14000000 | VERIFIED civilian unemployment rate age 16+, SA percent, monthly | Different survey/population from payroll employment |
| BLS annual schedule | Bounded collector reuses existing release-date/time and reschedule/cancellation contracts | Offline verified; live attempt returned unavailable; schedules are not actual publication or numeric vintage history |
| Treasury original par curve XML | Parser VERIFIED against deterministic Atom/OData fixtures for BC_2YEAR and BC_10YEAR, percent, business day | Collection AND analyst selection gated for unresolved source-specific service rights; no live XML parsing claim |
| BEA GDP, PCE/core PCE price indexes | Explicit gated source/metric coverage, no numerical parser or acquisition | Free registration, incorporated website policies, exact NIPA metadata/table/line/units and vintage mapping unvalidated; no invented GDP estimates |

FRED remains disabled by default. M2A.1 daily Treasury TGA remains gated. Existing
legacy Treasury 10-year CSV code is preserved for compatibility; its presence is
not new rights clearance or proof of expanded operational rates coverage. The
new par-curve metrics have distinct names and do not silently overwrite it.

## Source eligibility and official references

Reviewed 2026-10-30. These are bounded engineering eligibility assessments, not
blanket legal assurances for other material, model training, or future terms.

- [BLS v1 signatures](https://www.bls.gov/developers/api_signature.htm) document
  keyless multiple-series POST (up to 25 series, recent three-year snapshots).
  This collector requests only four pinned series, without a key or registration.
  [BLS copyright](https://www.bls.gov/bls/linksite.htm) places its publications in
  the public domain with photograph/illustration exceptions and asks for citation.
  [BLS API terms](https://www.bls.gov/developers/termsOfService.htm) describe
  secondary use without end-use controls, request-date citation, a required
  downstream-analysis disclaimer, no BLS logo, no false representation and service
  limits. No separate AI/storage ban was identified there. This supports numeric
  local storage and inference use for this subset; service quotas still apply.
  Attribution, acquisition date and the required disclaimer are rendered with
  selected evidence. No logo or endorsement used.
- [Official payroll description](https://www.bls.gov/opub/mlr/2023/article/job-openings-reach-record-highs-in-2022-as-the-labor-market-recovery-continues.htm)
  identifies CES0000000001 as total nonfarm SA employment in thousands (footnote 9).
  [CPS correction notice](https://www.bls.gov/bls/errata/cps-seasonally-adjusted-labor-force-and-unemployment-data-corrected-on-january-10-2024.htm)
  identifies LNS14000000 and illustrates why corrections must be retained.
  Series are pinned explicitly; API values alone do not carry all unit metadata.
- [Treasury structured-feed documentation](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed)
  confirms keyless GET, nominal par-curve dataset and date/month parameters.
  [Daily rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve)
  distinguish par yields from bill discount rates and real yields. The parser
  requires Atom/OData namespaces, dates, both exact tenor fields and numeric types;
  explicit null is missing. [Site policies](https://home.treasury.gov/subfooter/site-policies-and-notices)
  were inspected, but detailed automation/storage/AI service-use permission remains
  unresolved. This is a source-specific legal eligibility gap, not a demonstrated
  technical inability to obtain public XML, and not the Fiscal Data/TGA review.
  No expanded source request is made; direct parser rows remain analyst-excluded.
- [BEA copyright FAQ](https://www.bea.gov/help/faq/147) generally permits reuse of
  BEA material unless otherwise marked. [API signup](https://apps.bea.gov/API/signup/)
  requires free registration and agreement; no signup/key acquisition was done.
  [API terms](https://apps.bea.gov/API/_pdf/bea_api_tos.pdf) permit retrieving and
  analyzing data, require a specific attribution/no-endorsement notice and forbid
  false representation while incorporating website/privacy policies. This review
  does NOT establish an AI prohibition. Complete incorporated-policy review and
  actual free API/CSV metadata validation remain open. No BEA series is enabled;
  registration/access and mapping gaps are separate from remaining terms review.

## Time, revisions, failures and replay

BLS observation period is YYYY-MM, with explicit period end and SA flag. Event
time is the first-day New York date marker (DST-aware); not an instantaneous
measurement or publication timestamp. Annual M13 averages are skipped. Numbers
are finite nonnegative levels, preserved as decimal text with exact units.
Missing cells/series produce UNKNOWN metric coverage, not zeros. Unexpected
series, duplicate periods, label mismatch, malformed footnotes, invalid numbers,
future references, unexpected envelope or excessive rows fail the snapshot.

publication_time remains unknown for API values. first_seen_time and retrieved_at
are local acquisition time after reading the response; view_at excludes newly
fetched history before that time. Changed values/footnotes append corrections in
the existing store; unchanged snapshots retain earliest knowledge. Repeated
batches and corrections are idempotent; reopen and before/after cutoffs are tested.
No pre-collection vintage history, actual release verification, advance/second/
third GDP estimates or complete historical release-to-value linkage is claimed.
Existing scheduled events can be known before their scheduled time and retain
their own acquisition/reschedule history; never copied into numeric publication.

Requests have connect/read timeouts 3.05/15 seconds, a streamed 2 MB cap and no
redirects or automatic retry. Parser bounds also cap series/period counts. Each
instance imposes at least an hour between requests per API/calendar channel,
extended by numeric or HTTP-date Retry-After. Failures return unavailable batches
for persistence. There is no sleep/retry loop or log of remote response bodies or
credentials. This is bounded network work, not a strict total-wall-clock deadline:
read timeout bounds inactivity; response byte cap bounds accepted content.

Cross-instance/cross-process quota coordination and durable cooldown across
restarts are NOT implemented for these adapters. Callers must coordinate before
unattended use and honor current BLS quotas; no scheduler installed. Snapshot
PRESENT means usable rows, never certified complete intervening periods. Freshness
thresholds (75 calendar days monthly; four for yields) are heuristics, not official
release/holiday calendars.

## Analyst selection, tests and live evidence

The consumer selects one latest reference per eligible metric from the same
view_at and prioritizes its IDs/sources for lineage. Treasury parser rows cannot
bypass the pending gate. Dedicated inflation/labor/rates reservation is 3,500
characters. Narrative retains 4,000, BTC signals 6,000; total stays 28,000.
Other sections were rebalanced. Whole rows and evidence IDs are preserved or
explicitly omitted; complete history stays in SQLite. This is a character budget,
not a model token or entire-conversation limit. Older detail can be omitted.

- Focused new macro + actual graph suite: **68 passed**. Earlier combined focused
  macro/liquidity/calendars/graph run before the calendar additions: **100 passed**.
- Full offline regression: **1,486 passed + 99 subtests**, four skipped, one
  integration test deselected, 39.21 seconds. Skips: three POSIX file-mode tests on
  Windows and optional langchain_aws not installed. Existing model-name warnings.
- Ruff project checks, changed-file syntax compilation and git diff checks passed.
  No new mandatory package. Shared fixtures prohibit network; LLMs/vendors scripted.
- Deterministic tests cover schema/units/SA, month-end and DST, missing/annual
  values, invalid/nonfinite/duplicate/future rows, request timeout/redirect/oversize,
  429 and Retry-After numeric/date, cooldown, source gates, prospective revisions,
  repeated append/reopen, stale selection and bounded context.
- Actual TradingAgentsGraph test combines BLS, release schedules, H.4.1, RRP,
  BTC funding and war/drought/agriculture/energy/grid/technology/cyber narratives;
  later BLS and liquidity corrections are absent from captured model prompts.
  This verifies integration and preserves independent discovery semantics; these
  fixture headlines do not prove new specialized world-event collectors.
- Limited live BLS POST: **129 observations**, acquired
  `2026-10-30T04:34:52.042689Z` (11:34:52 Asia/Saigon). Latest returned period
  September 2026: CPI SA **336.298**, core CPI SA **338.896** index points;
  payroll SA **159044 thousand employees**; unemployment SA **4.2 percent**.
  These are sampled publisher values, not a verified claim about broader economic
  conditions or release completeness.
- Persisted into the SAME configured local-runtime canonical SQLite file; reopened
  view contains 281 total observations. Pre-acquisition view contains zero BLS
  observations. Combined BTC/macro/liquidity/world-store renderer: **14,507 chars**,
  BLS visible, within 28k. BLS calendar live attempt: zero usable entries and
  unavailable coverage persisted; no success or cause more specific than request/
  schema failure is claimed. No retry, live LLM, trading or predictive evaluation.
  Local-runtime/m2a2-live-report.json holds the measurements outside Git.

## Authorized M2A.1 push and remaining work

Verified actual branch, full SHA/parent, exact HTTPS origin, clean tracked starting
state, allowed 14-file committed diff and whitespace before a normal exact-SHA
feature-branch push. Network initially DNS-restricted; after turn network grant,
fresh ls-remote returned `82c6ba6e4abc209dee605cda1b05ef74fc23dd2e`.
One push attempt failed in the credential-manager MSYS shell with
BaseNamedObjects 0xC0000022. No repeated helper attempts, forced update, security
change, token extraction or history rewrite. Final fresh remote check still
returned the same parent SHA. M2A.1 is NOT reported pushed.

Workspace-root `Push-M2A1.ps1` is prepared for ordinary independent non-elevated
HOST Windows PowerShell, not this blocked execution environment. It verifies the
branch, M2A.1 ancestry/parent, tracked status and exact remote, then pushes ONLY
`72a72730f9830f0b2ff6134e14be391332930ce5` and freshly verifies remote equality.
Even if local HEAD contains M2A.2, the script cannot push M2A.2. It stops if the
remote differs from the expected parent/target. No execution-policy bypass needed.
New M2A.2 commits require separate push authorization.

Next concrete actions:

1. Run the prepared host script to synchronize authorized M2A.1 independently.
2. Diagnose BLS annual schedule access/schema and establish actual dated-release
   evidence linkage without inventing historical numeric vintages; coordinate
   durable source quotas before unattended collection.
3. Complete home.treasury.gov source-specific service-use review and limited live
   XML schema check before changing the par-curve eligibility definition. Resolve
   daily TGA separately; it remains gated.
4. Validate BEA free-access metadata and incorporated terms, then pin PCE price
   indexes vs spending and nominal/real GDP vs annualized growth. Save future
   estimate/revision arrivals prospectively; do not fabricate backfilled vintages.
5. Independent active Phase 3 world radar: review free original meteorological/
   drought/water, disaster/fire/flood, agriculture/food and energy/grid feeds,
   followed by health/science/cyber/regional sources. Extend the current two-domain
   discovery registry deliberately, with source-specific rights, bounded requests,
   explicit missingness, update/correction replay and domain examples requiring
   neither BTC keywords nor market movement. No source candidates are implicitly
   cleared or operational. Keep all evidence in this same store/graph.


## Quality recheck after reported network interruption — 2026-10-30

Rechecked committed baseline `2f6db789c5d6515640a9f35bfd1205a71b175006`.
The complete baseline offline suite independently passed again: 1,486 tests,
99 subtests, four skips, one deselected, 42.19 seconds. Ruff, compilation and
committed-diff checks passed. The code commit and local live report were present;
network interruption did not leave an incomplete tracked checkout.

Read-only SQLite audit: integrity_check=ok, 281 stored observations including
all 129 BLS rows. Every BLS row has finite numeric text, matching units, reference
time no later than retrieval, equal local first-seen/retrieval times, and unknown
publication. This confirms stored evidence integrity, not continuous live access
or independent revalidation of publisher values. No live data was refetched or
changed during this recheck. The earlier calendar failure's precise cause cannot
be reconstructed from the old generic diagnostic; it remains unavailable.

Adversarial parser checks reproduced two real gaps and fixed them: a fractional
JSON year was silently truncated by int(), and exponent text could expand into
an arbitrarily large formatted number despite the response byte cap. BLS years
now require four-digit publisher text. Numeric levels require bounded plain
decimal publisher text before Decimal conversion/formatting. Both numeric
parsers use this check. Normal published values and units are unchanged.

Request failures now distinguish network timeouts, connection failures, HTTP
status and schema/encoding errors without logging remote bodies, URLs or secrets.
Added regression cases for a connection lost AFTER the first streamed chunk;
both API/calendar adapters return only unavailable coverage and no partial
observations, with persistence/reopen verified. Tests also reject fractional
years, numeric type drift, exponent expansion and oversized numeric text.

GitHub read-only verification initially hit restricted-environment DNS failure;
the approved outside-environment read succeeded and confirmed remote feature SHA
`82c6ba6e4abc209dee605cda1b05ef74fc23dd2e`. No push or credential-helper retry.
Treasury/BEA/daily-TGA gates, default FRED disablement and independent world-radar
scope are preserved. This quality recheck does not complete the documented
calendar, rights, BEA, scheduler or specialized world-source gaps.

Final recheck after fixes: **1,497 passed + 99 subtests**, four skipped, one integration test deselected, 55.99 seconds. Project Ruff, syntax compilation and whitespace checks passed. Fixes are a new local-only commit; no history rewrite or push.
