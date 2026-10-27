# Current checkpoint: Phase 3 first slice (2026-10-27)

Current branch: `phase-3-event-narrative-slice`, based on verified local Phase 2
`22b804066284dd80557af16c1aa8193271feb43f`. Phase 2 branch preserved. Remote
Phase 2 branch independently verified via GitHub connector at
`7cb739d0af0fd7d0dd1b398b4c7bf66099bcbdea` (six commits behind local baseline).
No push. Current user authorized local implementation despite older storage gate.

See `docs/project-handoff/PHASE_3_ARCHITECTURE.md` for contracts and
`docs/project-handoff/PHASE_3_HANDOFF.md` for implementation, verified tests and
limitations. First slice: official Fed monetary headlines -> existing PIT store ->
URL/version grouping -> bounded real analyst context. Phase 3 remains in progress;
independence, contradiction lifecycle, continuous scheduling, live validation and
market-reaction controls remain future milestones. No world model/execution/alpha.
Older Phase 2 history follows and is superseded where inconsistent.

# Crypto AI Trading System — Project Status and Phase 2 Handoff

## Final Phase 2 release gate - 2026-10-27

This section supersedes the older pending/unverified status entries below. Verified starting branch: `phase-1.2-btc-ohlcv-collector`; starting HEAD: `db500bf88effc798a038c64057479f552c07d2cb`. The pre-existing three tracked edits were preserved and completed. This release is committed locally on that feature branch; use `git log -1` for its final SHA. No push or remote-state verification was performed.

**Technical release decision: GO for Phase 3 entry on the verified local baseline.** Phase 2's final code/test gate is complete. Existing remote-storage confirmation remains a separate prerequisite before treating the release as durably stored on GitHub. No Phase 3 implementation was added.

The analyst context has a deterministic 28,000-character overall budget, reserved per-section capacity, whole-record omission counts, stable ordering, and explicit warnings that omitted records do not prove absence, freshness, source availability, or complete coverage. Signal evidence, selected macro values, nearest scheduled events, and their metadata receive reserved space; coverage/source details favor sources used by the state, adverse/unknown conditions, and recent records. Uncapped historical condition counts and core freshness remain visible. Spot evidence sampling is disclosed. This is a character bound for the information context, not a token bound for the entire conversation.

Real graph tests capture the actual Market Analyst prompt and verify funding freshness/coverage/source/schema lineage, macro and scheduled-event evidence IDs, current-day UTC availability filtering, historical UTC end-of-day behavior, and backward compatibility when the optional store is unset. Stress tests cover 1,000 coverage records, 1,001 source definitions, 1,001 scheduled events, oversized-record omission, strict size limits, stable ordering, core lineage retention, and spot evidence sampling.

Verification with normal shared `tests/conftest.py` enabled:

- Focused information-layer plus graph suites: **98 passed**.
- Full default offline suite: **1,342 passed; 99 subtests passed; 4 skipped; 1 deselected; 20 warnings**. Skips: three POSIX file-mode cases on Windows and optional `langchain_aws`; integration tests remain excluded by project configuration. No live provider validation was run.
- Ruff on all five changed Python files, AST syntax parsing, and `git diff --check`: **passed**.
- Windows environment repair: dependencies installed into an isolated venv without global installation or dependency/lockfile edits. Editable packaging hit Windows path-length limits, so declared dependencies were installed directly and tests ran from the checkout. Workspace-local TEMP/TMP and pytest basetemp avoid Windows temp permission failures. The existing yfinance isolation test was corrected to require the suite's private temporary cache; Windows temp can legitimately be under the user's home.

Reproduction: use the isolated Python at `../.phase2-release-env/Scripts/python.exe` from the checkout, set TEMP and TMP to `../.phase2-release-temp`, and run `python -m pytest -q --basetemp=../.phase2-release-temp/pytest-recheck`. Use that same Python for `-m ruff check` on the changed files. The environment is retained outside the Git checkout.

Remaining limits: collection and freshness evaluation are caller-driven; no scheduler/alerts or live-source validation; no upstream historical provider vintages; source/event coverage remains incomplete; dollar-index data is a proxy; liquidation snapshots are not a complete liquidation tape. Replay reconstructs only locally ingested information with recorded availability. `sources/` and `.phase12-tools/` were untouched; `.phase12-tools/` remains untracked and unstaged. No change to `main`.

Canonical product vision remains multi-source BTC macro narrative plus micro market state, critical competing explanations, a world/regime model, scenarios, risk and execution, and point-in-time evaluation and learning. This release closes only Phase 2's information/state gate and does not claim delivery of the later narrative, reasoning, execution, or learning layers.

## Prior status history (superseded where inconsistent)

**Status date:** 2026-10-27 (Asia/Saigon)
**Repository:** `nghia876/crypto-trading-system`
**Feature branch:** `phase-1.2-btc-ohlcv-collector`
**Verified baseline HEAD:** `7cb739d0af0fd7d0dd1b398b4c7bf66099bcbdea`
**Local alignment correction commit:** `55689e6e186a13a56eab0248ba9a698ba8adfda7`
**Phase 2:** information-layer alignment is implemented locally; all 75 focused tests pass, while the full suite remains unverified.

## Current verified state

