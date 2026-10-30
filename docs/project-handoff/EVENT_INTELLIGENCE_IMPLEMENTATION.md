# Phase 3 event intelligence and bounded adaptive research — 2026-10-30

Status: VERIFIED bounded local implementation. Phase 3 remains IN_PROGRESS.

## Scope and architecture

`event_intelligence.py` adds immutable caller-reviewed incident membership to the existing Observation / SQLiteInformationStore / view_at architecture. A stable incident key identifies a reviewed episode/location, independently of article identity. Related conflicting accounts can share an incident; identical headlines about separate incidents need not merge. Headlines alone remain review candidates. No automatic semantic identity, event occurrence inference, causal inference, BTC reaction or trade alpha is claimed.

Membership records name exact available report versions and rationale. A revised article requires a new identity review; URL reuse never silently assigns a different episode to the earlier incident. Replacement memberships retract explicit earlier membership IDs in the same incident. Earlier views retain earlier membership. Article revisions and competing claims remain in existing claim_lifecycle history; incident membership does not create support or independence. First-known is earliest eligible local report acquisition; membership availability is separate, so a relationship learned later never appears earlier. Occurrence remains UNKNOWN. The shared-publisher guard now prevents two known channels of one publisher from satisfying independence even when a caller supplies an independence assertion. Existing syndication/origin transitive guards remain.

Compact incident annotations enter the actual analyst graph through existing whole-record narrative rendering. They share the protected 6,000-character narrative reservation inside the unchanged 28,000-character information cap. Existing round-robin domain selection and omission disclosure remain; this is not guaranteed recall or inclusion of every incident.

## Adaptive research and limits

`research_plan` adapts questions to contested vs unopposed reporting and selects at most four existing USGS/EIA/NASS source configurations for the incident's discovery domains (default two). It explicitly reports unsupported domains. No BBC/GDELT rights uncertainty is silently cleared. No new endpoints, article bodies, arbitrary URLs, paid tools, or database are introduced.

`research_once` locks the existing store and uses the existing coordinator, full registry health, durable due times, Retry-After and shared-host cooldown. A source filter limits requests while retaining host history across the full registry. Failed attempts remain unavailable coverage. Whole feeds are scanned for at most sixteen lexical candidates sharing two words of at least four characters with seed claims. This is bounded missing-evidence/disconfirmation discovery for human/semantic review, not a claim that a candidate contradicts, confirms or belongs to the incident. Repeated polls/candidates never become independent votes. The immutable research audit records cutoff, seed IDs, questions, source IDs, actual poll IDs, candidates and deferred/attempted status after completion. Semantic contradiction search remains unperformed; empty, failed or deferred acquisition proves no event absence. Ranking by significance, adaptive arbitrary web search and measured recall are open.

Command interface (run with the project Python from the checkout; use the EXISTING canonical database):

```powershell
python -m tradingagents.information.event_intelligence plan --store 'PATH-TO-EXISTING-CANONICAL-SQLITE' --incident 'reviewed-episode-key'
python -m tradingagents.information.event_intelligence link --store 'PATH-TO-EXISTING-CANONICAL-SQLITE' --incident 'reviewed-episode-key' --evidence 'AVAILABLE-OBSERVATION-ID' --rationale 'Location/episode evidence and review basis'
python -m tradingagents.information.event_intelligence research --store 'PATH-TO-EXISTING-CANONICAL-SQLITE' --incident 'reviewed-episode-key'
python -m tradingagents.information.event_intelligence show --store 'PATH-TO-EXISTING-CANONICAL-SQLITE' --incident 'reviewed-episode-key' --cutoff '2026-10-30T10:00:00+00:00'
```

The CLI refuses missing database paths; writes use current local time and reject historical cutoff arguments. Callers using the Python API are responsible for truthful acquisition timestamps, as for existing curated claim assertions.

## Rights and live sample

Only the already reviewed agency headline/link/date feeds are eligible for this follow-up executor. Existing agency attribution, original URL/date, rights references and third-party exclusions remain. EIA reuse and official RSS directory re-opened 2026-10-30:
https://www.eia.gov/about/copyrights_reuse.php
https://www.eia.gov/tools/rssfeeds/
EIA permits its information products with acknowledgment/date; protected third-party material and marks have separate restrictions. No blanket legal clearance or model-training permission is asserted.

