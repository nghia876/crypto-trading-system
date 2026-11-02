# Phase 3.8 operational freshness and real review — 2026-11-02

Phase 3 remains IN_PROGRESS. Implementation local only. Start HEAD:
`a619fe40e67606c92277eb886bd8b5c4aa03b93e`; tracked tree clean, existing
untracked `.phase12-tools/` preserved. No main branch exists locally; none created.
Canonical `sources/` read only. One canonical database remains at
`../canonical-information.sqlite3`, outside Git.

## Controlled backup boundary

Fresh read-only remote check returned `bcb700fdd06385c90fa7399e4fe9525a87c67d62`.
Authorized range contains exactly:

1. `5d76ff1055da7aef6890a31dfec65b06a4e07cf5` — Phase 3.6.
2. `a619fe40e67606c92277eb886bd8b5c4aa03b93e` — Phase 3.7.

Fast-forward ancestry and diff whitespace verified. All 33 changed commit blobs
scanned for protected/private paths, SQLite files/magic, private keys, credential
URLs and common token patterns: no findings. Path/code review found no private
data artifacts; public source metadata and local-path documentation are intentional.
Pattern scanning cannot prove absence of every possible secret.

**No push attempted or claimed.** No safe host-execution tool is exposed; the
computer-use skill explicitly forbids terminal automation. The failing Work/MSYS
credential-helper method was not repeated. Parent workspace contains inspected
`Push-Phase38-Approved-Backup.ps1`, pinned to the two commits above. It checks
ordinary non-elevated execution, branch, clean tracked tree, exact origin URLs,
target ancestry, exact commit list, expected remote base/target and post-push SHA.
The explicit SHA refspec excludes all new Phase 3.8 history even after local HEAD
advances. No force/tags/submodule push, merge, rebase or main mutation.

In **ordinary Windows PowerShell**, run:

```powershell
& 'C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\Push-Phase38-Approved-Backup.ps1'
```

Expected final verification is remote feature SHA `a619fe40e67606c92277eb886bd8b5c4aa03b93e`.
If policy, credential access or Defender blocks, stop and retain the exact error;
do not elevate, retry a security block, change Defender or bypass policy. A later
local Phase 3.8 commit is expressly outside this push authorization.

## Delivered and integrated

- `source_health` recomputes current/as-of status directly from the full canonical
  append-only polling journal and PIT observations. Counts persist across restart,
  including more than the coordinator's 12-attempt checkpoint window.
- Separate responding/empty/failed/never-polled transport and publication freshness,
  update freshness, errors, timeouts, HTTP 429, last attempt/success, publication to
  first-seen/retrieval lag and repeated-copy retrieval lag. Ages refresh without
  polling. Source updates never become original publication or event occurrence.
- Closed/open collection-unknown intervals disclose missing observation. They do
  not diagnose PC downtime: budget, backoff and absent invocations can also cause
  gaps. Successful stale/empty feeds can be quiet, not necessarily broken. Rolling
  feeds do not prove event absence or recover missed items. No uptime/recall claim.
- Poll journal now records request start/completion wall duration; older durations
  remain unknown. Naive start clocks are refused before access; within-request
  backward clock movement prevents commit. Wall durations cannot distinguish clock
  jumps from network delay. Arbitrary cross-run host clock correctness is unverified.
- Policy denials/unverified robots/crawl-delay deferrals have distinct safe error
  classes for future attempts. Existing failure history is not rewritten.
- Read-only CLI plus existing `polling health` and `world_radar` output include the
  report. Source/config fingerprints, publisher group and rights references remain
  explicit. Config histories are scoped to exact fingerprints, not silently joined.
- Three rights-reviewed official UK food/water/energy metadata feeds use the same
  collectors, SourceRegistry definitions, coordinator, Observation and SQLite/PIT
  store. Legacy broad configuration stays intact for compatibility; operational
  CLIs select the reviewed subset explicitly. No BTC/price/market gating, paid API,
  database/service or installed scheduler. Repeated acquisition copies preserve
  provenance; source/URL metrics collapse duplicate articles and poll IDs are durable.
- Neutral reproducible review forms bind the original five article versions for
  three proposals, actual source links, agent URL checks, occurrence/location
  uncertainties, identity/time fields and three explicit judgment choices.
  **All UNREVIEWED, human reviews zero**, labels unknown/pending. No imports,
  incident promotion, matcher tuning, score or new evaluated holdout.

See [human review guide](PHASE_3_8_REVIEW_GUIDE.md) and
[version-bound packet](PHASE_3_8_REVIEW_PACKET.json).

## Actual bounded source observations

Four finite jobs Nov 2 **02:17:44–02:20:51 UTC / 09:17:44–09:20:51 Asia/Saigon**:
11 attempts, 10 successful metadata responses and one EIA robots refusal. No tight
retry. GOV.UK one-feed/host/job and 30-second cooldown remain enforced; other feeds
rotate across invocations. First DEFRA attempt used inherited Nov 1 review metadata;
corrected explicit Nov 2 review date creates a new fingerprint for the second
attempt. Both attempts remain archived, never erased or counted as two origins.