The supplied end-to-end alignment audit reports independent verification that the remote feature branch matched local `7cb739d0af0fd7d0dd1b398b4c7bf66099bcbdea`, including the Phase 2 handoff. This supersedes the earlier stale remote SHA claim in this document. The current alignment correction is local-only and was not pushed.

The completion pass began on `phase-1.2-btc-ohlcv-collector` at `1e1a4d69a6cee291c673c5ffdd2e3d9957841583`. `main` was not changed. `.phase12-tools/` remains untracked and must never be staged. Keep all `sources/` files read-only.

## Phase 2 exit criteria and evidence

The Blueprint defines Phase 2 as market state, derivatives state, macro state, and scheduled events. Its exits are reproducible state, freshness monitoring, and historical reconstruction.

- **Reproducible state — PASS:** point-in-time views deterministically derive spot, derivatives, selected macro, and scheduled-event state with evidence.
- **Freshness monitoring — PASS:** applicable state fields report fresh/stale/unknown when a caller builds state. Collection is caller-driven; ongoing scheduler/alerts are not implemented.
- **Historical reconstruction — PASS for locally ingested data:** SQLite replay gates observations by known availability, retains revisions/reschedules, and tests before/after visibility. Unknown upstream publication times and historical vintages cannot be reconstructed.

Original Phase 2 verification (before the alignment correction): 70 focused tests passed across nine information-layer test files using pytest without shared `tests/conftest.py`; Ruff lint, Phase 2 changed-file format check, and `git diff --check` pass. Full-suite pytest remains unverified because shared setup imports unavailable `yfinance` and `curl_cffi`. Tests use mocked source replies. BLS runtime access returned HTTP 403, Treasury live persistence/reopen replay is not verified, event coverage is not exhaustive, and the broad dollar index is a proxy rather than ICE DXY. See repository `docs/project-handoff/PHASE_2_HANDOFF.md` for detail.

## Alignment correction applied locally (2026-10-27)

The follow-up audit identified a contract gap in generic source coverage and metric interpretation. On the verified feature branch, the local correction adds per-observation `schema_version` and `unit` fields, persists and replays them in SQLite (including additive migration for existing databases), and adds timestamped coverage records with statuses for present, absent, unavailable, stale, unknown, not applicable, low quality, negative evidence, and complete. Coverage records carry source/metric identity, detail, evidence IDs, and are filtered by their observation time in `InformationView`. Existing point-in-time state builders continue to consume one `InformationView` at decision time T; existing event identity, supersession, schedule status, and availability semantics remain in place.

Focused verification after the correction: 72 information-layer tests pass; Ruff lint and `git diff --check` pass. Tests were run from a private copy under `.phase12-tools/` to avoid the shared `tests/conftest.py`, whose import-time `yfinance` dependency is unavailable. The full suite remains unverified.

**Current implementation base:** `1e1a4d69a6cee291c673c5ffdd2e3d9957841583`; completion changes are uncommitted pending verification.

**Completion pass (2026-10-27):** source definitions have explicit versions and are durably appended/replayed with their observation-time metadata. All information-layer batch-producing collectors now attach a source snapshot and explicit coverage record on successful collection/parse; observations declare schema and metric units for spot, derivatives, macro series, Treasury yields, scheduled events, and liquidation snapshots. Empty source responses remain unknown unless the collector has affirmative coverage evidence. Optional `information_store_path` integration builds one replay view at the trade-date UTC cutoff and includes its derived market context and evidence IDs in the analyst input. The nine focused information-layer suites pass (75 tests); Ruff and `git diff --check` pass. Full-suite pytest remains unverified because shared setup imports unavailable `yfinance`. Collection remains caller-driven; no scheduler, live-source validation, or upstream historical publication-vintage reconstruction was added. Do not treat this as Phase 3 authorization. `.phase12-tools/` remains untracked and excluded from Git.

## Phase 3 gate

**Do not start Phase 3 implementation until the alignment gaps below are resolved and the correction commit is stored on the feature branch.** The earlier remote storage gate is reported complete by the supplied audit for the pre-correction commit; the new local correction has not been pushed. After storage is confirmed, create/use a normal chat as the Phase 3 master/checkpoint. Keep implementation in a separate Work session. Phase 3's next subject is event/narrative intelligence; first propose and agree on a scoped plan and exit checks.

## Prompt for the Phase 3 master/checkpoint chat

Continue the Crypto AI Trading System from the verified Phase 2 handoff. This is a normal chat used as the Phase 3 master/checkpoint, not the implementation work session. Do not begin Phase 3 implementation in this chat.

First verify GitHub repository `nghia876/crypto-trading-system`, branch `phase-1.2-btc-ohlcv-collector`, and `docs/project-handoff/PHASE_2_HANDOFF.md`. Confirm the remote branch contains the Phase 2 commits and handoff before treating Phase 2 as durably closed. If they are missing, report the exact local and remote SHAs and stop at the storage blocker. Never switch to or modify `main`; never overwrite/reset user changes; never stage `.phase12-tools/`; treat `sources/` as read-only; and do not push without explicit approval.

Use code and tests as authority over project documents and conversation history. Do not overstate live-source or full-suite verification. Once remote storage is confirmed, review the Blueprint's Phase 3 event/narrative-intelligence scope and propose an evidence-based work plan with acceptance criteria. Keep this chat for checkpoint decisions and use a separate Work session for implementation after the user chooses the next step.
