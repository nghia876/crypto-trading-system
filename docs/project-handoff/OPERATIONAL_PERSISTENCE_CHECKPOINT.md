# Resume update — activated, post-live graph gate blocked — 2026-11-05

The original pre-promotion stop below is historical. Frozen matcher restored;
full suite 1662 passed plus 99 subtests. Guarded activation completed, then ONE
live IPS/GV session added 35 rows (1254 total). Restart/PIT/recovery passed.
STOPPED at post-live graph assertion: none of the new evidence IDs reached
actual graph prompts. Phase 3 remains IN_PROGRESS; no further collection/push.
See [complete resume report](CANONICAL_ACTIVATION_RESUME_REPORT.md).

# Authorized activation attempt — guarded stop — 2026-11-05

STOPPED BEFORE PROMOTION. Fresh exact-union/integrity/PIT checks, both original
archives and staged scripted graph passed. Full offline suite: 1661 passed +99
subtests, one frozen-manifest reproducibility failure introduced by a draft CLI
edit changing the recorded whole-file matcher fingerprint. No activation,
collection, commit or push. Originals unchanged; draft code remains uncommitted.
See [current stop state and next action](CANONICAL_ACTIVATION_GUARDED_STOP.md).
Earlier approval boundaries below are historical; user has now authorized guarded
activation, but this attempt stopped on verification before any production switch.

# Disposable reconciliation evaluation update - 2026-11-04

Separately approved disposable evaluation PASS: exact union 1219 observations,
140 source-history rows, 163 coverage, zero gaps; no conflicting keys. Originals
and backups unchanged. All 85 revision links and 985 coverage evidence references
valid; 47 shared subjects retain all 141 copies. 75 PIT cutoffs and actual offline
graph/restart pass within 6k/28k. Full offline 1661 +99 subtests pass. No active
path, production migration, live collection or push. Phase 3 IN_PROGRESS;
authority activation and longitudinal production continuity NOT PROVEN.
See [evaluation and approval boundary](DISPOSABLE_RECONCILIATION_EVALUATION.md).
Original stop/proposal below is historical; only disposable evaluation executed.

# Focused operational persistence checkpoint - 2026-11-04

Phase 3 IN_PROGRESS. P1 investigation PASS; authority unresolved. P2 backups and
entry-point guards PASS, single-authority activation NOT PROVEN. P3 BLOCKED by
distinct legitimate evidence in BOTH stores. No migration or live collection ran.
User explicitly required stopping before consequential reconciliation. No push.

## Runtime trace and cause

`python main.py` copies DEFAULT_CONFIG; installed `tradingagents` enters cli.main,
whose normal graph also uses DEFAULT_CONFIG. Package import loads .env and
.env.enterprise from the working-directory ancestry without overriding exported
values. Previously neither default config nor env overlay selected an information
store. No automatic config.local.json loader exists. The private graph_trial.py
explicitly reads that file; normal launch does not. Thus there was no verified
global production authority, despite historical handoffs using "canonical".

The older local-runtime/live_trial.py explicitly initialized information.sqlite3
on October 29. Its operations/config identify a manual trial, not production
approval; macro and specialist acquisition subsequently appended real history.
PHASE_3_6_HANDOFF reports the earlier database absent and initialized
canonical-information.sqlite3 on November 1. Later specialist handoffs and
read-only diagnostics use that file. Both files now exist: this is divergent
operational history, not an empty legacy file or disposable test fixture. The
historical reason for the earlier absence is unknown.

Graph create_run_state previously opened the supplied path with the writable
constructor, permitting silent creation. Relative paths were interpreted against
the process working directory, not the repository or config-file directory.
Polling --store was required but could also create a missing file; adaptive CLI
required an existing file but still accepted CWD-dependent relative selection.
The backup bridge required an existing file but resolved relative paths from CWD.

## Read-only inspection

Private workspace root is the checkout's parent; exact host paths and metadata
are in the private persistence-audit-private.json, outside Git. Root-relative:

| File | Bytes | Observations | Source history | Coverage | Gaps |
| --- | ---: | ---: | ---: | ---: | ---: |
| canonical-information.sqlite3 | 1425408 | 222 | 116 | 125 | 0 |
| local-runtime/information.sqlite3 | 3780608 | 997 | 24 | 38 | 0 |

Both integrity_check results are ok. Same four-table schema: observations,
source_definitions, coverage, data_gaps. Different filesystem identities on the
same volume; not aliases. No shared observation IDs or exact rows in any table;
all 222/997 observation records are unique to their respective stores. Forty-seven
subjects overlap; do NOT discard repeat acquisitions as duplicate articles.
No observation-ID conflicts were found. Cross-table migration key/semantic
conflicts still require a dedicated preflight; migration has not been certified.

