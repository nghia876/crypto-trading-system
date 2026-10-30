# Phase 3.3 bounded candidate links and evidence-gap research — 2026-10-30

Status: VERIFIED bounded heuristic slice after the checks below; Phase 3 and full semantic Phase 3.3 remain IN_PROGRESS. No directional BTC, causal-price, trading-alpha or autonomous-operation claim.

## Verified starting state and authorization

Existing repository: nghia876/crypto-trading-system; checkout repo-checkout; branch phase-3-event-narrative-slice. Starting HEAD e801a80c8f7f672f64573da198dce0ccb80f65c4. Tracked files clean; pre-existing untracked .phase12-tools/ left untouched. No main operation, history rewrite, push, paid service, dependency change or secret logging.

The workspace MASTER_CHAT_HANDOFF_2026-10-30.md reports host PowerShell push/verification through f87ddbefd0126f05b0ad29b53d5065ea9796fddc. This supersedes historical remote-at-82c6ba6 statements in earlier documents. That remote result is supplied checkpoint evidence, not a fresh remote query in this session. e801a80 and this implementation remain LOCAL ONLY; no push is authorized. The new commit hash is reported in the completion message rather than embedded self-referentially here.

Read-only references inspected: canonical parent sources/PRODUCT_BLUEPRINT.md, MASTER_PROMPT.md, RESOURCE_MANIFEST.md, master handoff, WORLD_SPECIALIST_IMPLEMENTATION.md, EVENT_INTELLIGENCE_IMPLEMENTATION.md, SOURCE_COVERAGE_MATRIX.md and the living project status. Canonical sources/ and .phase12-tools/ were not modified.

## Inputs, implementation and boundaries

The existing event_intelligence.py, Observation, MarketDataBatch, SQLiteInformationStore and view_at remain the only evidence/provenance/PIT pipeline. No schema migration, duplicate graph, incident database or new feed. Existing reviewed membership, explicit retractions and claim_lifecycle support/contradiction/correction/origin/syndication/independence are retained.

- suggest_event_links(view) compares the latest available article versions, including already integrated broad WORLD discoveries. Discovery does not require BTC terms, prices or anomalies. The discovery-domain label is not treated as verified event type.
- Event types use a versioned English keyword lexicon covering drought/water, flood, wildfire, war, sanctions/trade, agriculture/food, energy/grid, disasters, health, science/AI/chips/cyber and regulation. This is candidate classification, not semantic extraction or new source coverage.
- Match requirements: shared event type; shared capitalized-name/optional entity anchor; at least two shared distinctive words; Jaccard overlap >=0.55; publication time (or acquisition availability fallback) within 72 hours. These are time proxies, never inferred occurrence times.
- Common event/generic words and a limited country-name list are excluded as distinctive anchors. Disjoint explicit locations, disjoint location phrases after in/near/at, or distinct named anchors on both sides veto a suggestion. A shared country or geographic proximity cannot override those guards. Missing/ambiguous metadata can cause false negatives; this is not geocoding.
- At most 128 latest records, 8,128 pair comparisons and 32 suggestions per invocation. Smaller configurable budgets supported; omitted records/candidates disclosed. Latest-record selection is not a measured global recall guarantee.
- Stable sorting and policy version are retained along with exact evidence IDs, source IDs/URLs, publication, first-known, retrieval, availability, shared types/anchors/words, similarity, time-proxy delta and lexical correction/denial cues. Cue words are requests for review, never contradiction findings.
- record_event_candidates appends an immutable suggestion snapshot at current acquisition time. candidate_history replays stored snapshots and eligible references; it does not recompute past suggestions with future data or newer policy. Candidate links never append incident membership, support, confirmation or independence assertions. Reviewed/confirmed reporting relationships remain in the existing reviewed lifecycle.
- Latest persisted snapshot annotations enter the real analyst graph separately as event_link_candidates, at most two per retained narrative record. Reviewed incidents include open gap annotations. Repeated unknown/hash fields are compacted in annotated records to preserve WORLD breadth; evidence/source/available times and source attribution remain. Complete provenance stays in SQLite. Whole-record omissions remain explicit under the protected 6,000-character WORLD reservation and unchanged 28,000-character information cap. This is not guaranteed inclusion of every event.

