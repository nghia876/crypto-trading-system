# Disposable reconciliation evaluation — 2026-11-04

Phase 3 IN_PROGRESS. Evaluation candidate PASS. Production activation NOT
AUTHORIZED; longitudinal continuity NOT PROVEN. No original database, backup,
active configuration or source mirror changed. No production migration, live
collection, Checkpoint C expansion or GitHub push.

## Method and immutable inputs

Read workspace v1.1 revised blueprint/master prompt/resource manifest, persistence
handoff, coverage matrix, SECURE_EXECUTION, actual SQL/model/storage/replay APIs.
Branch phase-3-event-narrative-slice; starting local HEAD
6dbf952ff5ed8491d8fc6749fb7a7f932917668c. Tracked tree initially clean; existing
.phase12-tools/ and bottleneck diagnosis preserved. Prior verified remote
c54af8c18e4418f4d34032b422d1c2bf02cc0082 was not freshly queried.

Both originals opened SQLite URI mode=ro; connection.backup created new consistent
private snapshots. Candidate was backed up from the older snapshot; exact newer
rows inserted deterministically in one transaction, with explicit key-equality
checks and semantic validation. Normal append() can deduplicate numeric rows and
synthesize revision links, so was deliberately bypassed. No INSERT OR REPLACE/
IGNORE, re-timestamping, ID rewriting, invented cross-store links or silent loss.

Private evaluation folder, relative to workspace parent of checkout:
local-runtime/DISPOSABLE-reconciliation-evaluation-20261104T043042Z/.
Candidate DISPOSABLE-NOT-OPERATIONAL.sqlite3, SHA256:
1df6303bc5de63687edc6081a4c6282f5dc358740e6c4e79b75386e353d7dceb.
Only isolated evaluation calls select it. No active configuration references it.
Private manifests, snapshots, per-source counts, all overlap details, row digests,
provenance and graph results are retained beside it, outside Git.

| Table | Newer before/after | Older before/after | Candidate | Shared/conflicting PKs |
| --- | ---: | ---: | ---: | ---: |
| observations | 222 / 222 | 997 / 997 | 1219 | 0 / 0 |
| source_definitions | 116 / 116 | 24 / 24 | 140 | 0 / 0 |
| coverage | 125 / 125 | 38 / 38 | 163 | 0 / 0 |
| data_gaps | 0 / 0 | 0 / 0 | 0 | 0 / 0 |

All source rows match exact SQLite values in the candidate, including timestamp
text and JSON serialization. Distinct filesystem identities, identical schemas
and indexes. Primary keys: observation_id; coverage_id; source_id/version/observed_at;
six-column gap tuple. Secondary event/poll indexes are nonunique. SQL declares no
foreign keys: foreign_key_check alone cannot establish application references.

Original SHA256 before = after:

- canonical-information.sqlite3:
  3e7548c55e59bf42e16a61c570122b98f5e056dcf2fa17c578d6c63a7595ec4b
- local-runtime/information.sqlite3:
  cbe813a934ae0b02a158299a5577fbced285fa16718a7940be137acf17ceb680

Existing backups in local-runtime/backups/persistence-20261104T041709Z reopened,
integrity ok, identical source schema/every row, unchanged hashes:

- canonical.sqlite3:
  e398695e7cef892ff1d551d4d2fabb477b6a32a7bf9c4414deca6c74614fb8f8
- local-runtime.sqlite3:
  d9be1337557a30efae1a950084555840c419a5273ec287d0bb7723de7ce9c4cb

All 85 supersession links (57 newer/28 older) resolve to same source/subject/
metric/event-time, with valid availability ordering and no cycle/fork. All 985
coverage evidence references resolve with matching source and retrieval no later
than coverage time. All observation/coverage source IDs resolve; 23 source IDs,
including failed/gated sources. No conflicting source-version definitions or
acquisition fingerprints. Actual rows contain narrative/macro observations, no
derived claim/incident assertions. No separate batch/version/correction tables:
batch lineage is immutable payload/config/snapshot/retrieval and coverage history.

## Overlap interpretation

47 shared article subjects contain 141 observations, all retained. Each subject
has one identical content-version ID across its copies: no changed headline/date
content revision or content-version collision detected. Existing local revision
links preserved; no cross-store link synthesized. Across the entire union, 87
repeated semantic-key groups contain 219 rows. 985 narrative observations contain
828 distinct content versions. All 985 URL-derived article IDs, content hashes,
retrieval/config-derived observation IDs and transformation fingerprints verified.

Shared-subject changed fields are acquisition/context metadata: intake and
excluded counts (24 subjects each), config fingerprint (8), domain (2), snapshot
hash (2). First-seen API returns the original minimum for all shared subjects.
These are repeated article-version acquisitions, not independent corroboration.
Article identity does not establish incident identity across different articles.
No automatic incident merge, origin/independence assertion or confirmation added.
Current projections hide only existing explicit supersessions; history keeps all.

## Gates and tests

