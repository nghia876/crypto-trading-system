# Current M2A.1 checkpoint — 2026-10-30

M2A.1 is locally implemented and tested for the eligible subset: original Board
H.4.1 assets, reserves and distinct weekly-average/Wednesday TGA; NY Fed overnight
Treasury RRP results. All use existing contracts, canonical SQLite/view_at and
actual Market Analyst context. Daily Treasury TGA parsing is implemented and
sampled, but collection and analyst use remain gated pending detailed service
terms review. FRED remains disabled by default. See [implementation and evidence](M2A1_IMPLEMENTATION.md)
for exact metrics, rights, times, tests, live measurements and limitations.

User confirms documentation checkpoint `82c6ba6` was pushed; Gate 1 complete.
New M2A.1 commits stay local. No push is a prerequisite for local implementation.
Historical NOT STARTED statements below are superseded for this eligible subset.
M2A.2 (BLS, yield expansion, BEA GDP/PCE) remains unimplemented. Comprehensive
Phase 3 world-event radar remains required: war, drought, floods, agriculture,
energy, infrastructure, cyber, technology and pandemics, with no BTC keyword or
price-anomaly discovery gates. This macro slice does not complete world coverage.

# M2A scope boundary — 2026-10-30

The original-publisher mapping below supports narrow M2A structured macro restoration, which has NOT started. Include BEA GDP and headline/core PCE price indexes (separate from consumption spending); exact PCE table/line, units and revision mapping remain to be validated as described in the [six-step sequence](NEXT_GITHUB_CANONICAL_STORE.md). No mapping grants blanket eligibility or proves replacement coverage.

M2A complements Phase 3 comprehensive world radar; it does not substitute for or postpone environmental, agricultural, disaster, energy, geopolitical, health, technology, cyber, regulatory or crypto discovery. See [binding architecture/roadmap](PHASE_3_ARCHITECTURE.md) and [source gaps](SOURCE_COVERAGE_MATRIX.md). Retain the existing canonical SQLite store and free-only legally eligible sources; default FRED remains disabled. Historical M2 references below mean bounded macro work where applicable, not all world-event acquisition.

# Bounded macro source eligibility review — 2026-10-29

Decision: default `data_vendors.macro_data` is `disabled`. The router returns an
explicit missing-coverage sentinel without a request. Explicit `fred` configurations,
parsers, collectors and tests remain compatible; this is not a global prohibition
or permission grant. The caller-driven graph-CSV collector is not scheduled by M1.
Do not activate it automatically pending review. No replacement collector is added.

## FRED findings

