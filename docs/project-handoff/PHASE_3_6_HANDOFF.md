# Phase 3.6 bounded acquisition and frozen review workflow — 2026-11-01

Phase 3 remains **IN_PROGRESS**. Implemented locally in the existing TradingAgents
checkout; no push authorized or attempted. Starting HEAD and fresh read-only
remote feature ref both `bcb700fdd06385c90fa7399e4fe9525a87c67d62`.
Tracked starting tree clean; existing untracked `.phase12-tools/` preserved.
No changes to main, synced canonical sources, dependencies or security settings.

## Delivered

- `evidence_slice` acquires only the two exact reviewed USGS configurations,
  with a fail-closed rights gate, two requests, default four retained items each,
  existing byte/item/time limits, refused redirects and no automatic retries.
  Existing polling writes evidence, source definitions and health into the same
  canonical SQLite information/PIT store. New slice-limit omissions are explicit.
- Raw item URL, agency publisher, supplied publication/update fields, local
  first-seen/retrieval, full-response hash and configuration provenance survive.
  Article bodies, images, logos and third-party links are excluded. Supplied
  publication dates are not event-occurrence dates or historical acquisition.
- `evidence_review` provides article-only packets, explicit adjudication/import,
  immutable-version binding, dispute rejection, reviewer kind/provenance and
  prospective context corrections through the existing canonical store API.
  Pair labels/rationales and partition clusters remain outside matching/SQLite.
- Frozen manifests join whole incident, origin and duplicate/correction clusters
  transitively, sort components by seeded SHA-256 and reserve the first ceiling
  20% (at least one component) for holdout. Unknown cluster IDs block freezing;
  cross-split pairs fail. Article, context, labels and matcher hashes are checked.
  New unfrozen context cannot be used to tune an inspected holdout. No matcher,
  threshold or discovery tuning was performed in this milestone.
- Early/late scoring reports TP/FP/TN/FN, precision/recall, family, hard-negative,
  reporting-channel and review-kind strata, unknown/unavailable exclusions and
  candidate/record omissions. Reopened-store results match. Scoring marks the
  holdout retired; preserve its frozen artifacts and use new clusters for tuning.

## Actual live evidence and rights

The canonical database was absent from the supplied checkout. Initialized the one
prospective canonical store at `../canonical-information.sqlite3`; no separate
event database or live system. Database remains local outside Git. First attempt
recorded two connection failures. After network permission, a deliberate new poll
ID acquired **8 actual USGS records**: 4 drought/water and 4 river-flood items.
Full parsed eligible feeds contained 8 and 370 records; 4 and 366 omitted by bound.
No further requests or article crawling. SQLite `integrity_check`: `ok`.

Actual acquisition: 2026-11-01 04:41:44.730843–04:41:45.720056 UTC
(11:41:44–11:41:45 Asia/Saigon). Retained source publication dates span
2022-08-19–2026-03-28. **Both feeds' content is stale**; successful retrieval does
not establish current coverage. Reports include NY low streamflow, Oregon fires
and gages, NJ low flow, CA runoff/flooding, Oregon atmospheric river and Ohio flood.
These are source claims, not independently verified incidents or current hazards.

