# Phase 3.2A: Broad News Acquisition and Replay

Date: 2026-10-27 (Asia/Saigon). Scope: locally verified acquisition/replay slice;
Phase 3 remains IN_PROGRESS. This supplements PHASE_3_HANDOFF.md and supersedes
its deferred broad discovery / poll outcome / intraday entry items.

## Preservation and authority

Starting branch `phase-3-event-narrative-slice`; HEAD
`ef4f56c9f1cf65dc0fe9fe819a3f3646dd7f7169`; tracked tree clean; only pre-existing
`.phase12-tools/` untracked. Work stays on that branch. No switch to or modification
of main, push, merge, reset, source-file edits, or staging of `.phase12-tools/`.
Canonical read-only PRODUCT_BLUEPRINT, MASTER_PROMPT, RESOURCE_MANIFEST and repository
Phase 2/3 handoffs were read. The referenced Phase 3 chat was retrieved, but its
assistant responses are opaque content references; no readable approved plan or
uploaded result was recovered. The current user's explicit implementation scope
is the authoritative implementation specification.

## Implemented and integrated

- `information/sources.py`: frozen, validated, versioned NewsDiscoveryConfig;
  BBC world/technology RSS and GDELT war/geopolitics + technology queries. No BTC
  keywords, price movement, instrument, analyst, or financial gate. Each request
  fingerprints its source, domain, query, parser format and bounds. Configured
  source definitions persist those fields even for empty/failing polls.
- `information/news.py`: RSS 2 and Atom parsing, GDELT JSON article discovery;
  max 2 MB, configurable max 250 items (defaults 100), 2,000-character headlines,
  4,096-character article URLs; reject DTD/entities, malformed snapshots, excess
  items/bytes and redirects. UTF-8 only. Streaming reads with connect/read timeouts;
  one request per configured source, no automatic retries or article-body crawling.
- `poll_once` uses the existing SQLiteInformationStore, Observation, Transformation,
  MarketDataBatch, Source and CoverageRecord. At most 16 sources per invocation.
  Each source's observations + source configuration + outcome commit atomically.
  Success, empty and failure are durable; empty means UNKNOWN, never no events.
  Failure includes error class and HTTP status where provided, without exposing
  arbitrary remote exception text. Snapshot hash is retained when text was fetched.
- Caller-supplied poll ID + complete configuration fingerprint keys idempotency.
  Reopen/retry returns the recorded outcome without refetching, including failures;
  a new ID deliberately starts a new poll. Partial runs resume per source. This is
  a sequential caller API, not a distributed-worker exactly-once guarantee.
- Canonical article identity hashes URL with lowercase authority and no fragment.
  Every query parameter is retained: identity/signature/tracking queries are not
  silently stripped. Original and canonical URLs are both stored. Distinct tracked
  URLs may therefore remain distinct candidates. No inferred semantic story merge.
- Stable article version ID hashes article identity + headline/publication/update
  content hash. Acquisition observation IDs also include configuration and local
  retrieval time. Same content can retain its version ID across polls; each copy's
  acquisition provenance is immutable. Snapshot hashes cover decoded UTF-8 snapshot
  text; full raw response and article bodies are not archived.
- Publication and Atom update timestamps are source-reported; missing, malformed
  or timezone-naive values stay UNKNOWN with raw fields retained. GDELT seendate is
  discovery time, never publication or local first-seen. Future publication/update
  bounds prevent early visibility; update-before-publication is explicitly flagged.
  Event occurrence remains unknown with a labeled envelope proxy.
- Coordinator first_seen_time is earliest locally stored acquisition of canonical
  article across sources; retrieved_at identifies this copy. Direct parser output
  has snapshot-local first_seen_time until coordinated against durable history.
  Availability remains conservative max(local first seen, retrieval, publication,
  and reported news update time). Later corrections never appear in earlier replay.
- Existing Fed narrative-event-v1 remains supported alongside narrative-news-v1.
  Selection collapses exact canonical article overlap across RSS/GDELT into one
  candidate; source-specific history remains stored. All broad news is unconfirmed:
  origin, syndication, independence, confirmations, reaction and credibility are
  unknown/unmeasured; contradictions are unsearched. Repetition is never votes.
