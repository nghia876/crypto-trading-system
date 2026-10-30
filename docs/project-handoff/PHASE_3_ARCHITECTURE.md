# Binding Phase 3 scope clarification and roadmap — 2026-10-30

This clarifies the existing product vision and Phase 3, not a new top-level phase. Read the [living checkpoint](../project-settings/PROJECT_STATUS_AND_PHASE_2_HANDOFF.md) for current state and constraints. The first-slice design below is historical and deliberately narrower than the full product.

## Product and discovery contract

One integrated TradingAgents repo, BTC-first, one canonical SQLite provenance/replay store, free-only legally eligible acquisition. The full product joins information, market/world state, critical causal/regime reasoning, conditional scenarios, deterministic risk, execution simulation, PIT evaluation and learning. Scope is not proof of implementation or profitability.

Phase 3 continuously discovers WORLD events independently of domain-to-BTC relevance: wars/conflicts; sanctions/trade; drought, floods, wildfires, storms and water scarcity; agriculture/crop and food supply disruptions; energy/oil/gas/electric grid/infrastructure; pandemics/public health events; technology breakthroughs/AI/chips; cybersecurity; geopolitics; regulation; and crypto. Discovery requires neither BTC keywords nor observed price moves. Relevance assessment and anomaly-triggered deeper research follow discovery.

Combine broad global/regional reporting with specialized environmental, agricultural, energy, disaster, health, science, cyber and official sources. Generic headline search and financial release feeds alone are insufficient. The [coverage matrix](SOURCE_COVERAGE_MATRIX.md) owns detailed source-family/metric gaps. Candidates require access/rights, latency, region/language, revision and PIT validation before operational use; naming a domain does not establish a collector.

## Next implementation priorities and phase boundaries

| Workstream | Scope / boundary | State at this clarification |
|---|---|---|
| M2A — next implementation task | Narrow structured economic/macroeconomic restoration after default FRED disablement: Fed H.4.1 assets/reserves/TGA, NY Fed ON RRP, Treasury daily TGA, BLS CPI/employment, Treasury yields, BEA GDP/PCE. Use eligible free original publishers and existing store/contracts, units, release/first-seen/retrieval timestamps, append-only revisions, provenance and explicit missing/stale reporting. See [eligibility](MACRO_SOURCE_ELIGIBILITY.md) and [sequence](NEXT_GITHUB_CANONICAL_STORE.md). | NOT STARTED; source review and existing direct Treasury support are not completed replacement coverage. |
| Phase 3 world-radar expansion — explicit next workstream | Expand specialized environmental/agricultural/energy/disaster and other global sources alongside broad discovery; close matrix gaps and rights/live gates. Existing Phase 3 obligation, separate from narrow M2A and not deferred to Phase 4. | Required; specialized breadth and operational coverage NOT YET PROVEN. |
| M2B-D — separate market-data backlog | BTC microstructure/multi-venue, derivatives/options, on-chain, institutional/stablecoin flows and related cross-asset/expectations gaps. Distinct from M2A and world discovery. Exact B/C/D allocation and acceptance slices must be verified/agreed before implementation; this clarification does not invent completed milestones. | Remaining matrix gaps; no new implementation here. |
| Phase 3 M3 evaluation | Measure provenance/origin, correlation/confirmation quality, latency, omissions and market-reaction alignment. Never gate discovery on price moves or count syndication as independent evidence. | Later evaluation against acquired PIT evidence. |
| Phase 4 — World Model + Regime | Test transmission mechanisms, competing hypotheses and counterevidence: e.g. drought -> crops/food -> inflation/policy, or energy disruption -> costs/growth/liquidity -> conditional BTC exposure. Challenge each link, timing, confounders and already-priced-in alternatives; allow unknown/no material effect. | Later reasoning, not automatic bullish/bearish event labels. |

Acceptance for expansion requires domain-specific discovery examples without BTC/price gates, explicit source/metric coverage and missingness, conservative publication/first-seen availability, immutable revisions, same-store reopen/replay and analyst lineage. Domain/region omissions, uncertain event times and source dependence remain visible. Offline fixtures, sampled downloads and source health alone cannot certify complete or continuous world coverage.

# Phase 3 first slice: event and narrative contracts

Date: 2026-10-27 (Asia/Saigon). Decision: accepted for this bounded slice.

## Baseline and product alignment

Verified local Phase 2 branch `phase-1.2-btc-ohlcv-collector` at
`22b804066284dd80557af16c1aa8193271feb43f`, tracked tree clean, only
`.phase12-tools/` untracked. GitHub connector queried the feature branch and
returned `7cb739d0af0fd7d0dd1b398b4c7bf66099bcbdea`; local baseline is six commits
ahead by ancestry. Direct git remote query failed with a network lookup error.
No push. Phase 3 branch is `phase-3-event-narrative-slice`, from the local baseline.
The current user explicitly authorizes local Phase 3 despite the older handoff's
remote-storage prerequisite. Remote durability remains incomplete.

Canonical references read: read-only project `sources/PRODUCT_BLUEPRINT.md`,
`MASTER_PROMPT.md`, `RESOURCE_MANIFEST.md`; repository Phase 2 handoff and status.
Their old Phase 0 startup descriptions are superseded by executable repository evidence.
The referenced chat could not be retrieved (Cloudflare challenge); the current
user's detailed scope is the authority for this session.

