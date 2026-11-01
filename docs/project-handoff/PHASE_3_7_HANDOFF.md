# Phase 3.7 — Operational WORLD Evidence Coverage — 2026-11-01

**Implemented and validated locally; Phase 3 remains IN_PROGRESS. No push.**
Existing `nghia876/crypto-trading-system`, branch `phase-3-event-narrative-slice`.
Verified starting local HEAD `5d76ff1055da7aef6890a31dfec65b06a4e07cf5`, clean
tracked tree, existing untracked `.phase12-tools/`. Read-only remote check with
credential helper disabled returned `bcb700fdd06385c90fa7399e4fe9525a87c67d62`;
one pending local Phase 3.6 commit at start. No push gate, push attempt, credential
helper invocation, main change, rebase, force or second codebase/database.
Canonical parent `sources/` read only; `.phase12-tools/` preserved.

## Functioning bounded radar

- New `python -m tradingagents.information.world_radar --store CANONICAL
  --report NEW_REPORT.json` drives the existing news collectors, SourceRegistry
  definitions, polling coordinator, Observation contracts and SQLite/PIT store.
  The exact canonical path here remains `../canonical-information.sqlite3`.
- Original NASA recent/technology, USGS global significant-earthquake Atom, and
  UK FCDO/trade/health Atom augment existing USGS/EIA/NASS configurations. BBC and
  GDELT remain compatibility/offline configurations but are withheld from the
  operational CLIs because expanded reuse is unresolved. No BTC keyword, market
  movement, price gate or paid API. No article crawling or separate event store.
- Both operational polling CLIs use exact reviewed configs and a bounded robots
  policy session. Denied/unverifiable robots, redirects and nonzero crawl-delay
  requirements fail closed. One request/feed, one feed/host/job, 30-second host
  cooldown, 900-second recurring interval, durable attempt IDs, error backoff,
  Retry-After and job locking reuse the existing coordinator. Default six feeds,
  12 retained records/feed; parser response limits still apply before retention.
- Fixed a real retention defect: bounded acquisition previously sliced random
  identifier order. It now prioritizes PIT-eligible latest source publication or,
  if publication is absent, update time; future/unavailable records cannot displace
  eligible ones. Exclusions and omissions remain explicit. Whole response hashes,
  original URLs, supplied publication/update, first-seen/retrieval/available-at,
  and config provenance persist; updates do not become publication/occurrence.
- Repeated canonical URLs collapse in article-level metrics; acquisition and
  correction history remain immutable. Conservative publisher/copy clusters are
  included in exports; syndication and original-incident independence stay UNKNOWN.
  Existing candidate/incident/claim guards remain authoritative: different sources
  never become automatic corroboration. No matcher or threshold tuning.
- Real mixed graph testing exposed stale/long records crowding out geopolitics.
  The 6,000-character narrative reservation now prioritizes recent records across
  domains and original news/speech/event formats over routine/photo formats, and
  avoids redundant prompt fields. Full provenance remains stored. OGL attribution
  survives compact rendering. Total information cap remains **28,000 characters**.

This is a finite, operational poll job suitable for an external 15-minute
scheduler, **not an installed continuously running service**. No scheduler or
unattended latency/uptime/recall claim is made. Cadence checks prevent immediate
repeated polls, and missed rolling-feed windows remain gaps.

## Actual live results, not hypothetical coverage

Bounded jobs ran Nov 1 **08:14:24–08:18:55 UTC / 15:14:24–15:18:55 Asia/Saigon**.
Five coordinator invocations plus one deliberate NASS-only acquisition after
fixing retention. Failed/denied attempts were not retried automatically.
Archive cutoff `2026-11-01T08:18:55.835718+00:00`.

| Publisher/feed | Actual retained evidence and freshness | Interpretation |
|---|---|---|
| NASA recent | 10 article URLs; source publications Oct 29–Nov 1, newest Nov 1 04:05 UTC | Fresh science stream, including Hubble servicing and MAX POWER notices; many astronomy/photo notices. Not ten verified technology incidents or AI/cyber coverage. |
| USGS significant earthquakes | 1 URL, “M 6.4 - southeast of Easter Island”; source update Oct 30 10:38:47.040 UTC | Fresh updated global hazard record. Original publication and earthquake occurrence not supplied by retained fields. |
| UK FCDO | 12 URLs; newest update Nov 1 02:47:08 UTC | Fresh sanctions/travel/UN statements, including Libya, Western Sahara and Colombia; government positions, not independent conflict verification. |
| UK health | 18 unique retained URLs across two selection versions; newest update Oct 30 13:33:30 UTC | Includes chickenpox, TB and outbreak-report notices alongside guidance/administration. Updated feeds, not fresh outbreak occurrence proof. |
| UK trade | 12 URLs; newest update Oct 30 15:32 UTC | Includes military export undertaking and trade factsheet notices; many administrative/labour publications. Not twelve trade shocks. |
| USGS drought | 8 URLs; latest supplied publication Aug 12, 2026 | Stale for current water monitoring. |
| USGS flood | 12 new recent-selected URLs plus 4 earlier Phase 3.6-only URLs remain visible; newest Oct 23, 2026 | Latest feed still outside seven-day window. Earlier slice understated recentness because it selected by hash; no fresh flood claim. |
| NASS | 23 unique retained URLs after corrected selection; latest Sep 24, 2025 | Stale. Entire eligible parsed snapshot has no later publication. 24 other-host links excluded; corrected request retains 12 and omits 276 eligible items. |
| NASA technology | 10 URLs; newest Oct 22, 2026 | Stale specialized feed, despite successful retrieval. |
| EIA | 0 acquired | robots disallows `/rss`; feed request refused. |
| CDC initial candidate | 0 observations | Specific syndication restrictions unresolved; endpoint content failed RSS/Atom parsing. Removed from operational configuration. |