## Adaptive gap research

research_plan/research_once accept either an existing reviewed incident key or one available narrative evidence ID, so a new event does not require prior identity review to begin research. Automatically open requirements include unknown occurrence, missing independently evidenced origin, missing original-source reporting, disconfirmation review, update/correction checks and existing reviewed unresolved contradictions.

Plans generate at most five gap-specific, claim-targeted questions; every question stays open. Existing contradictory reports add an explicit competing-account question. Agency/original reporting can remove the missing-original-report requirement; it does not prove truth, independence or contradiction resolution. Questions are audit/local-filter context, not arbitrary web search queries.

Execution uses ONLY existing rights-reviewed USGS drought/river-flood, EIA and NASS feed configurations matching the seed domains: default two, maximum four configurations. It retains the existing store lock, source eligibility, 2 MB body cap, per-feed item limits, (3.05s connect, 10s read) timeout, streaming elapsed checks, redirect refusal, no immediate retries, durable due times, Retry-After and shared-host cooldown. The source filter prevents unrelated configured sources from being queried even when the coordinator's internal minimum budget is two.

The existing at-most-16 acquired lexical evidence shortlist remains review-only and is distinct from the stricter event-link suggestions. Research also records a bounded automatic candidate snapshot and its audit ID. Immutable attempts record cutoff, seeds, open gaps/questions, selected sources, poll IDs, shortlist and attempted/deferred status. Unsupported domains now append an explicit no-eligible-source audit without any request. Failures, empty feeds, unsupported domains and cooldown deferrals preserve gaps and UNKNOWN truth; they never invent findings or prove absence. New claims/corrections still require reviewed assertions.

No background scheduler, analyst-triggered network access, semantic disconfirmation engine, arbitrary search/crawling, article bodies or new source clearance. Candidate generation/research are caller-driven bounded operations. Generic polling is unchanged; research invokes suggestions automatically after its bounded acquisition.

## CLI and replay

Use the existing canonical database file; the CLI refuses missing paths and refuses historical cutoffs on writes:

```powershell
python -m tradingagents.information.event_intelligence suggest --store 'EXISTING-CANONICAL-SQLITE'
python -m tradingagents.information.event_intelligence plan --store 'EXISTING-CANONICAL-SQLITE' --incident 'AVAILABLE-EVIDENCE-ID-OR-REVIEWED-INCIDENT' --cutoff '2026-10-30T10:00:00+00:00'
python -m tradingagents.information.event_intelligence research --store 'EXISTING-CANONICAL-SQLITE' --incident 'AVAILABLE-EVIDENCE-ID-OR-REVIEWED-INCIDENT'
```

Existing link/show commands remain for reviewed membership/state. Python candidate_history(store.view_at(cutoff)) returns immutable suggestion history. API callers remain responsible for truthful acquisition timestamps, as in existing curated assertions. A later suggestion or correction is gated by local retrieval/availability even when publication/first-known is earlier. Reopen does not change history. No historical upstream vintage reconstruction is claimed.

## Acceptance evidence

| Requirement | Executed fixture evidence |
|---|---|
| Independently sourced same drought suggests link without BTC terms | Different-source paraphrased Colorado farmland/irrigation reports; link candidate, no support assertion |
| Unrelated floods in one country stay separate | Lahore/Karachi including title-case headlines; Acapulco/Monterrey; explicit location mismatch and time/type vetoes |
| Syndication cannot count as independent support | Shared publisher, reviewed syndication, repeated acquisitions; origin gap remains open and support stays empty |
| Late contradiction/correction invisible before known | Old publication/first-known but later retrieval; early snapshot/gaps unchanged; late cue and reviewed contradiction visible only later |
| Open gap when evidence missing | Single unreviewed seed, missing original/independent evidence, empty feed and unsupported-domain audits |
| Rate-limit/timeouts bounded, no invented findings | One request per eligible config, timeout/redirect arguments, HTTP 429 Retry-After and durable reopen cooldown, no remote error text |
| Mixed actual graph under cap, WORLD retained | Actual TradingAgentsGraph retains suggested link, reviewed incident/gaps, war/technology/cyber, four specialist domains, BTC funding, BLS/calendar, H.4.1 and RRP; future membership/macro/liquidity excluded |
| Identical PIT candidate history after reopen | Exact snapshot equality before acquisition, at first suggestion and after later correction; repeat snapshot idempotence |
| Bounded deterministic matching and usable CLI | Input/output caps with explicit omissions, stable sorting/reopen, structured JSON and historical-write/missing-file refusal |

