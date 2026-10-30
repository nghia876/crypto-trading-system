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

# Current handoff navigation — 2026-10-30

Read the [living checkpoint](../project-settings/PROJECT_STATUS_AND_PHASE_2_HANDOFF.md), [Phase 3 roadmap](PHASE_3_ARCHITECTURE.md) and [coverage gaps](SOURCE_COVERAGE_MATRIX.md) for current binding scope and next-session instructions. This 3.2C handoff remains historical evidence; later release verification and the [canonical-store trial](NEXT_GITHUB_CANONICAL_STORE.md) supersede its blocked-regression/no-trial status. M2A has NOT started. Comprehensive world discovery belongs to Phase 3 now; macro restoration is only complementary.

# Phase 3.2C / M0 + M1 handoff — 2026-10-29

**Follow-up:** [release verification](M0_M1_RELEASE_VERIFICATION.md) now records
the full regression/graph pass and remaining live gate limits. See also the
[macro eligibility decision and original-source mapping](MACRO_SOURCE_ELIGIBILITY.md).
The original blocked test results below are retained as historical session results.

Status: implementation and LIMITED offline gate VERIFIED; full graph regression
and operational live gate BLOCKED/NOT PASSED. Phase 3 remains IN_PROGRESS.
This supplements prior handoffs and the [nine-family matrix](SOURCE_COVERAGE_MATRIX.md).

## Actual baseline and preservation

Local branch `phase-3-event-narrative-slice`, initial HEAD
`78ac4d58299dea94b3655ed98029762b6d226277`; tracked tree clean, only pre-existing
`.phase12-tools/` untracked. Confirmed origin fetch/push
`https://github.com/nghia876/crypto-trading-system.git`.
GitHub connector comparison independently reported identical Phase 3 HEAD and
Phase 2 ancestry (three commits ahead of `22b804066284dd80557af16c1aa8193271feb43f`).
After network permission, `git ls-remote` confirmed Phase 3 at 78ac4d5, Phase 2 at
22b8040 and main at `1394a3f72aa4393e1a98f51b382434c4b4c2d972`.
Local merge-base ancestry checks also passed for Phase 2 and main.
No reset, overwrite, main edit, canonical sources edit or .phase12-tools access/staging.
No second runtime database, registry, graph, daemon, paid library or API was added.

## Implemented

- `information/polling.py`: recurring due-source coordinator over EXISTING
  `news.poll_once` and SQLiteInformationStore. Defaults unchanged: BBC world/tech,
  GDELT geopolitical/tech. No BTC symbols, prices, market anomalies or analyst
  requests gate acquisition. No automatic semantic extraction/confirmation.
- Immutable existing per-source poll outcomes ARE checkpoints. Logical attempt IDs
  include cadence, UTC slot and complete config fingerprint. Atomic append retains
  source definition, articles and outcome together. Restart skips committed polls;
  pre-commit crash may refetch, never duplicates a committed logical attempt.
  Later polls deliberately retain acquisition copies of the same article/version:
  local first-seen remains earliest; canonical selection collapses current articles.
- At most 16 configured sources; source request budget 2..16, default 4. Domain
  round-robin and oldest-due provider order. At most ONE request per host per job,
  30-second host floor across known configured sources. With defaults, at most two
  requests/job; a one-minute trigger visits deferred providers on the next job.
  Keep the stable complete config set when calling the Python API: host policy is
  evaluated across that configured set. CLI always uses all default configurations.
- No immediate network retries. Subsequent jobs apply exponential failure backoff
  (first failure doubles cadence; max ordinary delay 24h) and valid HTTP Retry-After
  seconds/date lower bound, including >24h. 429/503 blocks the same configured host
  until due. Invalid/nonfinite headers are ignored; huge finite values safely defer
  to representable maximum time. Configuration changes deliberately restart state.
- Streaming adapter retains 2MB/100-item default cap (max250), 3.05s connect/10s read,
  no redirects; elapsed check after each chunk rejects >20s. A blocking read/DNS can
  exceed wall target: Task Scheduler hard stop below is the outer process limit.
  Errors are persisted by class/status without arbitrary remote error text.
- Append-only `narrative.collection_health` coverage captures latest attempt,
  eligible nonempty result, newest publication/unknown publication count, content
  stale (>1day), acquisition stale (>2 cadences), empty/failure, consecutive failures,
  overdue and missed-interval gaps, >1day rolling-window gaps, and budget deferrals.
  Completeness and independence remain UNKNOWN. No-events inference is prohibited.
  Health command displays timestamped stored snapshots, not a continuously updated
  monitor; inspect observed_at when the job itself stops running.
