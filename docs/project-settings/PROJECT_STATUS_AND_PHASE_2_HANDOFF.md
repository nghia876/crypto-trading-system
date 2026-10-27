# Crypto AI Trading System — Project Status and Phase 2 Handoff

**Status date:** 2026-10-27 (Asia/Saigon)
**Repository:** `nghia876/crypto-trading-system`
**Feature branch:** `phase-1.2-btc-ohlcv-collector`
**Verified baseline HEAD:** `7cb739d0af0fd7d0dd1b398b4c7bf66099bcbdea`
**Local alignment correction commit:** `55689e6e186a13a56eab0248ba9a698ba8adfda7`
**Phase 2:** alignment completion is implemented and focused information-layer verification passes locally; no push was made.

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

**Completion pass (2026-10-27):** source definitions have explicit versions and are durably appended/replayed with their observation-time metadata. Binance Spot and USDⓈ-M collectors attach successful-response coverage records, source snapshots, and explicit schema/unit declarations. Optional `information_store_path` integration builds one replay view at the trade-date UTC cutoff and includes its derived market context and evidence IDs in the analyst input. Missing data is rendered as unknown, not negative evidence. The nine focused information-layer suites pass (75 tests); Ruff and `git diff --check` pass. Full-suite pytest remains unverified because shared setup imports unavailable `yfinance`. Other collector families may still emit default units or omit coverage, no collection scheduler or live-source validation was added, and upstream historical publication vintages remain unavailable. Do not treat this as Phase 3 authorization. `.phase12-tools/` remains untracked and excluded from Git.

## Phase 3 gate

**Do not start Phase 3 implementation until the alignment gaps below are resolved and the correction commit is stored on the feature branch.** The earlier remote storage gate is reported complete by the supplied audit for the pre-correction commit; the new local correction has not been pushed. After storage is confirmed, create/use a normal chat as the Phase 3 master/checkpoint. Keep implementation in a separate Work session. Phase 3's next subject is event/narrative intelligence; first propose and agree on a scoped plan and exit checks.

## Prompt for the Phase 3 master/checkpoint chat

Continue the Crypto AI Trading System from the verified Phase 2 handoff. This is a normal chat used as the Phase 3 master/checkpoint, not the implementation work session. Do not begin Phase 3 implementation in this chat.

First verify GitHub repository `nghia876/crypto-trading-system`, branch `phase-1.2-btc-ohlcv-collector`, and `docs/project-handoff/PHASE_2_HANDOFF.md`. Confirm the remote branch contains the Phase 2 commits and handoff before treating Phase 2 as durably closed. If they are missing, report the exact local and remote SHAs and stop at the storage blocker. Never switch to or modify `main`; never overwrite/reset user changes; never stage `.phase12-tools/`; treat `sources/` as read-only; and do not push without explicit approval.

Use code and tests as authority over project documents and conversation history. Do not overstate live-source or full-suite verification. Once remote storage is confirmed, review the Blueprint's Phase 3 event/narrative-intelligence scope and propose an evidence-based work plan with acceptance criteria. Keep this chat for checkpoint decisions and use a separate Work session for implementation after the user chooses the next step.