This implements a seam in C05/C06/C07, feeding existing C08/analyst context. The
product remains BTC macro narrative plus micro market-state reasoning, with
critical evidence evaluation, contradictions, later world/regime models,
conditional scenarios, deterministic risk, execution, replay and learning.
This slice does not implement those later layers or claim alpha.

## Architecture and contracts

Public official RSS -> bounded parser -> versioned Observation/MarketDataBatch ->
existing append-only SQLite store -> one InformationView at T -> deterministic
event grouping -> budgeted analyst context -> existing Market Analyst graph.
No anomaly trigger is required to call the radar. Poll scheduling is a later milestone.
No database migration or new required graph setting; optional-store behavior stays intact.

| Contract | Semantics |
|---|---|
| Event identity | SHA-256 prefix of canonical official release URL; publisher-specific, not a global story identity. Query/fragment stripped. Different release URLs remain distinct. |
| Version identity | Event + normalized claim hash + publication + local retrieval timestamp. Exact duplicate feed entries collapse; repeated polls are retained as observations but group into one event. |
| Source | Persisted Source definition with endpoint, method, timing, limits, official-primary credibility and one publisher group. Credibility is provenance, not measured accuracy. |
| Event time | Actual occurrence UNKNOWN. Envelope uses explicitly labeled publication proxy, never a claimed policy-effective or meeting time. |
| Published | RSS pubDate, timezone required; malformed item fails the snapshot atomically. |
| Observed/ingested | Local retrieval completion; conservative first-seen for that copy. Store preserves all copies, so earlier polls remain replayable. |
| Available | Existing envelope max(publication, first-seen, retrieval); never historical publication alone. Future-dated entries stay hidden until this bound. |
| Confirmed/reaction | Null/UNKNOWN in this slice; official reporting is not independent fact verification or reaction detection. |
| Claims/facts | Headline is a source-reported claim. Verified facts empty; no semantic extraction or numeric policy assertion. |
| Independence | Same Federal Reserve publisher group, including cross-posts; count of links/polls never increases corroboration. Second independent publisher deferred until claim-level origin/dependency mapping exists. |
| Contradictions | Empty list with explicit not_performed search state, never 'no contradictions'. Later edges must identify claim, opposing evidence IDs and availability. |
| Lifecycle | This adapter emits only officially_reported. Proposed broader states: candidate, unconfirmed, independently_confirmed, officially_reported, contradicted, stale, resolved. Each future transition must be a new available observation with supporting IDs; no mutable historical status. |
| Correlation | Same official canonical URL groups copies/updates; no heuristic title merge across announcements or inferred calendar matching. Recent events render alongside existing macro/calendar/micro evidence at the same cutoff. |
| Lineage | Evidence observation ID, original URL, parser transformation/version, source definition, schema/unit and timestamps remain in the store/context. |
| Coverage | Nonempty feed PRESENT only for observed records; empty feed UNKNOWN. Never complete, negative evidence, or no-event proof. Network/parser failures raise; caller must record failures separately. |
| Replay | Filter availability before latest-version grouping; corrections cannot replace prior views before local observation. Deterministic timestamp/ID tie-break; simultaneous conflicting versions have no semantic resolution. |

## Selection and boundaries

Selected Federal Reserve monetary-policy RSS: public, no key, official macro
announcements relevant to the BTC research universe, feasible structured timestamps.
Official directory: https://www.federalreserve.gov/feeds/feeds.htm . Feed:
https://www.federalreserve.gov/feeds/press_monetary.xml . Directory was inspected
through web search; direct web feed open rejected XML content type. No successful
live collector check is claimed. Fixtures exercise protocol shape, not provider reliability.
Alternatives: general news aggregator (broader but ambiguous provenance and syndication),
full-page crawling (more facts but larger extraction/revision surface), second Fed
channel (same publisher, not independent). Chosen narrow primary-source seam is
explicitly extensible without inventing independent confirmation.

Input limits: 2 MB response, 200 items, 2,000-character headline, bounded streaming
read and network timeouts; reject DTD. No source execution or model-directed tool use.
The total information-context bound remains 28,000 characters, with a reserved
4,000-character narrative section and whole-record omission counts. Other sections
retain reserved space; omissions mean unknown. This is not a token bound or whole
conversation size bound. Store/replay history can grow; retention/indexing is later work.

## Acceptance and next milestones

First-slice acceptance: deterministic parsing and identity; immutable persisted
versions; no visibility before local/publication availability; update replay;
empty/invalid/oversize/failing source behavior; whole-record bounded prompt;
real graph Market Analyst inclusion and exclusion of future corrections;
optional-store backwards compatibility and broader offline regression checks.
Verification results are recorded in PHASE_3_HANDOFF.md after execution.

Next: live feed shape validation and operational failure/coverage records; durable
poll scheduling and latency measurement; second independently sourced claim adapter
with origin/dependency mapping; append-only confirmation/contradiction lifecycle
and calendar linkage; temporal market-reaction controls and evaluation. Only then
advance to later world/regime reasoning. No phase-wide completion is claimed.