- Latest eligible canonical article versions feed deterministic domain round-robin
  selection, with whole-record fit and omission disclosures. Domain labels denote
  discovery requests, not verified topic classification. Existing total context
  stays <=28,000 characters; narrative section stays within its 4,000-character
  allocation. Selected narrative evidence IDs, schema/unit/availability metadata
  receive priority; metadata is based on actual selected records rather than the
  previous first-three approximation. Macro, calendar and micro reservations remain.
- `TradingAgentsGraph.propagate(..., decision_time=aware_datetime)` passes the cutoff
  through `_run_graph` and `create_run_state`. UTC date must match trade_date and
  future cutoffs are rejected. Date-only behavior remains unchanged. Stock behavior
  remains unchanged apart from explicit cutoff disclosure; BTC market-state context
  remains crypto-only. Explicit intraday checkpoint resume is rejected to prevent
  accidentally resuming an earlier cutoff. Legacy news/social/market tools and
  date-based memory do not enforce intraday PIT; actual prompts disclose this.

## Use within the existing system

```python
from tradingagents.information.news import poll_once
from tradingagents.information.store import SQLiteInformationStore

# Use the SAME path already configured as graph.config['information_store_path'].
store = SQLiteInformationStore(config['information_store_path'])
outcomes = poll_once(store, poll_id='caller-assigned-unique-poll-id')
# Reuse this ID only to resume/retry this exact logical poll.
# Later graph.propagate(..., asset_type='crypto', decision_time=aware_cutoff)
# reads eligible evidence from this same store; it does not acquire news.
```

Source public-access references checked (documentation, not collector validation):
[GDELT official API documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/),
[BBC feed directory / feed terms link](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm).
Public access does not grant blanket redistribution/business rights. These defaults
are for private research; BBC business reuse requires separate terms review. No
paid services, credentials, scheduler, parallel database or agent system added.

## Verification

Normal shared conftest and its no-network guard remain enabled.
- Initial retained-contract regression: 65 passed.
- Expanded focused suite (broad news, Fed, contract, store, context budget, actual
  graph): 91 passed in 8.99 s.
- Initial full offline suite: 1,382 passed, 99 subtests passed, 4 skipped,
  1 deselected, 20 warnings, 29.59 s.
- Final full default offline suite: **1,384 passed, 99 subtests passed, 4 skipped,
  1 deselected, 20 warnings, 35.43 s**. Skips: three POSIX file-mode tests on
  Windows and optional langchain_aws. Integration excluded by project defaults.
- Final Ruff check on all nine changed/new Python files, AST syntax parsing and
  git diff --check passed. Explicit-path diff reviewed before local commit.
- Tests include non-BTC war/technology, RSS/Atom, GDELT overlap and query bounds,
  date anomalies, unknown publication, malformed/oversized inputs, source errors,
  redirects, repeated polling, empty/failing outcome persistence, retries/reopen,
  corrections and changed publication time, out-of-order append, first-seen versus
  retrieved times, future-publication/update visibility, mixed Fed/news domain
  budget and precise selected metadata. Real graph prompt capture tests explicit
  historical intraday cutoff and a correction one microsecond later, crypto and
  stock compatibility; existing date-only graph and Phase 2 tests remain active.
- Controlled live adapter attempts at 2026-10-27 17:28 Asia/Saigon: one bounded
  request to each of the four default configurations; all failed ConnectionError.
  No successful live response, parser shape, persistence or availability verified.
  These live attempts were separate from offline mocked tests. No live corpus or
  second evidence database was created; no ongoing readiness claim.

## Limits and next milestone

Rolling discovery is incomplete (GDELT request window one day); source caps can
omit material or reject large feeds, and missed polling intervals are not healed.
No full article extraction, semantic event clustering, claim fact verification,
independence inference, contradiction search, confirmation lifecycle transitions,
market reaction timing/causality, full historical vintages, scheduler, continuous
latency monitoring, distributed coordination, world/regime model or alpha evidence.
The whole graph is not certified PIT: legacy tools and date-based memory remain
outside the replay store guarantee. Explicit intraday checkpoints are unsupported.

Next Phase 3 milestone: provenance-aware claim/event correlation and append-only
confirmation/contradiction lifecycle (proposed Phase 3.2B), preserving unknown
origin/dependency states until supported by evidence. Live endpoint shape and a
small prospective collection/replay evaluation remain necessary before operational
claims or reaction-timing evaluation. Continue toward the full blueprint's world,
regime, scenarios, deterministic risk, execution and learning layers in that order.
