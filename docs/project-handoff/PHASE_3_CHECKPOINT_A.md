# Phase 3 Acquisition Upgrade — Checkpoint A — 2026-11-02

Implementation only in existing TradingAgents checkout and canonical SQLite schema.
Phase 3 remains IN_PROGRESS; no Phase 4 causal interpretation or Phase 5 trade logic.
Checkpoint B/C discovery, attention/virality and BTC depth/flow are NOT implemented.

## Starting state and authority

Verified branch `phase-3-event-narrative-slice`, starting local HEAD
`e413ca05c272837173303ead06c0109df485ad64`; no tracked modifications.
Preexisting untracked `.phase12-tools/` and
`docs/project-handoff/PHASE_3_BOTTLENECK_DIAGNOSIS.md` preserved and excluded from staging.
Origin lookup with credential helper disabled failed DNS (`Could not resolve host: github.com`).
Prior user-verified remote `a619fe40e67606c92277eb886bd8b5c4aa03b93e` is historical,
not a newly verified remote. No push authorized, attempted or performed, including
older local commits fec1a97/e413ca05. No merge/rebase/reset/main operation.

Read revised adopted PRODUCT_BLUEPRINT, MASTER_PROMPT and RESOURCE_MANIFEST v1.1
from parent workspace, living exit-readiness/Phase3.8/bottleneck/security/coverage
documents and current implementation. Synced `sources/` originals untouched.

## Implemented contracts

- `sources.NewsDiscoveryConfig.intake_contract`: additive parser/byte bounds,
  provider order/window, unknown upstream omissions, retention semantics and
  separate summary access/retention/inference/redistribution rights. Existing
  source fingerprints and source versions remain stable; no data migration.
- `news.parse_news_snapshot`: RSS description and Atom summary extraction under
  the rights gate, source item positions, canonical mention identity and copy
  lineage, snapshot counts even for empty/all-excluded responses. Duplicate
  response items counted separately. `NewsParserOverflow` exposes total items,
  excess above parser cap and the entire atomic-rejected count; no partial success.
- `news.poll_once`: independent parser and retention caps, optional aware
  `window_start`, explicit publication-else-update window semantics (not occurrence),
  provider window/order unknowns, cap/window/host-exclusion/duplicate counts,
  snapshot/query/config/run provenance. Bounded per-snapshot manifest reconciles
  eligible canonical URL hashes and version hashes, provider positions, supplied
  dates and retained/omitted/window/future-gated states. The manifest is coverage
  metadata, not evidence of omitted contents. No headlines/text from omitted
  records are made available to the analyst. Upstream omissions remain unknown.
- `polling.coordinate` and `world_radar.run`: per-source retention overrides,
  explicit run/host budgets, host cooldown, source filter and not-due/backoff
  reasons; query and start/completion metadata. Existing default 12 is retained,
  not indiscriminately raised. CLI exposes `--retention-limit` and `--window-start`.
  Same poll ID/config is still an immutable retry; changed policy requires a later
  deliberate acquisition, not alteration of a recorded attempt.
- `news_evidence`: HEADLINE_METADATA_ONLY and FEED_SUMMARY are implemented levels;
  SNIPPET/EXCERPT/FULL_BODY are vocabulary for future eligible adapters, not claimed
  collectors. Summary retention requires all four rights explicitly `permitted`,
  a rights reference and a review date in trusted registry configuration. Missing
  rights fail closed to headline metadata. Retained text is a 1,200-character
  normalized text prefix; original retrieved summary prefix (2,400 characters),
  original SHA256, truncation flags, field/endpoint, publisher, transformation and
  rights provenance are retained. No fetched article body, generated substitute,
  cross-publisher text copying or scraping bypass. A feed summary is never a body.
- `source_health`: latest intake counters and selection reason exposed as-of;
  absent fields in legacy attempts remain null/UNKNOWN, not zero-filled history.
- `narrative_events`: evidence level and attributed permitted context reach the
  real graph; selected versus canonical candidate count, latest-per-config
  acquisition omissions/failures and unknown gaps are explicit. Raw observations,
  copies/revisions and independent mentions stay distinct. No claim that a small
  selected prompt represents all observations. Repeated identity hashes and
  repeated status prose compacted; whole-record fit keeps the 6k narrative slot
  and mixed graph below 28k without dropping the tested WORLD domain coverage.
- `evidence_slice`/`world_radar` replay: frozen legacy specimens reproduce their
  original payload shape; immutable review fingerprints are not weakened and
  fixtures are not rewritten. New metadata specimens preserve source position,
  snapshot counts and first-seen provenance for deterministic offline round trips.

