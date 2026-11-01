# Phase 3.5 reviewed occurrence context - 2026-11-01

Status: bounded offline implementation VERIFIED; independent real-world quality
UNVERIFIED; Phase 3 remains IN_PROGRESS. LOCAL ONLY, no push of this work.

## Security and synchronization

Read and follow [secure Windows execution](SECURE_EXECUTION.md). User-reported
Defender detection `Ransom:PowerShell/FileFix.DZ!MTB`, Removed, followed by a
reported clean FULL scan does not establish a false positive or machine safety.
No new security block/alert surfaced in this session's tools; no Defender log
audit performed. Used direct patches, reviewed small literal commands and
existing dependencies. No installer, security-setting change or bypass.

Existing nghia876/crypto-trading-system checkout, branch
phase-3-event-narrative-slice, starting HEAD
8b74679b3f1ba638187b795935fb84ae100772ab. Starting tracked tree clean; existing
untracked .phase12-tools/ preserved. Canonical parent sources/ references read
only. No main, force, merge or rewrite operation. Remote GitHub read required
network permission after initial DNS failure, then returned
f87ddbefd0126f05b0ad29b53d5065ea9796fddc. No push attempted in this session.

Reviewed parent Push-Phase33-Authorized.ps1: checks exact origin URLs, branch,
tracked cleanliness, ancestry, exact e801a80 + 8717005 range, whitespace, pinned
remote base; pushes an exact SHA refspec with tags/mirror disabled and verifies
the result. Reviewed range inventory and code, no database/credentials/untracked
files included; private-key/token pattern scan returned no matching files in
the scoped information/test/handoff content. Pattern scans are not proof of
absence. Guarded target remains 8717005bc505bfd66c3206c40a49140193291890;
Phase 3.4 and every newer commit excluded. Ordinary non-elevated host Windows
PowerShell is inaccessible to this execution surface. User host action:

```powershell
& 'C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\Push-Phase33-Authorized.ps1'
```

The script verifies remote equals the authorized target after success. Do not
retry the known broken Work Git/MSYS helper. Backup remains pending, not a local
development blocker. No new push authorization is implied.

## Implementation and contract

`event_context.record_event_context(store, evidence_id=..., recorded_at=...,
reviewer=..., provenance=..., rationale=..., episode_key=None,
location_key=None, occurrence_start=None, occurrence_end=None, supersedes=None)`
appends a review of one immutable narrative observation to the SAME canonical
SQLite store. Actual review acquisition time governs PIT availability; occurrence
bounds are separate and timezone-aware. Corrections explicitly supersede the
active review; all-null correction withdraws context. The envelope's event_time
stays the evidence event_time to honor the existing store revision contract.
Revised articles do not inherit context. No schema migration or extra live store.

Caller supplies canonical globally namespaced episode keys and location keys at
one documented granularity. Distinct keys must denote distinct places/episodes,
not aliases or parent/child administrative units. Occurrence windows describe
the episode, not publication/reporting duration. The API is caller-curated;
reviewer strings are provenance, not authenticated proof of human review.

Candidate v2 first applies unchanged v1 eligibility, then vetoes conflicting
episode/location keys or strictly disjoint occurrence windows. Touching windows
do not conflict. Missing/one-sided context preserves behavior; agreement never
creates candidates, membership, truth, support or independent corroboration.
Results expose context review IDs, total veto count and bounded veto reasons.
Persisted historical snapshots retain original policies. use_reviewed_context=False
selects the frozen v1 comparison. Reviewed time is not yet promoted to incident
state or used to close evidence-gap requirements. No analyst/network flow added.

## Evaluation and verification

Original v1 fixture is unchanged: 80 synthetic pairs, TP30/FP15/TN25/FN10,
66.67% precision, 75% recall; regression still passes with missing context.

New frozen 24-pair synthetic contract holdout: four new family templates,
eight positives and sixteen negatives. Frozen before first execution, no logic
or threshold tuning after outcomes. Exact fixture hash and every outcome are
in PHASE_3_5_METRICS.json; reproduce with `python -m tests.test_event_context`.
Labels enter scoring only after matching; per-article metadata is explicit test
input, not extracted from pair labels by production code.

| Same 24 trials | TP | FP | TN | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| v1 | 8 | 16 | 0 | 0 | 33.33% | 100% |
| v2 | 8 | 4 | 12 | 0 | 66.67% | 100% |

Each of flood/drought/grid/cyber yields 2TP/4FP/0TN/0FN before and
2TP/1FP/3TN/0FN after. Four unknown-metadata negatives still link. Tiny correlated
synthetic templates, authored with knowledge of the guard, are not independent
quality evidence or comparable to the 80-pair baseline's distribution. No human
review, confidence interval, real-world accuracy or source-independence claim.
An independent held-out corpus was not available; see the explicit
[cluster split, separate review and label-freeze protocol](EVENT_CONTEXT_HOLDOUT_PROTOCOL.md).

Focused candidate/evaluation/context/incident/actual-graph run: 70 passed before
the last one-sided/non-promotion acceptance test. Full final offline suite:
**1,554 passed + 99 subtests**, four skipped, one integration test deselected,
20 existing model warnings, 49.48 seconds. Parent phase35-regression.txt retains
output. Existing mixed BTC/H.4.1/RRP/BLS/broad WORLD actual graph remains under
28,000 characters; PIT, late reviews, correction, withdrawal and reopen checks
pass. Full tracked Python Ruff, changed-file syntax and diff checks pass.
After the full run, made the fixture hash newline-independent for Windows Git
checkouts; all ten context tests and changed-file Ruff passed again (2.92 seconds).
An initial overbroad Ruff invocation scanned untracked .phase12-tools and
reported third-party lint errors; read-only, no fixes applied there. Corrected
scope includes tracked project Python plus new files. An initial acceptance
failure exposed the store's fixed event_time revision requirement; corrected
the review envelope and reran focused/full suites successfully.

## Limits and next action

Erroneous review keys or overly narrow occurrence windows can veto true matches;
recall preservation is measured only on these stipulated cases. Missing metadata,
lexical paraphrase misses, location aliases/granularity and authentic review
coverage remain open. No live canonical database was found/audited or created.
Fixtures use temporary canonical-schema stores only; reports stay outside them.

Keep broad WORLD discovery: war, disasters, drought/water, agriculture,
energy/infrastructure, health, geopolitics and technology/cyber, without BTC or
price-movement gates. No source/feed/paid dependency added. Original coverage
gaps remain. Daily TGA/yields rights gates, incomplete BEA GDP/PCE, unavailable
BLS live calendar and disabled FRED remain deferred.

Next: acquire eligible original evidence into the existing canonical store,
review per-article context independently from pair labels, freeze incident/origin
clusters and score an untouched holdout at early/late cutoffs before tuning.
