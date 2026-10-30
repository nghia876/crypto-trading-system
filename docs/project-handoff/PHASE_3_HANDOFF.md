# Current specialist WORLD checkpoint - 2026-10-30

VERIFIED bounded USGS drought/river-flood, EIA energy and NASS agriculture
headline discovery now shares existing news polling, source definitions,
canonical SQLite/replay and the real Market Analyst graph. No BTC keyword or
movement gate. BBC/GDELT broad discovery remains enabled. Automated source-gap
reporting exposes absent adapters, stale content/collection and specialist gaps.
Live samples: drought 8, floods 370, EIA 21, NASS 288 unique eligible articles
(24 external-host entries excluded). No bodies, images, logos or second database.
Narrative reservation is 6,000 characters within the unchanged 28,000 total;
BTC/numerical macro reservations remain protected. Full offline suite:
1,510 passed + 99 subtests; four skipped, one deselected. Ruff/syntax/diff passed.
All 129 live BLS observations preserved; SQLite integrity OK.

Phase 3 remains IN_PROGRESS. US-centric agency headlines do not establish global
hazard/food metrics, grid incident monitoring, wildfire, health, original cyber,
trade or regional coverage. Source reporting is not independent confirmation.
OPEN macro gaps: daily TGA gated; Treasury 2y/10y XML collection/analyst use
rights-gated; BEA GDP/PCE/core PCE numerical integration incomplete; BLS live
release calendar unavailable; FRED disabled. New work is LOCAL ONLY; no push.
See [implementation, rights, exact evidence and next gaps](WORLD_SPECIALIST_IMPLEMENTATION.md).
This checkpoint supersedes older claims below that no specialized adapters exist.

# Latest checkpoint: Phase 3.2A (2026-10-27)

Broad RSS/Atom + GDELT discovery, durable poll outcomes, general news replay and
explicit intraday graph cutoff are now implemented locally on the same branch.
See [PHASE_3_2A_HANDOFF.md](PHASE_3_2A_HANDOFF.md) for current contracts, exact
checks, live-connection limitations and next milestone. The older first-slice
handoff below remains history; Phase 3 as a whole is still IN_PROGRESS.

# Phase 3 first-slice handoff

Date: 2026-10-27 (Asia/Saigon). Status: first slice locally VERIFIED by the checks
below; Phase 3 as a whole remains IN_PROGRESS. See PHASE_3_ARCHITECTURE.md for
contract definitions, decisions, alternatives, product alignment and milestones.

## Preservation and remote evidence

Local baseline verified at `22b804066284dd80557af16c1aa8193271feb43f` on
`phase-1.2-btc-ohlcv-collector`, tracked tree initially clean. Separate working
branch: `phase-3-event-narrative-slice`, created from that exact commit. The Phase 2
branch still points to the baseline. GitHub connector independently resolved the
remote Phase 2 branch at `7cb739d0af0fd7d0dd1b398b4c7bf66099bcbdea`, an ancestor six
commits behind. Direct `git ls-remote` failed with a network lookup error; connector
verification succeeded. No push or merge; main untouched. Remote storage of the
local baseline and Phase 3 work remains pending. Current user instructions
explicitly authorize continuing locally despite the older handoff storage gate.

## Implemented

- Federal Reserve official monetary RSS collector/parser with byte/item/headline
  limits, streaming read, timeouts, strict source URL and aware publication-time
  validation; empty snapshot UNKNOWN and invalid snapshot fails atomically.
- Existing Observation, Source, CoverageRecord and MarketDataBatch contracts and
  SQLite store used directly. Event identity is canonical release URL; versions
  preserve source claim, provenance, publication, local observation and conservative
  availability. Same event copies collapse in the derived view, never into votes.
- Narrative polls preserve every evidence reference, even unchanged copies, and
  support idempotent retries after automatic store revision linkage. Existing
  non-narrative skip/revision behavior is preserved. No schema migration.
- Eligible latest versions render beside existing BTC micro, macro and scheduled
  events through the real Market Analyst graph, within the original 28,000-character
  total. Reserved 4,000-character narrative section, stable order, whole-record
  omissions, explicit uncertainty, source claims versus facts, no causal inference.
- Coverage metadata excludes evidence IDs for future-publication observations.
  Publication proxy for unknown event occurrence is labeled explicitly.

## Verification evidence

- Focused information-layer plus real graph suite: **114 passed**.
- Final full default offline suite: **1,358 passed; 99 subtests passed; 4 skipped;
  1 deselected; 20 warnings** (32.69 seconds). Skips: three POSIX file-mode
  tests on Windows and optional langchain_aws. Integration tests remain excluded
  by the project default configuration. No live provider validation.
- Ruff on all five changed Python files, AST syntax parsing, `git diff --check`:
  passed before local commit; staged diff reviewed, explicit paths only.
- Tests cover duplicate items, canonical URL variants, distinct announcements,
  repeated polls without corroboration, append/reopen/revision replay, retry
  idempotency, out-of-order append, future publication and local observation,
  malformed/naive timestamps, invalid host/XML/DTD, oversized inputs, empty feed,
  mocked streamed transport/timeouts, large prompt omissions and determinism.
- Existing graph test extended for current-day and historical cutoffs: actual
  Market Analyst prompt includes eligible event evidence and excludes a correction
  observed one microsecond later. Optional-store compatibility tests remain active.
- During development, test setup needed short parametrization IDs to avoid Windows
  path-length failures; tests were corrected. A revision assertion was corrected
  to account for the existing store's automatic supersession semantics. Those
  initial failed runs are not counted as passing verification.

Reproduction from repository, PowerShell:

```powershell
$env:TEMP = (Resolve-Path ../.phase2-release-temp).Path
$env:TMP = $env:TEMP
../.phase2-release-env/Scripts/python.exe -m pytest -q --basetemp=../.phase2-release-temp/pytest-phase3-reproduce
```

Dependencies reused from the retained isolated Phase 2 environment; no dependency
or lockfile edits. Offline tests use normal shared conftest, not isolated copies.

## Limitations and next milestones

No successful live feed collector run: official feed directory checked via web,
XML feed viewer rejected content type. Mocked tests establish code behavior only,
not provider shape, continuous availability, latency or historical vintages.
Only one official publisher; no independent second source or semantic fact
verification. Cross-posting/repetition is not corroboration. Contradictions are
unsearched; confirmation/reaction timestamps unknown. Only officially_reported
lifecycle output implemented; broader lifecycle is defined but deferred. Correlation
is release-URL identity, not cross-publisher semantic clustering or calendar linkage.
No scheduler, operational failure persistence, complete feed coverage, reaction
causality controls, world/regime model, execution or alpha claims. Feed item
historical event time is unknown; publication is a labeled envelope proxy. Same-time
conflicting observations use deterministic ID selection without semantic resolution.
Historical store growth and full release-body/raw response archiving remain future work.

Next milestones:
1. Validate live feed shape; persist raw snapshot hashes, failure coverage and
   polling health; measure latency and schedule continuous caller-independent radar.
2. Add an independent publisher with claim-level origin/dependency mapping, preserving
   syndication rather than treating repeated articles as confirmation.
3. Implement append-only confirmation/contradiction/stale/resolved transitions,
   claim evidence edges and deterministic calendar correlation.
4. Define and evaluate time-controlled market reaction evidence before causal
   narratives; later advance to world/regime models without collapsing risk/execution.

Use `git log -1` for this handoff's local commit SHA. Final expected repository
status after commit: only pre-existing `.phase12-tools/` untracked and unstaged.
Synced project sources and that tools folder were not edited.