- `store.py:polling_history` reads at most 12 recent checkpoints plus latest success;
  additive partial index on the existing coverage journal. `evidence_by_ids` reads
  <=250 evidence IDs under the same exact cutoff gate. No full evidence-store scan
  in the polling coordinator. Failure count saturates at retained history (12),
  sufficient for capped backoff; it is not a lifetime failure counter.
- CLI OS file lock serializes jobs for the resolved store path; Windows msvcrt or
  POSIX flock, released on crash. Lock file is coordination only, not an evidence
  database; do not delete it while a job runs. Python API callers must use job_lock.
- Existing narrative renderer/consumer/analyst graph unchanged. Publication, local
  first-seen, retrieval and conservative availability semantics are inherited.
  Source corrections and curated claim assertions remain append-only. No source
  host/publisher/domain count is promoted to independent corroboration.

## Operational commands / Windows scheduling

Run from this checkout using its existing Python environment. `CANONICAL.sqlite`
is a placeholder: use the EXACT existing graph config `information_store_path`.
There is no default production store path in this checkout; do not create a second
news database. Ensure its parent exists and set graph and job to the same absolute
path. Synthetic test databases are disposable verification fixtures only.

```powershell
$python = (Resolve-Path ../.phase2-release-env/Scripts/python.exe).Path
$store = 'ABSOLUTE_PATH_TO_THE_EXISTING_CANONICAL.sqlite'
& $python -m tradingagents.information.polling poll-once --store $store --interval 900 --max-sources 4
& $python -m tradingagents.information.polling health --store $store
```

`poll-once` means one bounded coordinator invocation, not force-fetch of sources
that are still in cooldown. Exit 1 indicates attempted-source failure; lock contention
also fails visibly. No tight retries; next trigger evaluates persisted state.
Set up Task Scheduler only after live/usage gates are accepted:

1. Action: the absolute Python executable above; arguments exactly the poll-once
   module/arguments above with quoted absolute store path. Set Start in to checkout.
2. Trigger every ONE minute indefinitely; per-source desired cadence remains 900s.
   Use the normal user account, no elevation, no credentials/API keys in arguments.
3. Settings: **Do not start a new instance**; **run as soon as possible after a
   scheduled start is missed**; stop task if running >THREE minutes. Do not configure
   automatic immediate restarts on failure; subsequent normal triggers handle backoff.
4. Task History/Last Run Result plus timestamped health snapshots expose failures.
   Stopping/disabling the task stops collection; no application daemon remains.
5. Re-enable after an interruption and inspect late/missed/window-gap fields. The
   rolling 1-day GDELT/finite RSS window does not recover full historical coverage.

No scheduled task was installed by this implementation session. The API is available
for an already configured canonical store; deployment/access clearance is separate.

## Reproducible verification

```powershell
$env:TEMP=(Resolve-Path ../.phase2-release-temp).Path
$env:TMP=$env:TEMP
& $python -m pytest -q --basetemp=../.phase2-release-temp/pytest-m1-full
# If native imports are blocked, LIMITED pure information tests only:
& $python -m tests.run_information_offline
# Opt-in real loopback HTTP, no provider/DNS/TLS validation:
& $python -m tests.local_news_smoke
& $python -m tradingagents.information.network_diagnostics
```

The limited runner leaves shared conftest untouched, explicitly denies Python socket
network access, disables optional plugin autoload and selects information-layer
files. It uses `--noconftest` because normal shared setup imports blocked native
pandas through yfinance. It is NOT equivalent to the full project/graph suite.
No blocked DLL was replaced, disabled or bypassed; no dependencies were altered.

New cases cover repeat/reopen, partial crash, no duplicate committed attempts,
first-seen, future cutoff, non-BTC war/science/corrections, empty/error/backoff,
Retry-After dates/invalid/nonfinite/huge values, host/domain fairness, late/window
gaps, stale publication, exact microsecond checkpoint/evidence gates, bounded
history reads, consumer/claims replay and 28k context, and OS lock/release.
The new `test_recurring_poll_reaches_graph_at_cutoff` is authored but actual graph
execution remains UNVERIFIED due to environment failures described below.
Existing Fed and Phase 2 tests are included in limited verification.

