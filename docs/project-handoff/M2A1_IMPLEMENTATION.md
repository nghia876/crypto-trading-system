# M2A.1 implementation — 2026-10-30

Branch: `phase-3-event-narrative-slice`, starting checkpoint `82c6ba6`.
User confirms that documentation checkpoint was pushed using ordinary host
PowerShell. Gate 1 is complete; no push was attempted or required here.
New implementation commits are LOCAL ONLY. Main, synced sources and
`.phase12-tools/` were not modified.

## Delivered and pending

`tradingagents/information/liquidity.py` adds original-publisher Sources,
Observation parsers and bounded caller-driven collection. It uses the existing
MarketDataBatch/CoverageRecord/SQLiteInformationStore/view_at contracts.
`consumer.py` renders the selected liquidity evidence in the actual Market
Analyst's existing analysis_information input. No additional database or graph.

| Metric | Implementation / availability |
|---|---|
| H.4.1 table 5 total assets | Wednesday level; million USD; eligible, parser and collector implemented |
| H.4.1 table 1 reserves | Weekly average and Wednesday level are separate metrics; million USD; eligible |
| H.4.1 table 1 TGA | Weekly average and Wednesday level are separate metrics; million USD; eligible |
| NY Fed ON RRP | Results only, Overnight, Treasury-only details, total accepted per operation; USD; eligible subject to NY Fed terms |
| Treasury daily TGA | Closing-label row in `open_today_bal`, million USD; parser implemented and sampled; collection AND analyst selection gated pending detailed rights review |

This is a verified eligible subset, not unconditional completion of every M2A.1
source. Daily Treasury TGA remains an explicit gap. Historical DTS schema before
2022-04-01 is rejected, not guessed. No historical schema equivalence is claimed.
FRED stays disabled by default. No net-liquidity arithmetic or causal BTC signal
is inferred from mixed daily and weekly measurements. ON RRP is per operation,
not an asserted aggregate of every same-day operation or H.4.1 reverse repos.

## Official endpoints and eligibility assessment

