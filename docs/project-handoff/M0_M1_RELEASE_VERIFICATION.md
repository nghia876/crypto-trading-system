# M0 + M1 release verification — 2026-10-29

This follow-up supersedes the previous environment-blocked regression status in
[Phase 3.2C](PHASE_3_2C_HANDOFF.md). Phase 3 remains in progress; operational live
readiness is NOT approved.

## Observed repository state

- Existing checkout: `phase-3-event-narrative-slice`, starting HEAD
  `c28ebc5ce9af37eb709d97bae18b0cb624b35124`.
- Initial tracked tree clean; only pre-existing `.phase12-tools/` untracked.
- Verified origin: `https://github.com/nghia876/crypto-trading-system.git`.
- Fetch and ls-remote confirmed remote feature HEAD
  `78ac4d58299dea94b3655ed98029762b6d226277`, 0 behind / 2 ahead initially.
  Remote feature ref is an ancestor of local HEAD. Phase 2 commit `22b8040` and
  remote main `1394a3f` are also ancestors. Main was not switched or modified.
- Synced sources and `.phase12-tools/` were not edited or staged; no history rewrite.

## Tests actually executed

Existing release environment: Python 3.12.14, pandas 3.1.0. Imports of pandas,
pytest, yfinance, langgraph and langchain_openai passed. No dependency changes.

| Check | Observed result |
|---|---|
| Full default offline pytest before edits | 1419 passed, 4 skipped, 1 deselected; 99 subtests; 40.85 s |
| Full default offline pytest after changes | 1420 passed, 4 skipped, 1 deselected; 99 subtests; 35.61 s |
| Focused graph, recurring news, broad news, SQLite store, FRED | 103 passed; 8 subtests; 9.34 s |
| Explicit recurring-poll graph cutoff + real Market Analyst context + FRED | 25 passed; 8 subtests; 2.28 s |
| Real loopback HTTP -> poll -> SQLite -> reopen/no-refetch/cutoff | PASS, disposable synthetic fixture removed |
| Ruff on ten release-related Python files | PASS |
| AST parse for changed Python files; git diff --check | PASS |
| Pending backup file review for secret literals, private keys, absolute private paths | No candidates found; no tracked database, credentials or protected tools artifacts |

The full suite excludes one external integration test by the repository's default
marker. Three skips are POSIX permissions checks on Windows; one is optional missing
`langchain_aws`. Twenty warnings concern model-name recognition. Actual graph nodes,
tools, state and analyst prompt paths ran with scripted LLMs and mocked vendor data;
this is not a live model-provider or trading-quality validation.

The disabled default initially exposed two all-tools graph fixture expectations.
Those tests now explicitly opt into mocked FRED so they still exercise all tool
wiring. A new default-route test proves FRED is not called and missing macro data
is reported. Existing explicit FRED and Phase 2 tests passed unchanged otherwise.

## Bounded live checks

At approximately 13:20 Asia/Saigon, DNS resolved for BBC, GDELT and the Fed. TLS
verification remained enabled; no proxy/certificate override or access workaround.

- BBC world: download and parse PASS, 27 observations; BBC technology: 20.
  Pre-acquisition cutoff excluded all sampled observations. This establishes sampled
  access/parser behavior, not completeness or feed business-reuse clearance.
- Both GDELT configurations: ReadTimeout. No parsed live GDELT response, durable
  production ingestion or rate-limit acceptance can be claimed.
- Board H.4.1: HTTP 200. NY Fed RRP: HTTP 200 and operation JSON inspected.
- Fiscal Data TGA: HTTP 200; latest-date four rows inspected, including the closing
  balance stored in `open_today_bal` with `close_today_bal` null. API metadata reports
  million-dollar units. This is recorded in the replacement matrix.
- BLS CPI: HTTP 200, REQUEST_SUCCEEDED; CUSR0000SA0 September 2026 observation.
- Existing direct Treasury CSV endpoint: ReadTimeout in the bounded sample.
- No FRED data request or paid API/model call was made.

No actual configured canonical-store path or existing SQLite database was found in
the inspected checkout configuration/files. The existing graph still requires explicit
`information_store_path`. No new production store was created and no scheduler was
installed. Canonical production polling, durable live replay and analyst ingestion
therefore remain NOT VERIFIED; synthetic durable replay and actual graph ingestion
were verified separately. Do not infer no events from these coverage gaps.

## Bounded eligibility/default change and next gate

See [macro source eligibility and exact coverage mapping](MACRO_SOURCE_ELIGIBILITY.md).
Default macro routing is disabled pending eligibility review; explicit caller overrides,
FRED code and offline fixtures remain. No replacement is represented as delivered.
M1 news defaults are unchanged. M2 must close eligible direct-publisher macro gaps,
configure the one canonical store, establish prospective live replay and resolve
GDELT and feed rights/operational gates. M3 measures provenance, correlation and
reaction alignment after that evidence exists. Broad financial and non-financial
coverage, free-only access and the existing architecture remain requirements.

## Backup procedure

Commit only explicit release files, fetch origin again, verify feature ancestry,
then normal non-force push `HEAD:refs/heads/phase-3-event-narrative-slice`.
Compare resulting `ls-remote` SHA with local HEAD. The final work report records
the observed commit and push result; this document alone is not proof of a push.