## Network findings and actual gates

Initial four feed requests and separate BBC/GDELT/Fed lookups reproduced DNS 11001;
Git getaddrinfo thread failed. No proxies or certificate override variables were
configured; CA bundle exists, OpenSSL 3.5.8. No TLS/HTTP reached at that point.
After explicit network permission, DNS resolved for all three hosts. At ~10:56
Asia/Saigon, both BBC snapshots downloaded. Separate real adapter parses returned
27 world and 20 tech articles, zero missing publication dates; all availability
bounds >= local retrieval. This proves only the sampled fetch/parse path.
Both GDELT reads timed out at the configured read timeout; no parsed GDELT live
response or source completeness was verified. No provider outage is inferred.
Loopback real HTTP -> poll -> disposable SQLite -> reopen/repeat -> pre-T exclusion
passed after permission. No TLS disabling, IP pinning, proxy/DNS changes or access
bypass. No live corpus persisted into an unconfigured/new production store.

Full default pytest was attempted twice: Windows Application Control blocks native
pandas DLL imports in shared conftest; initial optional langsmith plugin also hit a
blocked uuid_utils DLL. No full suite or actual graph pass can be claimed. The
bundled runtime has pandas 3.0.1, but replacing dependency/runtime combinations to
work around controls was not performed. Restore an approved working environment
and run full regression/graph before promoting operational readiness.

Licensing blocker discovered: current FRED legal terms explicitly restrict AI-system
development/training uses; see matrix and official link. No FRED code behavior was
changed or live collection attempted here. Original-source alternatives/permission
require M2 investigation. BBC current business/feed reuse clearance also unverified.

## Next

M2: approved test environment/full graph regression; configured canonical-store
prospective trial; GDELT response/rate-limit validation and scheduler/access gates;
liquidity (WALCL/TGA/RRP/reserves), microstructure, on-chain/flow/options contracts;
original-source rights, regional/official/science diversification. M3: measured
origin/correlation accuracy, adversarial evidence and market-reaction alignment.
No Phase 4 reasoning, strategy, paid services, trading credentials or execution.

Final exact verification and release results are appended below after review.

### Final verification and checkpoint release

- Limited offline suite: **138 passed**, 6.38 seconds. New recurring cases plus
  existing Fed/news/claim/store/contract/context and Phase 2 collector regressions.
- Real loopback HTTP smoke: PASS, including durable reopen/no-refetch/pre-T replay.
- CLI help: PASS. Ruff on all seven changed/new Python files: PASS; AST syntax
  parsing of all seven: PASS; git diff --check: PASS. Git reports informational
  LF-to-CRLF conversion warnings on existing Windows-tracked documentation/tests.
- Full default suite: attempted, BLOCKED before collection by Application Control
  native-library import errors. Actual new analyst graph test: authored, NOT RUN.
  No inherited 1,400-test result is represented as a new run.
- Final fetch before commit: remote Phase 3 identical to local baseline (0 ahead,
  0 behind); Phase 2/main refs match verified SHAs. Changes reviewed by explicit
  file list; source files, credentials, data artifacts and .phase12-tools excluded.
- This is an implementation CHECKPOINT backup, not an operational release approval.
  Local feature-branch commit/push follows successful limited checks and review;
  use git log -1 for final SHA, and final response for verified remote equality.

### Actual commit / GitHub backup outcome

Implementation commit: `0e76559a2aa9588531d7ca297fa128fa248fe13f` on
`phase-3-event-narrative-slice`. Final fetch showed 1 ahead / 0 behind; ancestry
check passed. Normal non-force `git push origin HEAD:refs/heads/phase-3-event-narrative-slice`
was attempted and FAILED: Git credential-manager's shell could not create its MSYS
BaseNamedObjects directory (NtCreateDirectoryObject access denied, 0xC0000022), then
Git could not read a username. No credentials were printed or changed.
Post-attempt `git ls-remote` verified remote remained
`78ac4d58299dea94b3655ed98029762b6d226277`.
The implementation and this handoff follow-up remain LOCAL / UNPUSHED. GitHub backup
is BLOCKED by credential-helper execution, independently of read-only GitHub access.
Repair approved host Git authentication/helper execution, then normal push this
feature branch and verify remote SHA; do not force-push or merge main.
Tracked working tree is clean after the handoff follow-up commit; only original
untracked .phase12-tools remains. Use git log -1 for the final documentation HEAD.