| Gate | Result |
| --- | --- |
| SQLite integrity, schema, exact row union | PASS |
| Application references, revision lineage, fingerprints | PASS |
| Existing backups, consistent snapshots, original immutability | PASS |
| PIT and first-seen preservation | PASS — 75 cutoffs |
| Actual graph, denied network, scripted model | PASS — before/between/after |
| Fresh-process restart | PASS — identical final context hash |
| Collision/lineage rejection and exact-row transaction rollback | PASS |
| Existing provenance/rights safeguards preserved | PASS with limits below |
| Authority activation / live longitudinal production persistence | NOT AUTHORIZED / NOT PROVEN |

PIT compares current/history IDs and coverage with both inputs and independent
availability/supersession sets; latest eligible source-version views also match.
Cutoffs cover before/during/between/after Oct29–30 and Nov1–2, and immediately
before/at every recorded availability boundary. No future IDs in graph prompts.

| Graph cutoff UTC | Current/history | Narrative chars | Context chars | Largest prompt chars |
| --- | ---: | ---: | ---: | ---: |
| Oct28 00:00 | 0 / 0 | 898 | 5366 | 12967 |
| Oct31 12:00 | 969 / 997 | 5255 | 15280 | 22881 |
| Nov4 00:00 | 1134 / 1219 | 5590 | 15649 | 23154 |

All narrative <=6000 and context/individual prompts <=28000 characters. Final
prompts contain 17 current evidence IDs, not the entire corpus. Actual
TradingAgentsGraph.propagate runs with scripted models, mocked legacy vendors,
and denied Python sockets/requests/curl. Fresh-process context SHA256 matches:
ea65fe59a402c2325a9295ffbb75c72cafbf8882bc33084b7d3d3e428bfa2a6d.
Legacy settlement has unavailable mocked current prices. This verifies evidence
replay/wiring, not useful reasoning, live model quality or full-system PIT.

Ten focused tests pass (2.04s): unequal observation/source/coverage keys,
conflicting same-source-version definitions at different times, dangling/wrong-
subject lineage, cycle, fork, conflicting content version. Rejected transactions
restore exact baseline rows; identical shared keys counted, repeat union
idempotent, successful reopen and output overwrite refusal; input hashes stable.
Initial focused run found two fixture/exception-class issues, corrected before
passing focused/full runs. Full offline: 1661 passed +99 subtests, four expected
skips, one integration deselected, 20 existing warnings, 65.14s. Build/PIT 10.975s;
three graph cutoffs 26.493s; fresh-process graph 23.541s. Changed Python lint,
syntax and diff checks pass. No dependency/security-setting changes.

## Rights, limits and next approval

All 985 narrative rows are headline/date/link metadata, no summary/body evidence
text. BBC world/technology 27/20 and EIA 42 historical rows do not authorize future
collection. BBC fails reviewed PolicySession allowlisting. EIA remains in legacy
registry/allowlist; historical RSS robots restriction remains recorded. Mocked
Disallow /rss/ proves fail-closed before feed request; current live robots/terms
deliberately not fetched. Summary rights still need all four explicit permissions;
existing offline rights tests pass. This is preservation, not new legal clearance
or universal enforcement on every low-level caller-supplied session.

No unresolved data collision in these snapshots. Historical reason older store
was reported absent remains unknown. Backups are local, not off-device disaster
recovery. Live multi-session continuity, B2/C1/C2 and Phase 3 exit remain open.
No tool-reported Defender alert; no Defender audit/false-positive claim.

Separate approval must name a permanent absolute authority path and authorize a
backed-up migration/activation procedure, retaining both originals as immutable
archives and rechecking hashes/replay before switching configuration. Target and
rollback copy must be concrete before execution. This disposable evaluation is
not that approval. Subsequent bounded eligible IPS/Global Voices collection and
same-store restart/replay also need explicit authorization; a later independent
session is needed for longitudinal proof. GitHub push needs separate approval.

## Per-source exact reconciliation

Every source row from each input was matched exactly, not only counted.

| Source ID | Observations | Source history | Coverage |
| --- | ---: | ---: | ---: |
| macro.original.bls | 129 | 1 | 4 |
| macro.original.h41 | 5 | 2 | 10 |
| macro.original.on_rrp | 100 | 1 | 1 |
| macro.original.tga | 0 | 1 | 1 |
| macro.us.bls.release_calendar.2026 | 0 | 1 | 1 |
| news.bbc.technology | 20 | 2 | 3 |
| news.bbc.world | 27 | 2 | 3 |
| news.cdc.newsroom | 0 | 2 | 2 |
| news.eia.today | 42 | 13 | 14 |
| news.gdelt.geopolitics | 0 | 1 | 1 |
| news.gdelt.technology | 0 | 1 | 2 |
| news.nasa.recent | 20 | 7 | 9 |
| news.nasa.technology | 20 | 11 | 11 |
| news.nass.news | 324 | 16 | 16 |
| news.uk.energy | 12 | 4 | 5 |
| news.uk.fcdo | 12 | 8 | 9 |
| news.uk.food | 24 | 6 | 6 |
| news.uk.health | 24 | 10 | 10 |
| news.uk.trade | 12 | 8 | 9 |
| news.uk.water | 12 | 4 | 5 |
| news.usgs.drought | 36 | 14 | 15 |
| news.usgs.earthquakes | 2 | 10 | 10 |
| news.usgs.river_flood | 398 | 15 | 16 |