Final offline regression: **1,532 passed + 99 subtests**, four skipped, one integration test deselected, 20 existing model-name warnings, **45.15 seconds**. Skips are three Windows/POSIX file-mode checks and optional langchain_aws. The 14 new candidate acceptance cases and the strengthened actual-graph fixture pass. Project Ruff (`tradingagents tests cli main.py`), AST syntax for all four changed Python files and whitespace diff checks passed. Final test report: workspace-root phase33-regression.txt, outside Git. No network, live LLM or trading is used by the offline suite.

Changes: event_intelligence.py (suggestions, immutable audits, gap questions, seed research and CLI); narrative_events.py (compact candidate/gap graph annotations); test_event_candidates.py (14 acceptance cases); test_graph_end_to_end.py (mixed actual-graph acceptance); this handoff and current checkpoint headers in Phase 3, event intelligence, WORLD specialist, source coverage and living roadmap documents. No collector/source-registry or dependency changes.

## Live/source eligibility check

EIA's official reuse policy and RSS directory were re-opened on 2026-10-30:
https://www.eia.gov/about/copyrights_reuse.php
https://www.eia.gov/tools/rssfeeds/
Agency information products permit reuse with acknowledgment including date; protected third-party material and marks have separate restrictions. Scope stays agency-produced headline/link/date metadata with attribution and third-party host exclusions; no bodies, images or blanket AI-training clearance.

A single bounded EIA fetch/parse was attempted without persistence at 2026-10-30T10:50:41.586165Z and returned ConnectionError. An earlier local invocation omitted the required session argument and made no HTTP request. No new live acquisition success is claimed. Diagnostic report: workspace-root phase33-live-sample.json, outside Git. The earlier live canonical local-runtime/information.sqlite3 is still ABSENT; no replacement live database was created and no fresh preserved-BLS-row/integrity audit is claimed. Offline reopen tests use temporary fixtures.

## Known limitations and next bounded actions

Full semantic Phase 3.3 remains IN_PROGRESS: no semantic identity/negation/correction judgment, evaluated precision/recall, multilingual normalization, complete geographic disambiguation, measured independent origins or significance ranking. Conservative name/time/word guards can reject related reports; similarly worded unrelated episodes can still require reviewer rejection. Source coverage, callback cadence and service-level freshness remain incomplete. Questions remaining open is intentional.

WORLD stays central: original global disaster/wildfire, health, science/AI/chips/cyber, trade/sanctions and grid-incident breadth, regional/language coverage and quantitative food/water/hazard surveillance remain missing/unvalidated. Existing BBC/GDELT licensing/operational caveats remain; the research executor does not query them. No new mandatory paid service.

Macro restrictions unchanged: daily TGA gated; Treasury yield acquisition/analyst use rights-gated; BEA GDP/PCE/core PCE incomplete; BLS live calendar unavailable; FRED disabled by default.

Next: build a reviewed, source-attributed offline evaluation set of at least 30 same-event and 30 unrelated-nearby/recurring pairs across WORLD domains, including denials, corrections and syndicated copies. Measure candidate precision/recall by domain and verify every late-evidence/reopen cutoff. Tune only against a held-out split before expanding automatic decisions. Separately validate one free original health/cyber/disaster feed's rights, host scope, timestamps, corrections and bounded failure behavior in the SAME pipeline. Any push of e801a80 or this new commit needs separate explicit authorization.