Reviewed [current full terms](https://fred.stlouisfed.org/legal/) and the
[separate API terms page](https://fred.stlouisfed.org/docs/api/terms_of_use.html).
The current full page restricts development/training uses (API prohibition k),
and caching, archiving and database incorporation (API l; general prohibition p).
These materially conflict with developing this system and its persistent evidence
store. Inference-only use is not clearly resolved by that wording; no conclusion
that every inference use is forbidden or permitted is made. The older separate
API page does not remove the current page's restrictions. Obtain clarification
before enabling FRED. Graph CSV is not an eligibility workaround.

Preserve original-provider notices and FRED attribution for any permitted use;
API use also has an endorsement-disclaimer requirement. Third-party series need
their own rights review. Public-domain underlying statistics do not establish
permission to use the FRED service in this architecture. This is an engineering
eligibility decision, not legal advice or a finding of legal certainty.

## Original-publisher mapping and remaining implementation gaps

These are candidate mappings, not claims of implemented or numerical equivalence.
All candidates must enter the existing SQLiteInformationStore and analyst view.
No second database, paid dependency, or BTC-keyword acquisition filter is proposed.

| Required evidence / FRED identifier | Original publisher and exact candidate | Cadence / availability | Vintage and gap handling |
|---|---|---|---|
| Fed balance sheet / WALCL | [Board H.4.1](https://www.federalreserve.gov/releases/h41/current/), table 5 total assets, Wednesday level, millions USD | Weekly Thursday generally 16:30 Eastern; holiday exceptions | Archive dated releases; distinguish Wednesday level from weekly average and reserve-bank credit. Validate FRED mapping before substitution. |
| TGA / WTREGEN, WDTGAL | H.4.1 table 1 Treasury general account: weekly average for WTREGEN; Wednesday column for WDTGAL | Weekly H.4.1 release | Preserve both distinct statistics. [Treasury DTS](https://fiscal.treasury.gov/accounting/daily-treasury-statement) daily operating cash balance is an additional daily measure, not an interchangeable weekly average. |
| Daily TGA | [Fiscal Data API](https://fiscaldata.treasury.gov/api-documentation/), `/v1/accounting/dts/operating_cash_balance`: select `account_type` = Treasury General Account (TGA) Closing Balance and `record_date` | Business-day statement, generally following business day; verify current calendar | Live October 27 row has value 1052530 in `open_today_bal`, in millions USD per metadata; `close_today_bal` is null. Do not select opening balance or infer field meaning from its name. Validate historical schema transitions and dated statement reconciliation. |
| ON RRP / RRPONTSYD | [NY Fed operations](https://www.newyorkfed.org/markets/desk-operations/reverse-repo), [Markets API](https://markets.newyorkfed.org/static/docs/markets-api.html), `/api/rp/reverserepo/all/results/last/1.json`, `repo.operations[].totalAmtAccepted` for overnight Treasury operations | Daily operation results; publication after operation | Live October 28 sample has `term=Overnight`, Treasury details, accepted amount 176000000. Confirm API dollar units before billion-USD normalization. Do not equate with H.4.1 total reverse repos (includes other counterparties). Archive corrections prospectively. |
| Reserves / WRESBAL | H.4.1 table 1 reserve balances with Federal Reserve Banks, weekly average, millions USD | Weekly; separate Wednesday level | Reconcile the exact column and units; preserve release copies, not retrospectively revised current rows. |
| CPI / CPIAUCSL, CPILFESL | [BLS API](https://www.bls.gov/developers/): `CUSR0000SA0`, `CUSR0000SA0L1E` | Monthly release, normally 08:30 Eastern; calendar authoritative | Seasonally adjusted indexes; derive MoM/YoY explicitly, not from rounded headline values. Seasonal revisions mean current API values are not historical vintages. Archive releases and annual revisions. |
| Employment / PAYEMS, UNRATE | BLS `CES0000000001` (thousands, SA), `LNS14000000` (percent, SA) | Monthly Employment Situation, normally 08:30 Eastern | Payroll revisions and annual benchmarks; household unemployment and establishment jobs are distinct. Save dated releases and revisions. |
| GDP / GDP, GDPC1, A191RL1Q225SBEA | [BEA API](https://www.bea.gov/API/signup), NIPA `T10105` line 1 nominal GDP; `T10106` line 1 real GDP; `T10101` line 1 real GDP percent change | Quarterly advance/second/third estimates, normally 08:30 Eastern; annual updates | Verify current units/base year from metadata. Real growth is annualized, levels SAAR. API current tables are not vintage reconstruction. Free API key required; key not requested here. |
| Treasury yields / DGS2, DGS10 | [Treasury official daily par curve XML](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed), `BC_2YEAR`, `BC_10YEAR`; existing direct Treasury CSV adapter covers 10y | Business-day end-of-day observations; exact release timestamp absent in rows | Match maturity/methodology/date and units before claiming equivalence with H.15/FRED. Current-year files lack vintage history; archive local snapshots and corrections. |

Common availability rule: reference date is not release time. Store publisher release
time when actually evidenced, first-seen and retrieval separately; conservative replay
availability must not precede local acquisition. Previously unseen historical values
are unavailable at earlier decision cutoffs. Append revisions and source versions;
never overwrite earlier known values. Historical source archives may support separate
vintage research but do not prove this installation knew an observation then.

## Access and rights assessment

- [Board policy](https://www.federalreserve.gov/disclaimer.htm): Board information
  is generally public domain unless indicated; cite the Board and inspect exceptions.
  H.4.1 release was accessible. The page announces DDP changes in November 2026;
  do not build a replacement around a presumed permanent DDP endpoint.
- [BLS policy](https://www.bls.gov/bls/linksite.htm): statistical publications are
  public domain; citation requested. Free API supports limited unregistered requests;
  registration expands limits. Respect current quotas; API access and release archives
  still need production validation. A live unregistered CPI request succeeded and
  returned September 2026 for CUSR0000SA0; this does not establish archive coverage.
- [BEA copyright FAQ](https://www.bea.gov/help/faq/147): generally public domain
  unless stated otherwise. Official search result accessible; direct FAQ fetch timed
  out. API signup documentation accessible; authenticated data response not tested.
- [NY Fed terms](https://www.newyorkfed.org/privacy/termsofuse) permit automated
  access, storage and use for personal/business purposes subject to conditions.
  Preserve notices/source identifiers, attribution and terms link; label transformations,
  avoid endorsement, and inspect content-specific restrictions. Not blanket public domain.
- Treasury endpoints are public/free candidates. Fiscal Data documentation returned
  403 to the web reader, but direct API returned JSON including TGA rows and unit
  metadata. Detailed current license/usage review remains open. Public access alone
  is not a rights clearance. The bounded existing Treasury CSV request timed out.

Additional existing FRED context needs separate coverage: DTWEXBGS -> Board H.10
broad dollar index (not ICE DXY); DCOILWTICO -> EIA WTI Cushing spot (free API key);
NFCI -> Chicago Fed original NFCI, subject to that publisher's terms. S&P 500 and VIX
remain third-party licensing gaps; do not silently replace them with unrelated proxies.
The existing alias vendor also covers indicators beyond this bounded US review;
those are not cleared or replaced here.

## BTC vision acceptance criteria for M2

Preserve liquidity, inflation, labor, growth and rate evidence alongside broad war,
policy and technology information. Disabling FRED leaves an explicit macro coverage
gap today. The goal is preserved by the required mapping above, not yet delivered by
replacement code. M2 must implement eligible adapters in the same contracts/store,
validate units/column definitions and publication timing, prove prospective revision
replay, and expose missing/stale coverage to the analyst. A net-liquidity calculation
such as assets minus TGA minus RRP is a labeled transformation, not reserves or a
causal BTC predictor; mismatched daily/weekly observations require explicit alignment.
M3 then measures provenance/correlation and market reaction; no equivalence or
predictive-quality claim is made by this review.