- Board: dated releases at `https://www.federalreserve.gov/releases/h41/YYYYMMDD/`.
  [Official H.4.1](https://www.federalreserve.gov/releases/h41/current/) identifies
  table definitions/units and the forthcoming DDP changes. HTML is used rather
  than building around a disappearing DDP export. The dated release and labeled
  cells must match; schema drift fails closed. Internal HTML table `t7` contains
  printed table 5; `t2` is printed table 1 continued. Assets use `t7r25c3`, not
  the consolidation/elimination column `c2`. Reserves use `t2r16c2/c5`; TGA uses
  `t2r8c2/c5`. Header dates and labels are validated before extraction.
  [Board policy](https://www.federalreserve.gov/disclaimer.htm) generally permits
  copying/distribution of Board information as public domain unless otherwise
  marked. Cite Board, preserve exceptions, do not use seals or imply endorsement.
  No H.4.1-specific AI/retention restriction was identified in the reviewed
  material; eligibility is an engineering assessment, not blanket legal certainty.
- NY Fed: `/api/rp/reverserepo/all/results/last/100.json` under
  `https://markets.newyorkfed.org`. [Markets API docs](https://markets.newyorkfed.org/static/docs/markets-api.html)
  load the official `markets-api.yml` schema. `repo.operations[].totalAmtAccepted`
  reconciles with Treasury `details[].amtAccepted`. The official reverse-repo
  page's JavaScript divides these amounts by 1e9 for its billion-dollar display,
  supporting retention of API values in USD without scaling. UI asset inspected:
  `/medialibrary/Interactives/markets-data/repo-and-reverse-repo/reverse-repo-pi-ui/browser/main.js`
  on `www.newyorkfed.org`; schema alone does not label the units.
  [NY Fed terms](https://www.newyorkfed.org/privacy/termsofuse) permit automated
  access, storage and derivative works subject to conditions. Attribution, terms
  URL and transformation/no-endorsement notices are retained in payload and
  rendered context. Content-specific restrictions still apply; do not describe
  NY Fed content as blanket public domain. No separate AI prohibition was found
  in reviewed public terms; this does not authorize unrelated training corpora.
- Treasury: `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance`.
  Bounded metadata/schema sampling succeeded. The closing-label row's value is
  in `open_today_bal`; metadata must state `$1,000,000`. Opening-label rows and
  null closing values are never zero. [About Fiscal Data](https://fiscaldata.treasury.gov/about-us/)
  was accessible through direct requests but returned 403 through the web reader.
  Its linked open-data policy was identified; the web reader also returned 403
  for that PDF. The attempted `fiscal.treasury.gov/website-policies.html` was 404.
  Detailed service automation/retention/AI-use review remains unresolved. Public
  accessibility and US government origin alone were not treated as clearance.
  The gated collector makes NO request and emits unavailable coverage; direct
  parser output is excluded by analyst eligibility selection as well.

No authentication, paid API, new dependency, security setting change or access
bypass. Sources record eligibility/timing/rights conditions. No scheduler was
installed. Poll coordination and source-specific operational review remain
necessary before unattended collection; these collectors are caller driven.

## Time, failures and restart behavior

Reference dates are New York calendar-date markers, with DST handled by zoneinfo.
They are not intraday observation timestamps. Exact publication timestamps are
UNKNOWN in these snapshots. H.4.1 retains its release date separately; it does not
invent 16:30 for holiday exceptions. ON RRP `releaseTime` is offer opening, not
result publication. `lastUpdated` is retained as a publisher update timestamp,
not mislabeled as exact publication; future updates fail closed. First-seen and
retrieval use local acquisition. Availability never precedes local retrieval,
including backfills and newly encountered dated releases.

Canonical store appends correction arrivals and resolves supersession at view_at.
An exact retry of an automatically linked numeric correction now matches the
stored revision link, just as narrative batches already did. Conflicting IDs
still fail; prior history is retained. Unchanged rows preserve earliest knowledge
across restarts. Coverage does not invent IDs for deduplicated unchanged rows.

Requests use connect/read timeouts 3.05/15 seconds, no retries or redirects and a
2 MB response cap. Errors return unavailable coverage batches for caller append;
they do not become numeric zero. Caller must honor provider cooldown/Retry-After
and should not poll a source more than hourly. There is no autonomous retry loop.
Snapshot coverage counts usable rows, explicitly does not certify intervening
dates, business-day calendars, holidays or complete historical coverage. Missing
cells yield unknown metric coverage. Invalid labels/units/dates/numbers fail the
snapshot atomically. Daily stale threshold is four calendar days; weekly ten;
these are conservative heuristics, not a certified holiday calendar.

The 28,000-character context budget remains. A dedicated liquidity section keeps
BTC signals, scheduled macro and broad narrative sections. Whole records and IDs
are retained or explicitly disclosed as omitted. Macro/coverage/evidence section
budgets were rebalanced; representative fixtures and actual combined graph pass.
Large histories can still omit detail by design; complete lineage stays in store.

## Verification evidence

Deterministic tests cover each schema, units, date/column mismatch, missing values,
malformed/nonfinite values, duplicates, DST, future updates, eligibility gates,
HTTP failure/429/redirect/oversize, idempotence, correction retries, before/after
view_at, reopen and staleness. The actual TradingAgentsGraph test combines BTC
funding, H.4.1, ON RRP and a flood/agriculture/infrastructure world event, and
excludes a later correction. Models and vendor responses are scripted, no live LLM.
Final focused/full-suite counts are recorded in the session verification addendum.

Live samples on October 30 (Asia/Saigon), separate from mock correctness:

- Initial network-restricted attempts failed DNS for all three publishers. After
  network permission, dated H.4.1 returned HTTP 200 / 680,660 bytes; latest-one
  ON RRP returned 200 / 686 bytes; two-row unfiltered DTS returned 200 / 2,794 bytes.
- Live H.4.1 parsing exposed a `<br>` normalization defect not present in the
  first fixture. Fixed and included in fixtures. Reparsed the downloaded dated
  release and appended five observations at conservative parse/acquisition time
  `2026-10-30T04:27:21.334372Z`, with earlier view excluded and reopen verified.
  October 28 assets 6,745,635; reserves average 2,893,770 / Wednesday 2,895,236;
  TGA average 999,727 / Wednesday 1,015,632 — all million USD.
- ON RRP last-100 collector appended 100 operations at
  `2026-10-30T04:25:36.597816Z` into the existing configured canonical live-trial
  database, not another store. Latest October 29 accepted 353,000,000 USD.
  Reopen and before-acquisition exclusion passed. API schema and public UI asset
  both returned 200. No claim of historical vintages or continuous operations.
- Filtered DTS closing-row sample returned 200: October 28 = 1,015,632 and
  October 27 = 1,052,530 million USD in `open_today_bal`. Schema validation passed;
  pending-source numerical evidence was NOT appended to the live store or sent
  to the analyst. Gated unavailable coverage was appended.
- Combined live-store renderer after H.4.1: 12,671 characters. Raw sampled files
  and `m2a1-live-report.json` remain in local-runtime outside Git. No live LLM,
  trading, production readiness or predictive-quality claim.

## Next

1. Resolve daily Treasury TGA service-use eligibility and historical DTS schema,
   then enable only through a reviewed source-definition change and tests.
2. M2A.2: BLS CPI/core CPI and employment, Treasury yield expansion, BEA GDP and
   headline/core PCE price indexes, following the existing ordered macro sequence.
   Free registration where necessary is separate from a paid dependency.
3. NONNEGOTIABLE Phase 3 world radar remains parallel product scope: war,
   drought, floods, agriculture, energy, infrastructure, cyber, technology,
   pandemics, regulation and crypto. Discovery must have no BTC keyword or price
   anomaly gate. Specialized breadth/operational coverage remains unproven and
   is not fulfilled by this macro work. M2B-D and Phase 4 are separate backlogs.

Future pushes require explicit authorization for these new commits. If Work's
MSYS helper restriction persists, use ordinary non-elevated host PowerShell;
never make broken synchronization a prerequisite for authorized local work.

## Final verification addendum

- Focused liquidity/store/context/actual graph: **68 passed**, 7.80 seconds.
- Full offline suite after the live-discovered HTML fix: **1,445 passed**, **99
  subtests passed**, 4 skipped, 1 integration test deselected, 34.89 seconds.
  Skips: three POSIX file-mode tests on Windows and optional langchain_aws absent.
- `ruff check tradingagents cli tests`: passed. Changed-file lint also passed.
  A broad directory lint included the pre-existing untracked `.phase12-tools/`
  dependency copies; their diagnostics are not project-source regressions and
  nothing there was edited.
- Syntax compilation of changed Python files passed; final whitespace/diff check
  passed. No new mandatory packages. Full suite's shared fixtures prohibit
  network, including the scripted actual graph run.
- Modified implementation: `liquidity.py` (new), `consumer.py`, `store.py` and
  information README. New `tests/test_liquidity.py`; combined actual graph case
  in `tests/test_graph_end_to_end.py`. Seven living documents updated with current
  delivered/pending checkpoint; this report contains detailed evidence.
- Review: exact H.4.1 cells/headers versus live release, ON RRP selection/units,
  future/reference/acquisition times, revision retry behavior, pending eligibility
  exclusion, prompt-budget preservation, protected-path and staged-diff checks.
  Local commit identity is reported in the final response; no push performed.
