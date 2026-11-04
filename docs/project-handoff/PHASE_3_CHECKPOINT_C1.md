# Focused operational persistence checkpoint - 2026-11-04

P1 investigation PASS: both stores contain distinct real history (222/997
observations). P2 private SQLite backups and entry-point guards PASS; single
authority activation NOT PROVEN. P3 BLOCKED pending separately approved
nondestructive reconciliation. Both original databases unchanged; no live
collection or push. Full offline 1651 passed +99 subtests; Phase 3 IN_PROGRESS.
Historical B2 sessions do not establish production-store continuity. Broad
Checkpoint C was not advanced. This supersedes filename-based authority claims.
See [findings and concrete proposal](OPERATIONAL_PERSISTENCE_CHECKPOINT.md).

# B2 bounded closeout and first C1 slice — November 4, 2026

Phase 3 IN_PROGRESS; exit NO-GO. Current explicit user authorization permits
Checkpoint C acquisition work while carrying unresolved B2 quality gaps.

## Status and scope

B2 three independent user-requested acquisition sessions are demonstrated for the
two-publisher IPS/Global Voices pilot. Bounded acquisition pilot CLOSED with
limitations; broader B2 NOT PROVEN. Rights-cleared informative context,
independently corroborated shared incidents, general automated search and global
coverage remain unmet. Historical no-C instructions are superseded by this user's
current authorization, not by an invented quality pass.

The new `research_session` bridge requires an existing SQLite store, explicit
manual write opt-in and a new private backup path. Under the existing collector
lock: check source integrity, exclusively create a SQLite online backup, check
backup integrity, invoke existing rights/cadence/health-aware research, check final
integrity. No competing operational DB or scheduler. All writers must honor the
lock. Failure preserves partial append history and backup for inspection; no
automatic destructive rollback. Restore only after stopping all writers and
verifying backup integrity; preserve failed files first. Backups are private and
must remain outside Git, protected like the original.

```text
python -m tradingagents.information.research_session --store EXISTING_CANONICAL_PATH --backup NEW_PRIVATE_BACKUP_PATH --run-id UNIQUE_SESSION_ID --allow-canonical-write
```

Production persistence NOT PROVEN. Recent handoffs use canonical-information.sqlite3;
the older local-runtime config still points to local-runtime/information.sqlite3.
Both exist. Neither private store nor configuration was changed. Reconcile the
active launcher path before a genuine live write. Validation used isolated synthetic
databases, not a second production store or invented independent live sessions.

C1 PARTIAL: cutoff-eligible immutable history supplies unique article first-known
counts for last/prior 24h and change to the existing actual Market Analyst narrative
renderer. Publisher identities and acquisition channels remain separate structured
fields. Repeat polls, revisions and cross-feed copies of one canonical URL never
create new article counts. Retained versions are counted separately. Availability
is conservative, never backdated publisher time. Origin/syndication/reach UNKNOWN;
no inferred lineage, credibility or corroboration. Rumor/claim state unchanged.
Zero sampled articles is not zero real activity. This is corpus article attention,
not incident propagation or acceleration. Incident-bound windows, observed lineage
and live multi-session canonical evidence remain deferred.

C2 DEFERRED: no depth/executed-trade implementation or new venue eligibility/live
audit. C03 unchanged. No whale intent, alpha, causal inference, automated trades,
Phase 4 or Phase 5 work. WORLD intake remains independent of BTC price/anomalies.

## Evidence

- Focused 37 passed: B2/adaptive/bridge; historical actual metadata replay through
  actual graph with offline scripted model, <=6k narrative / <=28k individual prompts.
- Full offline: 1,647 passed +99 subtests, four expected skips, one integration
  deselected, 20 existing warnings, 61.09s. New-file lint and diff checks passed.
- Isolated synthetic daily appends/reopen preserve first-seen, PIT and unique counts
  across polls; distinct run journals, backup/recovery-copy state and integrity
  checked. Existing backup and missing database refused. Not live session evidence.
- Both private stores read-only integrity ok and hashes unchanged during checks.
  Recent canonical SHA256 3e7548c55e59bf42e16a61c570122b98f5e056dcf2fa17c578d6c63a7595ec4b;
  older store cbe813a934ae0b02a158299a5577fbced285fa16718a7940be137acf17ceb680.
- No new live collection, private writes, dependencies, paid/cloud APIs, rights
  expansion or security changes. No tool-reported new alert; no Defender audit.

## Backup and preservation

Start HEAD c54af8c18e4418f4d34032b422d1c2bf02cc0082 on expected feature branch,
clean tracked tree; existing untracked .phase12-tools/ and diagnosis preserved.
Fresh network-enabled remote: a619fe40e67606c92277eb886bd8b5c4aa03b93e,
an ancestor of the approved target. Seven pending commits /42 final changed paths.
Bounded scan reviewed all 67 changed blobs for private paths and credential patterns;
only an inspected negative-test fake credential URL needed allowlisting. No claim
that this detects every possible secret. Synced sources remain read-only.

NO PUSH ATTEMPTED: SECURE_EXECUTION forbids repeating the known failed Work Git/MSYS
credential-helper method. Parent-workspace Push-B2-Exact-Approved.ps1 is reviewed
for ordinary non-elevated host PowerShell, with no security changes. It pins exact
remote and seven-commit history, checks branch/URLs/ancestry/tracked state, pushes
only c54af8c via normal explicit non-force refspec and verifies remote equality.
New local commits are excluded even with newer HEAD. Older backup script targets
another SHA and must not be used for this authorization.

Next bounded action: reconcile canonical launcher path, perform one genuine opted-in
backed-up manual session and same-store graph replay, then extend incident-bound C1.
Retain broader B2 quality gaps and separate C2 eligibility/live-acquisition gate.
The historical readiness JSON and coverage inventory were not regenerated.