Freshness is explicitly **seven days**, with separate **24-hour counts**, not an
unqualified “timely” designation. Snapshot metrics: 53 unique retained URLs with
recent publication/update across five **feed-request families**, three conservative
publishing groups (NASA, USGS, UK Government). Only two records meet 24 hours: a
NASA astronomy notice and an Ecuador travel-advice update. This does **not** prove
three families of new incidents in 24 hours. All UK departments share one group.
NASA/USGS/UK are institutionally distinct original agency publishers, but incident
origin independence, regional/language recall, source bias and corroboration have
not been investigated. Consequently the independent-origin/corroboration target
is **unverified**, not silently passed by counting hosts.

`tests/fixtures/phase37/real_specimens.json` archives **106** unique source/article
retained records acquired in this session, including stale records. This is not
106 incidents or the full feeds. Four older Phase 3.6-only flood URLs explain the
larger cumulative store metrics. Archived normalized fields/response hashes are
not original XML. `operational_results.json` preserves five bounded run outcomes,
robots checks and snapshot metrics; SQLite also preserves the deliberate final
NASS attempt. The initial hash-selected reports remain archived as historical
attempts rather than rewritten to hide the retention defect.

Exact policies, limitations, robots outcomes and candidate failures are in
[source eligibility review](PHASE_3_7_SOURCE_RIGHTS.md). Current State and CISA
research endpoints returned 403. BBC/GDELT reuse remains unresolved. No permission
for their article bodies or paid substitute was inferred.

## Human review packet: proposals only

`articles_unreviewed.json` contains hash-bound article packets from the existing
adjudication workflow. `pairs_unreviewed.json` contains three proposals, all
**UNREVIEWED / pending / label=unknown**, with URLs, publishing group, supplied
dates, title-derived location, rationale and uncertainty:

1. Plausible same incident: USGS Florida Panhandle Hurricane Isaias flood response
   and explicit “Day 2” follow-up (publications Oct 10–11). Same publisher; no
   independence claim. These are older reports, not freshly occurring incidents.
2. Plausible distinct incidents: that Florida flood response versus the southeast
   of Easter Island earthquake record. Both USGS; occurrence dates remain null.
3. Possible same report release: UK chickenpox hospitalisation news and varicella
   epidemiological publication. Not asserted to be the same outbreak/incident.

Occurrence dates stay null; publication/update is not substituted for occurrence.
Agent-selected proposals are not human labels. **Human reviews 0. No precision,
recall, TP/FP diagnostic or new evaluated holdout**; nothing was promoted into
incident membership or reviewed context. Preserve the retired Phase 3.6 artifacts.
Use Phase 3.6's independent article review, separate pair adjudication, conservative
connected origin/incident/copy clustering and frozen untouched holdout workflow.
Review packets bind the live canonical versions; normalized offline replay is a
test specimen, not a replacement for those live fingerprint-bound versions.

## Validation

- Final full offline suite: **1,572 passed + 99 subtests**, four skipped, one
  integration test deselected, 20 existing model warnings; **50.26 seconds**.
  Skips: three POSIX permission tests on Windows, optional `langchain_aws` absent.
  Parent `phase37-regression.txt` retains the full output locally.
- Thirty focused tests passed: policy refusal, bounds/current retention, real
  specimen early/late/reopen/repeat replay, publication/update distinction,
  conservative origins, pending pair identity, specialist/context contracts and
  actual mixed analyst graph. Existing full suite covers future corrections,
  review availability, source-independent corroboration and event-link guards.
- The new actual Market Analyst graph uses **real archived WORLD metadata with
  offline BTC/BLS/H.4.1/RRP fixtures and a test model**, all visible under 28k.
  No live market or macro observations were newly acquired in this milestone.
- All 232 tracked/new project Python files passed Ruff and AST syntax checks.
  Diff whitespace and canonical SQLite `integrity_check` passed (`ok`).
- Initial integration exposed context crowding, fixed and retested. A compact
  rendering lifecycle-key regression was caught and corrected; no failed final
  tests. Existing Phase 3.6 frozen replay remains passing and unchanged.

## Remaining Phase 3 exit gates

1. Sustained timely, geographically/language-diverse original evidence and
   independent reporting of shared incidents, not only agency announcements.
   Food/agriculture, drought, physical grid incidents and specialist AI/cyber need
   viable rights-cleared fresh sources. Existing agency feed failures are explicit.
2. Independent human article/occurrence/location and pair adjudication, authentic
   positives/hard negatives, correction/syndication/origin ground truth and an
   untouched incident-cluster holdout before real-world precision/recall claims.
3. Measured cadence, latency, missed-feed windows, source health and useful incident
   yield; fresh administrative/photo notices alone do not satisfy a world radar.
4. Macro gates unchanged: Treasury **daily TGA and yields rights-gated**, BEA
   **GDP/PCE incomplete**, **BLS live calendar unavailable**, **FRED disabled**.

Followed [SECURE_EXECUTION.md](SECURE_EXECUTION.md): direct patches and small
auditable commands, existing reviewed environment/dependencies, no giant
PowerShell source here-strings, installer, exclusion, Defender/policy changes or
bypass. No new security alert/block surfaced through tools; Defender event logs
were not audited. Prior FileFix detection cause remains uncertain, not a proven
false positive. All work remains local; no push authorized or attempted.