All durable evidence, source copies, revisions, manifests and health continue in
the existing observation/coverage/source tables of ONE SQLite store. No alternate
operational database or authoritative cache. Tests use isolated temporary stores.
Existing earliest-local-first-seen, conservative available-at (including reported
future updates/publication), immutable raw history and canonical article collapse
are preserved. Re-acquiring a previously omitted item becomes available only at
the later local retrieval; it is not backdated to its publication/manifest date.

## Rights and operating limits

Operational exact-config/robots gates are unchanged: BBC/GDELT remain withheld,
EIA robots gate remains, CDC/CISA/State uncertainties remain. Existing agency
review scope excludes summaries. Consequently **no operational publisher summary
has been newly cleared or collected**; eligible summary behavior is verified with
explicitly synthetic permission fixtures. This is a remaining operational limit,
not completion of informative-content coverage. Human/manual sessions remain valid.

GOV.UK reuse page was readable through the research web surface on Nov 2 and
requires OGL conditions and robots compliance:
https://www.gov.uk/help/reuse-govuk-content . The linked current OGL text returned
403 through that surface. No expanded summary grant inferred from this check or
from public access. Follow-up: exact summary scope review, exceptions/attribution
and actual eligible feed specimens before enabling four summary rights in an
operational config. A changed config fingerprint must be explicitly reviewed by
the existing WORLD allowlist; no bypass is introduced.

Parser overflow deliberately rejects the whole snapshot: count is known, item
identities/content are uncollected. Byte/unsafe/malformed failures may have unknown
item count. Manifest identities cover successfully parsed eligible unique records;
host-excluded and duplicate items are separately counted, not independent mentions.
Window filtering uses publication else update, with undated items retained as
unknown; it is not an incident-time reconciliation or recovery of unseen history.
Default cap 12 still causes omissions unless a caller deliberately selects a
suitable bounded per-source limit. No live source refresh, benchmark recall,
new original-incident confirmation, human labels, scheduler or continuous uptime
was established. Previous Phase 3 and macro exit blockers remain open.

## Validation and security

Checkpoint A tests cover each rights gate, missing/partial/Atom evidence, bounded
original context, out-of-order feed retention and hashed omission reconciliation,
window exclusion, parser overflow, duplicate/third-party/future records, later
re-acquisition without backdating, repeated polls and corrected summary as one
canonical mention, historical payload/reopen compatibility, health deferrals,
legacy frozen manifests, new metadata round-trip and actual graph integration.

Initial focused graph regression exposed context crowding; fixed by compacting
redundant fields. Initial full regression: 1 failed, 1,606 passed +99 subtests;
failure was frozen historical replay fingerprint drift, corrected in the replay
adapter without weakening review hashes. Subsequent full run: 1,609 passed +99
subtests, four expected skips, one integration deselected, 20 existing warnings.
Final code/specimen round-trip regression: **1,610 passed +99 subtests**, four
expected skips, one integration deselected, 20 existing warnings, 52.51 seconds.
Skips are three Windows/POSIX permission-mode checks and the absent optional AWS
dependency. Final full log is parent-workspace `checkpoint-a-regression-verified.txt`;
earlier failed and successful logs are retained separately for diagnosis.
Final focused replay/acquisition/WORLD suite: 32 passed. Earlier broader focused
suite: 107 passed. Full project Ruff and 240-file AST syntax checks passed.

Canonical database opened only with SQLite `mode=ro`; integrity `ok`. SHA256 before
and after that check: `3e7548c55e59bf42e16a61c570122b98f5e056dcf2fa17c578d6c63a7595ec4b`.
No canonical database writes or production backfill. Direct patches and small
auditable commands, existing reviewed environment, no downloads/installers,
security/Defender/execution-policy changes or credential-helper retry. No new
security alert surfaced through tools; no Defender event-log audit or proven
false-positive diagnosis. Implementation commit is LOCAL ONLY after validation.

## Recommended next checkpoint

Checkpoint B: bounded free non-official original-source discovery pilot using the
same adapters/store, with exact rights-cleared informative summaries/context,
source/origin attribution, query/run manifests and a small independently enumerated
in-window reconciliation set. Choose genuinely distinct original reporting sources;
publisher count alone does not establish independent evidence. Preserve partial
evidence and unknowns. Adaptive/general AI scans need actual available capability
and separate validation. Checkpoint C virality and BTC depth/orderflow remain later;
no Phase 3 exit, Phase 4 causal or Phase 5 trading advancement is claimed here.