Archived **89 unique acquired source/URL records** (including previously known
articles), not 89 new incidents. Three new feeds add 36 retained URLs. Cumulative
canonical source/URL count 146; 89 publication/update dates within seven days,
eight topic families, three publisher groups. Four URLs within 24h: NASA notice,
FCDO advice update, two Environment Agency updates. This is not four new incidents.
Old FCDO/trade/health collection is unobserved since Nov 1; content freshness does
not hide that collection gap. All UK departments share one publisher group.

| Feed | Actual result | Limit |
|---|---|---|
| DEFRA food/agriculture | 12 retained, 8 omitted; newest update Nov 1 00:01Z | Government administrative/news stream, no food-shock recall claim |
| Environment Agency water | 12 retained, 8 omitted; newest update Nov 1 16:05:03Z | Water/environment announcements, not global water scarcity measurements |
| DESNZ energy | 12 retained, 8 omitted; newest update Oct 30 17:05:01Z | Policy/agency stream, no physical grid-outage telemetry |
| USGS drought/flood | Successful; latest publication Aug 12 / Oct 23 | Stale current incident coverage |
| NASS | Successful; latest publication Sep 24 2025 | Stale |
| NASA | Successful; recent feed newest Nov 1 04:05Z; technology Oct 22 | Routine/science notices; specialist AI/cyber gap remains |
| EIA | Robots refused RSS; no feed request | Still gated |
| Cyber candidates | CISA policy HTTP 403 in web research; NCSC Atom not inspectable in research surface | No new clearance, feed acquisition or cyber coverage claimed |
| Health/geopolitics | Existing UKHSA/FCDO metadata preserved | Independent incident corroboration still UNKNOWN; CDC rights unresolved |

[GOV.UK reuse](https://www.gov.uk/help/reuse-govuk-content) and
[OGL v3](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
checked directly Nov 2 02:17:17 UTC, HTTP 200, policy hashes archived. OGL permits
copy/adapt/commercial processing with attribution and exceptions. Exact new Atom
paths use the same published government reuse basis; robots allowed each before
acquisition. Scope: agency headline/link/date only, no bodies/images/logos/personal
datasets/third-party works. Contains public sector information licensed under the
Open Government Licence v3.0. No AI-specific grant or training permission invented.
Independent incident origins, non-English/regional recall and source bias remain
unverified. Metadata freshness alone cannot satisfy the WORLD exit criteria.

Operational evidence and policy/robots hashes:
`tests/fixtures/phase38/operational_results.json`; normalized metadata:
`tests/fixtures/phase38/real_specimens.json`. Replays are temporary offline test
stores, never production backfills or the full original XML. Source body checks
were research-surface cached representations, separate from live feed checks.

## Operation and optional scheduling

From repo-checkout, the read-only reproducible report:

```powershell
& ../phase3-final-env/Scripts/python.exe -m tradingagents.information.source_health --store ../canonical-information.sqlite3 --as-of 2026-11-02T02:20:51.098082+00:00
```

Omit `--as-of` for current age/gaps without any network requests. To deliberately
run one bounded job using exact reviewed configurations and existing locking:

```powershell
& ../phase3-final-env/Scripts/python.exe -m tradingagents.information.polling poll-once --store ../canonical-information.sqlite3 --interval 900 --max-sources 6
```

Optional user-controlled Windows Task Scheduler configuration: existing reviewed
`phase3-final-env\Scripts\python.exe` as program, absolute repo-checkout as start
directory, arguments above with the absolute canonical SQLite path. Run as the
ordinary user, only while logged on, every 15 minutes, never highest privileges;
do not overlap running instances or catch up missed triggers. Choose and inspect
local output/error logging. **No task installed.** Multiple GOV.UK feeds rotate
one per job, so per-feed cadence exceeds 15 minutes. Unknown gaps disclose that
budget/backoff/offline time; no 15-minute incident latency guarantee.

## Verification and remaining gates

Validation results are recorded in PHASE_3_8_STATUS.md after final checks.
Tests use deterministic mock transports and real archived metadata with offline
BTC/BLS/H.4.1/RRP fixtures/test model. Operational feed checks above are the only
new live acquisition claim; no live market/macro or human evaluation performed.

Remaining: sustained timely geographically/language-diverse original coverage,
independent incident origins/corroboration, useful incident yield and measured
unattended cadence; physical grid, food/water monitoring and specialist cyber/AI;
independent human article/pair adjudication, chronology/occurrence resolution,
authentic positives/hard negatives and untouched incident-cluster holdout before
real precision/recall claims. Macro gates unchanged: daily Treasury TGA and yields
rights-gated, BEA GDP/PCE incomplete, BLS live calendar unavailable, FRED off.

Secure execution: direct patches and small auditable commands, existing reviewed
dependencies, no install/security-policy/Defender changes or bypass. No new alert
surfaced through tools; no Defender log audit. Prior FileFix cause remains unknown,
not an established false positive. Synced sources and `.phase12-tools/` preserved.