Canonical first-seen: November 1 04:41:44 through November 2 02:20:51 UTC.
Families: NASA recent/technology 20/20; NASS 36; UK energy/FCDO/food/health/trade/
water 12/12/24/24/12/12; USGS drought/earthquakes/river-flood 20/2/28.
Source history covers 14 IDs, including failed CDC/EIA acquisition.
Local-runtime first-seen: October 29 06:30:02 through October 30 09:56:16 UTC.
Families: BLS CPI/core CPI/payrolls/unemployment 32/32/33/32; H.4.1 five distinct
metrics one each; NY Fed ON RRP 100; BBC technology/world 20/27; EIA 42; NASS 288;
USGS drought/river-flood 16/370. Source history covers 13 IDs, including gated
TGA, BLS calendar and GDELT attempts. Publication ranges include stale historical
material: canonical 2012-09-28 through 2026-11-01; older store 2011-07-18 through
2026-10-29, with some publication times unknown. These are not current incidents.

Original SHA256, unchanged through backup and graph replay:

- canonical: 3e7548c55e59bf42e16a61c570122b98f5e056dcf2fa17c578d6c63a7595ec4b
- local-runtime: cbe813a934ae0b02a158299a5577fbced285fa16718a7940be137acf17ceb680

## Safe guards and recoverability

New shared opt-in TRADINGAGENTS_INFORMATION_STORE_PATH is read by default graph
configuration and polling/adaptive/backup bridge CLIs. Explicit caller/--store
selection takes precedence. Operational paths must be absolute existing files;
missing or relative selections fail rather than creating a competing database.
Graph opens its evidence store read-only. No environment/config value was activated
and neither file was selected. Intentional low-level SQLiteInformationStore creation
remains available for tests/bootstrap; this is not an OS-level write prohibition
or universal interception of every legacy utility. Old relative command examples
must be replaced by an approved absolute path before operational use.

SQLite connection.backup from read-only sources created private backups under
local-runtime/backups/persistence-20261104T041709Z (outside Git). This captures
SQLite's consistent snapshot including committed WAL state, not naive file copying.
Backups reopened, passed integrity, and matched every source table row exactly.
Backup hashes differ from originals because SQLite backup can change physical
layout; logical equality was checked explicitly:

- canonical.sqlite3: e398695e7cef892ff1d551d4d2fabb477b6a32a7bf9c4414deca6c74614fb8f8
- local-runtime.sqlite3: d9be1337557a30efae1a950084555840c419a5273ec287d0bb7723de7ce9c4cb

No rollback needed: originals were never changed. For future recovery stop every
writer, preserve failed DB plus WAL/SHM and manifests, recheck the selected backup
hash/integrity, restore to a NEW private recovery path using SQLite backup, compare
all rows and replay before explicitly switching configuration. Never overwrite an
original or delete its sidecars as an automatic rollback. Local backups are not an
off-device disaster-recovery guarantee.

## Verification and limits

November 4, 2026: full offline 1651 passed +99 subtests, four expected skips, one
integration deselected, 20 existing model warnings, 68.90 seconds. Initial full run
found an undefined name in the new test; corrected and reran full suite. Earlier
focused store/bridge/graph tests: 50 passed. Changed Python files lint and diff checks
pass. No new dependencies, installations, security-policy changes or live services.

Separate read-only actual graph replays at 04:19:49 UTC, scripted models and mocked
legacy vendors with socket access denied: canonical view 165 current/222 historical
records, 7 evidence IDs captured, narrative 5587 characters, mixed context 13018,
largest individual prompt 20530. Older view 969/997, 15 evidence IDs, narrative 5250,
mixed 15282, largest prompt 22794. Pre-first-seen cutoffs excluded all observations.
Legacy settlement reported unavailable mocked Yahoo prices; this was not a live
model run, full-system PIT certification, or acquisition/restart longitudinal proof.
Original source counts/hashes stayed unchanged. No new session IDs, acquired items,
freshness/dedup measurements or live failures exist for this checkpoint.

Starting HEAD 6df2224a3ba8fb5fcfde32f172bb3dd35a38fc9a, correct feature branch;
tracked tree initially clean, existing .phase12-tools/ and diagnosis preserved.
Fresh read-only remote verification returned c54af8c18e4418f4d34032b422d1c2bf02cc0082
after network permission (initial DNS failure). New work LOCAL ONLY; no push,
main change, merge/rebase, source-mirror edits or Defender setting changes.
No tool-reported security alert; no Defender audit or proven false positive.

## Concrete reconciliation proposal - NOT EXECUTED

After separate approval, preserve both snapshots and build a disposable private
reconciliation candidate from a verified backup of local-runtime/information.sqlite3,
which contains unique macro/BBC/EIA history. Append all immutable rows from the newer
store under a transaction with exact-key equality checks; halt on unequal same-key
records. Preserve all IDs, timestamps, source-definition versions, coverage/failures,
revision links and a separate import manifest identifying source hashes. Do not
collapse the 47 shared subjects or backdate new discoveries. Validate the complete
1219-record observation union, all source/coverage history, revision/PIT behavior,
first-seen queries and graph budgets. Candidate is validation-only, not an authority.
Only after review promote explicitly to one approved existing path, retain both
originals as immutable archives, and activate the shared absolute configuration.
Then perform one backed-up IPS/GV session and same-store restart/analyst replay;
collect a later genuinely separate session before claiming longitudinal proof.
WORLD remains independent of BTC/price; broad C1/C2, rights expansion, scheduler,
cloud, trading and GitHub push remain outside this checkpoint.