Rights reference checked live: [USGS Copyrights and Credits](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits),
and [USGS policies](https://www.usgs.gov/policies-and-notices). USGS-produced
information is US public domain with credit requested; non-USGS protected works
are exceptions. This bounded scope permits archival/model processing of agency
headline/link/date fields on that basis, not blanket clearance of USGS-hosted
content. No special AI permission was inferred for copyrighted third-party works.
Other-jurisdiction rights have not been independently adjudicated. Robots URL and
generic feeds index were inaccessible through web research; existing specific RSS
endpoints succeeded. No rights expansion to BBC/GDELT bodies or new publishers.

`tests/fixtures/phase36/` archives normalized **real acquired fields**, source
response hashes, review packets, label provenance, frozen manifest and outcomes.
It does not archive the complete RSS response or article body. Offline specimen
replay reconstructs matching canonical observations in temporary test stores;
it must not be used to backdate a newly acquired production database.

## Frozen real-source diagnostic — no accuracy claim

Manifest SHA-256:
`145c776e4531859d4ca6f80c281f2875465fdd9bb70ea10cdfd4d2a64d36ad0a`.
Matcher v2 unchanged. Files were written and frozen before their first score;
no subsequent label, partition or matcher adjustment based on outcomes.

All eight records share one conservative USGS origin/partition component. The
incident partition key deliberately groups the entire slice conservatively; it
does **not** assert one incident. All eight are held out; there is no development
sample. Original publisher is known; independent origins/corroboration are not
demonstrated. Article occurrence/location fields stay null/pending; no fabricated
human adjudication or semantic incident promotion was imported.

Five title-only **agent-reviewed**, low-confidence pairs: three stipulated
different-event negatives and two unknown relationships (CA correction and
same-publisher possible shared reporting). Early cutoff excludes all five pairs.
Late cutoff: **TP0 / FP0 / TN3 / FN0; 2 unknown excluded**. Precision and recall
are **undefined**, because there are no labeled positives or predicted positives.
Hard negatives TN2; other place-negative TN1. Reporting strata group same-publisher
records conservatively, not as proven syndication. Correction/syndication strata
contain unknowns, not a validated real correction/syndication benchmark.
Candidate and record omissions zero on this diagnostic; reopened scores identical.

Human reviews **0**. Agent title-based negatives can be wrong; publication-time
distance cannot establish occurrence identity. No confidence interval, independent
holdout quality estimate, real-world precision validation or Phase 3 exit claim.
This inspected slice is retired from independent evaluation. Existing synthetic
80-pair baseline and 24-pair context contract results remain distinct and unchanged.

## Human review workflow

1. Export article-only JSON with `python -m tradingagents.information.evidence_review
   packet --store CANONICAL --cutoff ISO_TIME --output article-review-v1.json`.
   Reviewers must not inspect pair labels, predictions or frozen test outcomes.
   Check eligible original material manually. Record actual reviewer identity,
   acquisition time, provenance, rationale, canonical location granularity and
   occurrence bounds. Unknown occurrence/place stays null. Use `review_kind` of
   `human_declared`, `agent_reviewed` or `synthetic_authored`; strings cannot
   authenticate human participation. Preserve all disputed proposals externally.
2. Only after adjudication set `status=adjudicated`; import ONE article record
   with `apply --store CANONICAL --articles article.json --output receipt.json`.
   Never backdate `recorded_at`. Bind the article fingerprint. Correct an active
   review by explicit `supersedes` review ID; all-null correction withdraws context.
   Revised article versions require separate reviews. Disputes/pending records
   cannot be promoted. Export a fresh packet after import to freeze context hashes.
3. A separate human pair reviewer works from source evidence without matcher
   outputs. External pair JSON must include `evidence_ids`, `label` of same_event,
   different_event or unknown, `review_status` (pending/disputed/human_reviewed/
   agent_reviewed/synthetic_authored), `reviewer`, actual `reviewed_at`, `rationale`,
   `provenance`, `confidence`, `family`, `stratum`, `reporting_relationship`.
   Use unknown/disputed for unresolved disagreement. Record proposals and final
   adjudicator separately with `label_version` and `supersedes_label_sha256`;
   retain old files instead of overwriting. Never turn agent annotation into
   human_reviewed by renaming its reviewer string.
4. Assign conservative incident/origin/URL-copy clusters BEFORE matching.
   Keep corrections, aliases, syndication and nearby ambiguous episodes together
   when independence is unresolved. Unknown identities block freezing; explicitly
   document conservative groupings rather than inventing per-item origins.
   `freeze --articles ARTICLES --labels LABELS --seed FIXED --frozen-at ISO_TIME
   --output MANIFEST` hashes data, labels and matcher. Freeze before tuning.
5. `score --store CANONICAL --manifest MANIFEST --labels LABELS --cutoff EARLY
   --cutoff LATE --output REPORT` opens SQLite read-only. Keep labels outside the
   store. Scores are retrospective comparisons to later labels, not knowledge
   available at the early cutoff. Metadata/claims still use PIT visibility.
   Archive outcome/report hashes and retire the holdout after inspection. Human
   separation and a no-tuning policy require procedural enforcement; filesystem
   access and reviewer strings cannot prove independent conduct.

## Verification and reproduction

Use the existing reviewed environment `../phase3-final-env/Scripts/python.exe`;
no installations or `.phase12-tools/` changes. Commands below use `python` for
brevity. `python -m pytest -q` runs the full offline suite. Focused tests include
rights gating, real specimen parsing and full frozen rehydration, cluster leakage,
future-label/future-context rejection, dispute isolation, source failures,
no-BTC discovery, SQLite integrity/reopen and combined actual analyst graph.
Existing suite covers same-incident/nearby-unrelated, source corrections after
cutoff, synthetic comparisons and broad WORLD/macro graph under 28,000 characters.

Reproduce the saved real-source evaluation entirely offline with
`python -m pytest tests/test_evidence_review.py::test_recorded_real_manifest_reproducible_offline -q`.
Saved metrics/manifest/labels must not be regenerated to improve results.
For a NEW acquisition only, `evidence_slice --store CANONICAL --report REPORT
--poll-id NEW_ID` is one deliberate bounded live operation. The reviewed
`python -m tests.phase36_report --acquisition REPORT --store CANONICAL --output
NEW_DIRECTORY` writes frozen artifacts before scoring and refuses overwrites;
it is specific to this eight-item diagnostic, not an independent-label generator.

Final full offline suite: **1,562 passed + 99 subtests**, 4 skipped, 1 integration
test deselected, 20 existing model warnings; 48.07 seconds. Skips: three POSIX
permission tests on Windows and optional `langchain_aws` absent. Full tracked
Python plus new-file Ruff passed; scoped compileall syntax and diff whitespace
checks passed. Focused initial acquisition/review/context/specialist run: 41 passed;
final new review tests: 7 passed; new actual mixed graph: 1 passed. No failed
final tests. Initial lint found one import-order issue, corrected before full
checks. Parent `phase36-regression.txt` retains the full result locally.

## Remaining gates and security

Obtain sufficiently independent human metadata/pair adjudication, authentic
same-incident positives and hard negatives, original-source diversity, correction/
syndication ground truth and fresh incident-cluster holdout before tuning or any
real-world precision claim. US-centric stale agency headlines do not satisfy
global discovery breadth, latency, regional/language recall or independence.
Existing independent WORLD discovery remains active without BTC keywords or
price triggers: war/trade, drought/water, disasters/flood/wildfire, food/agriculture,
energy/grid, health/pandemic and science/AI/technology/cyber. Missing specialized
adapters and unknown coverage are still reported; no paid service added.

Macro gates unchanged: daily TGA and Treasury yield rights, incomplete BEA
GDP/PCE, unavailable BLS live calendar, disabled FRED. No live trading enabled.

Followed SECURE_EXECUTION.md: direct patches, small reviewed literal commands,
existing dependencies, no downloaded executable/installer, no Defender exclusions
or policy changes/bypass. Prior FileFix detection cause remains uncertain despite
user-reported clean full scan. No new security alert/block surfaced through tools;
Defender event logs were not audited. All new implementation stays LOCAL ONLY.