One bounded EIA fetch/parse sample at 2026-10-30T10:13:58.077391Z returned 21 observations. No live LLM, article-body crawling or persistence. Report: workspace-root event-live-sample.json, outside Git. The previously reported local-runtime/information.sqlite3 and its 129 BLS observations are ABSENT in this checkout; no claim of fresh integrity/reopen validation of that live database is made and no substitute live database was created. Store/reopen verification uses isolated offline test fixtures only.

## Synchronization and audit boundary

Start HEAD: f87ddbefd0126f05b0ad29b53d5065ea9796fddc.
Fresh remote feature branch: 82c6ba6e4abc209dee605cda1b05ef74fc23dd2e.
Verified remote is an ancestor of start HEAD; pending range comprises:
72a72730f9830f0b2ff6134e14be391332930ce5 (M2A.1),
2f6db789c5d6515640a9f35bfd1205a71b175006 (M2A.2),
a253e754924b2d311efda9c21f33271fb8c6a4d9 (macro hardening),
f87ddbefd0126f05b0ad29b53d5065ea9796fddc (specialist WORLD).
Tracked starting state clean; only pre-existing untracked .phase12-tools/. Range is 26 files, 3,190 insertions, 24 deletions: code, public/synthetic fixtures and handoff documents. Secret/private-key/credential-pattern scan found only synthetic secret-like failure-message tests. No credentials, private datasets or runtime database selected for synchronization. Pattern scanning is not an absolute guarantee of absence. Existing BBC/GDELT, Treasury/BEA and FRED rights caveats remain disclosed; publishing code is not operational source clearance.

No authenticated push attempted: this execution surface runs under Work's restrictions and exposes no independent non-elevated host PowerShell execution mechanism. Starting another PowerShell through it would retain the known blocked credential-helper environment. No helper retry, elevation, security change or force push. Workspace-root Push-Verified-PreSession.ps1 is the guarded host fallback: exact origin/branch/clean tracked-state checks, pinned authorized start HEAD, expected remote parent, ancestry, normal exact-SHA push and fresh remote equality verification. It cannot include this session's new implementation commit even when HEAD advances. The older Push-M2A1.ps1 remains unchanged. No main branch operation or history rewrite.

## Preserved gaps

Daily Treasury TGA gated; Treasury 2y/10y acquisition/analyst use rights-gated; incomplete BEA GDP/PCE/core PCE; missing BLS live calendar; FRED disabled by default. Original health/science/AI/cyber/trade, global disasters/wildfire and infrastructure incident coverage, regional/language breadth, automatic semantic clustering/correction classification, independent-origin validation and prospective recall/latency evaluation remain open. Broad WORLD discovery has no BTC keyword/price movement prerequisite. Canonical sources/ and .phase12-tools/ were not edited.


## Final verification

- Full offline suite against the actual checkout: **1,518 passed + 99 subtests**, four skipped, one integration test deselected, 20 existing model-name warnings, 52.38 seconds. Skips: three Windows/POSIX mode checks and optional langchain_aws not installed. Shared project fixtures block network; no live LLM or trading operation.
- Focused incident/claim/news/specialist/recurring/narrative checks: **92 passed** before final full regression. Eight new tests cover related vs separate identical reports, immutable membership corrections, competing claims, repeat idempotence, future/reopen cutoffs, shared-publisher non-independence, missing-domain no-request behavior, source-failure cooldown, lexical candidates without automatic merges, exact-version review and combined BTC/BLS/H.4.1/RRP/WORLD context.
- The actual TradingAgentsGraph combined test now includes a reviewed incident and excludes a later membership, alongside broad war/technology/cyber evidence, four specialist domains, BTC funding, BLS/calendar, H.4.1 and RRP. Later macro/liquidity corrections remain excluded and total context stays <=28,000 characters.
- Final project Ruff, changed-Python AST syntax and staged whitespace checks pass. No repository dependency changes. A separate workspace verification environment contains the existing declared dependencies; Windows blocked the editable-package build's long temporary path, so dependency wheels were installed separately and the checkout imported directly. The redundant installer was stopped. Existing tools source files were not edited.
- Main implementation files: tradingagents/information/event_intelligence.py; existing claim_lifecycle.py, narrative_events.py and polling.py. Tests: test_event_intelligence.py and combined actual-graph fixture in test_graph_end_to_end.py. Handoff, coverage matrix, architecture and living status updated. No new source endpoint or live database.
- Fresh remote recheck remains 82c6ba6e4abc209dee605cda1b05ef74fc23dd2e; no push. Local implementation will be committed after these checks; its hash is reported in the session result to avoid a self-referential commit hash in this file.
