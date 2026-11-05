# Historical pre-promotion stop — superseded by resume report

The later authorized resume activated the canonical store and performed one live
session, then stopped at the post-live graph gate. See
[current resume result](CANONICAL_ACTIVATION_RESUME_REPORT.md). Original stop
details below are preserved as the historical record.

# Guarded canonical activation stopped before promotion — 2026-11-05

Phase 3 IN_PROGRESS. User authorized activation and one subsequent live session.
Execution STOPPED before promotion on an unresolved frozen evidence manifest
verification failure. No authority configuration, rename, production overwrite,
live collection, commit, push or Checkpoint C work occurred.

## Verified state

Feature branch phase-3-event-narrative-slice; HEAD
d953bcfa3eec86a6c18f06cfbcdd5db750a38842. Read-only GitHub connector resolved
the current branch to c54af8c18e4418f4d34032b422d1c2bf02cc0082. The cached local
origin ref is older (78ac4d5, October 27); no fetch/push changed it. Existing
untracked .phase12-tools/ and bottleneck diagnosis preserved. Synced sources read
only. Private absolute paths, fingerprints and stop record are outside Git in
activation-current-private.json in the workspace parent.

Both original database SHA256 values match the user handoff. Candidate SHA256
1df6303bc5de63687edc6081a4c6282f5dc358740e6c4e79b75386e353d7dceb matches.
Current SQLite integrity/application validation and exact union pass: 1219
observations, 140 source definitions, 163 coverage, zero gaps, 85 revision links.
Seventy before/at availability boundary cutoffs pass exact original-view union
checks for visible/history/coverage. This is a fresh, narrower cutoff set than
the prior 75-cutoff evaluation, not a claim to have rerun all prior checks.

Fresh private SQLite backup-API archives of BOTH originals were independently
reopened, integrity checked and compared by exact rows/schema. Archive files
marked read-only (Windows file attribute; no claim of tamper-proof/WORM storage).
Originals and archives were rehashed and validated at the final stop. Copies are
local; no off-device disaster recovery claim. No Python collector was listed by
Get-Process; detailed CIM process inspection was denied. Exclusive Windows file
handle and switch-time quiescence checks have NOT been performed.

A fresh staged SQLite-consistent production copy in the same runtime directory
has exact candidate rows/schema/record digests. SHA256
c3f152eb6f0cf16e69e8534bbc22bbe82f0d8fbab4072fa03dc687d3a27dd5c9.
Staged actual graph replay at 2026-11-05T02:59:29.514934Z passes with scripted
models, legacy vendors mocked, Python sockets/requests/curl denied: 1219 history,
1134 visible, 17 evidence IDs in prompts, narrative 5587 chars, mixed 15653,
maximum prompt 23165 (limits 6000/28000). Staged file hash unchanged.

## Failed gate and draft changes

Focused runtime/reconciliation: 14 passed. Full offline: 1661 passed, 99 subtests
passed, ONE FAILED, four skipped, one integration deselected, 20 warnings, 63.57s.
Failure: tests/test_evidence_review.py::test_recorded_real_manifest_reproducible_offline,
ValueError: invalid split manifest.

The new CLI-only runtime path guard in event_intelligence.py changes its complete
file fingerprint, which freeze_manifest embeds as matcher_sha256. Independent
comparison finds ONLY matcher_sha256 and consequent manifest sha256 differ;
articles, labels, clustering and assignments do not differ. The event_context.py
fingerprint is unchanged. Frozen fixtures were NOT regenerated or relaxed.
This is an integration regression introduced by the draft, not an observed
database corruption. The guard is still uncommitted and the full suite is red.

Other uncommitted draft changes add an optional private installation authority
file, default graph selection, explicit rejection of alternate stores without a
legacy opt-in, and existing absolute-path guards on several older CLIs. The
authority file DOES NOT EXIST; none of these drafts establishes active authority.
Legacy private trial launchers have not yet been adapted. Do not treat draft
coverage as verified across every operational entry point.

## Stop state and next action

Final record 2026-11-05T03:02:06.726635Z /10:02:06 Asia/Saigon.
The intended local-runtime/information.sqlite3 still contains the older original
997 observations, 24 definitions, 38 coverage, zero gaps. The root original still
contains 222/116/125/0. Candidate and staged copy remain 1219/140/163/0.
No new eligible observations, first-seen metadata, live publisher status or
acquisition latency is claimed. No live session occurred. Longitudinal persistence
NOT PROVEN. Post-promotion restart/PIT/analyst replay and isolated rollback drill
NOT RUN. No production switch means no production rollback is needed.

Next: resolve the CLI/frozen matcher fingerprint coupling without rewriting
historical frozen evidence; rerun focused/full offline checks. Then revalidate
originals/backups/stage and all launch routes, establish switch-time writer
exclusion, and only then execute the already authorized guarded activation and
single eligible IPS/GV collection. Preserve the no-push/Checkpoint-C boundary.
After one successful session, a later independently invoked research session is
still necessary for longitudinal production persistence proof.

No new tool-reported Defender block; no Defender event audit, security-setting
change or claim that the earlier alert was a proven false positive.
