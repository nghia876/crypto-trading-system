# C2-A source-independent BTC spot evidence — November 6, 2026

**Offline contracts VERIFIED; Kraken/Bitstamp acquisition BLOCKED. Phase 3
IN_PROGRESS. Local only. No production migration or collection.**

## Verified starting state and boundaries

Existing checkout `nghia876/crypto-trading-system`, branch
`phase-3-event-narrative-slice`, initial HEAD
`004d698c31fe554ce16d9f9c127dd7005f748c39`, following C1
`7077df64003cf1beb0583092ab2efcf58712d19a`. Tracked files/staging were clean.
Existing untracked `.phase12-tools/` and bottleneck diagnosis were preserved.
Origin is the expected HTTPS repository. Remote feature `0a2a06f...` remains a
historical supplied confirmation, not a freshly checked remote reference.
No fetch/push/merge/rebase/force or main operation.

Consulted adopted workspace revised v1.1 Product Blueprint, Master Prompt and
Resource Manifest, C1/C2 handoffs, secure-execution guidance, project status,
source coverage/rights matrix and actual store, authority, observations,
source/health, market-state, consumer and Market Analyst/graph wiring.
Synced `sources/` and frozen reference material remain read-only.

## Contract and persistence design

`spot_microstructure.py` adds schema `spot-microstructure-v1`, reusing existing
`Observation`, `Source`, `MarketDataBatch`, `CoverageRecord`, `MarketDataGap`
and `SQLiteInformationStore`. No table or schema alteration is needed.
The canonical tables remain `observations`, `source_definitions`, `coverage`
and `data_gaps`; disposable tests exercise the same implementation.

- `spot.depth.sample`: best-first unique bids (descending) and asks (ascending),
  exact price/size decimal strings, venue/symbol, BTC spot, base/quote units,
  declared or unknown precision, optional snapshot ID and nonnegative sequence.
  Each side accepts at most 500 levels, retains the configured 1–500 cap and
  records pre-cap counts. Spread and retained base depth use decimal arithmetic
  with sufficient precision. USD and USDT are labeled separately.
- Crossed/locked/one-sided/empty books are retained as LOW-quality invalid
  evidence, explicitly labeled in context. They never become a valid book.
  Invalid decimal syntax, binary floats, nonfinite/exponent values, negative or
  zero sizes, excess precision, duplicate/unordered prices and oversized inputs
  reject the entire response before persistence. This is sampled resting depth,
  not continuous L2, order cancellations or evidence of executed volume.
- `spot.executed_trade`: required venue trade ID, positive price/quantity,
  exchange time or null, reported side, normalized aggressor side and semantic
  definition, plus `raw`/`aggregated`/`unknown` granularity. Without an explicit
  provider definition, normalized aggressor remains UNKNOWN. No venue adapter
  currently supplies such a definition. Missing trade IDs reject the input;
  duplicate IDs inside one response reject ambiguous adapter output.
- `spot.microstructure.receipt`: immutable local attempt identity, config and
  normalized-response hashes, evidence IDs, duplicate count, receive time,
  sequence/reversal, opaque cursor, reported continuity gap, exchange ages/skew,
  and transport failure. No raw exchange response is stored or represented as
  observed data. Every fixture is SYNTHETIC.
- Logical identities are qualified by source/venue/symbol/kind and trade ID or
  snapshot ID. Without a snapshot ID, the local receipt identifies that sample.
  Repeating an identical receipt within source/config/kind is idempotent; changed
  data/time under that identity collides. A changed config is a separate namespace.
  A later receipt with identical identified content retains the original evidence
  ID and availability while adding its own receipt/coverage. Changed content,
  including reversion to an earlier value, creates a new immutable version using
  the existing store's supersession contract. Conflicting identity content at the
  same receive instant is rejected. Identity conflicts remain visibly qualified.
- Exchange time is nullable and untrusted in payload `exchange_event_at`.
  Payload `received_at`, envelope `retrieved_at`, logical identity `first_seen_time`
  and computed `available_at` are distinct. The legacy required `event_time`
  envelope field is explicitly a **local identity anchor**, never an invented
  exchange occurrence. PIT uses local receipt/first-known bounds; exchange clocks
  never backdate evidence. Local receive-clock rollback is rejected.
- Source history and coverage are appended with every new receipt. Success means
  sampled UNKNOWN completeness, invalid books LOW_QUALITY, disconnect UNAVAILABLE.
  More than twice the configured expected interval records an unobserved sampling
  interval; explicit provider gaps and disconnects add gap records. Trade ID jumps
  never imply a numeric count of missing executions. Zero gaps never proves
  continuous coverage. Failure does not imply zero trading.

The pure `normalize_spot_response` parser needs no connection or permission
assertion. Ingestion and the injected one-attempt `fetch_spot_once` seam require
an explicitly enabled/configured venue and exact `permitted` metadata for
collection, private durable retention, internal AI inference and third-party
processing, plus free access, rights reference and assessment date. UNKNOWN,
denied and truthy substitutes fail before transport or writes. Redistribution
is a separate recorded attribute and is not enabled by inference permission.
`ENABLED_VENUES` is empty. There is no HTTP client, exchange wire adapter, CLI,
scheduler, production configuration, key or external provider registration.
The injected transport is for mocked tests; a future real transport must enforce
exact reviewed endpoint, byte/time/rate/access-policy limits separately.

## Analyst context and replay

The existing consumer renders at most four deterministic whole C2 evidence
records into its existing Signals reservation and prioritizes their coverage
and evidence metadata. WORLD/narrative (6,000), macro/liquidity and derivatives
reservations are unchanged. The combined context remains <=28,000 characters;
tests also check every actual model prompt <=28,000. With no C2 rows, historical
context stays unchanged. Selection uses local receipt availability, not exchange
chronology, and checks source rights as of the cutoff. Same-time conflicting
rights definitions fail closed. Stale/invalid/identity-conflict/reversed-sequence
state, latest transport failure and recorded gaps remain explicit.

This is descriptive evidence only. No trade imbalance, causal inference,
whale/participant identity, directional score, scenario or trading signal.
Latest-trade context is a sample, not a complete tape or flow aggregate.

## Offline verification

Final C2 focused: **48 passed**. Full offline: **1,746 passed +99 subtests**,
four existing skips, one integration deselected, 20 existing warnings.
Test authority isolation uses the previously reviewed private
`visibility_tests.py`; no installation-authority file is changed. Ruff and
AST syntax pass for the three Python files; Git whitespace/diff checks pass.

Synthetic disposable evidence counts, asserted independently:

| Fixture | Evidence | Receipts | SQLite observations | Coverage | Gaps |
| --- | ---: | ---: | ---: | ---: | ---: |
| Same identified snapshot after restart/repeated fetch | 1 | 2 | 3 | 2 | 0 |
| Trade repeat, empty batch, ID jump and disconnect | 2 | 5 | 7 | 5 | 2 |

The snapshot fixture also asserts two persisted source-history rows. No count
in this table is observed exchange evidence or production data.

Coverage includes decimals through 24 integer/18 fractional digits without
rounding, precision errors, negative sizes, crossed/empty/locked books, level
caps, explicit units/unknown precision, future/old/missing exchange clocks, rollback,
sequence reversal, identity collisions/reversions, receipt/cursor collisions,
duplicate/missing IDs, missing trades/unknown completeness, provider-reported
gaps, outages, restart, rights denial/revocation/conflict, and exact PIT cutoffs.

Actual `TradingAgentsGraph.propagate` runs use scripted models, mocked vendors
and denied socket/DNS/requests/curl network. Before C2 availability, new IDs are
absent; at availability, both new C2 IDs reach Market Analyst alongside both
synthetic WORLD publishers, C1 narrative headers and funding/macro context.

| Synthetic UTC cutoff | Narrative chars | Mixed chars | Largest prompt |
| --- | ---: | ---: | ---: |
| Nov 5 03:27:59.999999 | 4,027 | 9,390 | 16,998 |
| Nov 5 03:28:00 | 5,438 | 13,113 | 20,714 |

Read-only historical preservation: **70 cutoff views +11 Nov5/Nov6 boundaries**
match, and all **1,707 protected-file hashes** match C1 baseline. Four actual
historical graph replays retain narrative/mixed/largest prompt sizes:
5744/15810/23418, 5429/15441/23049, 5429/15441/22953 and
5429/15448/22960. Political/C1 visibility regressions pass in the full suite.
Scripted output does not validate model quality, predictions or trading returns.

## Source rights and next step

The [dated official-source investigation](C2A_RIGHTS_RESEARCH_20261106.md)
records exact prospective Kraken/Bitstamp endpoints, fields, limits, short
quotes and rights separately. Kraken's October 30 terms/API exception remains
unresolved; Bitstamp's public API describes a commercial data licence and
substantive legal text could not be retrieved. Private durable retention,
internal AI and third-party processing remain UNKNOWN for both. Both BLOCKED;
no live calls or unlicensed storage. Technical documentation is not permission.

Next prerequisite: free applicable official licence/clarification for one exact
venue/pair and the four required uses, with redistribution addressed separately.
Then implement its bounded adapter/transport and offline endpoint fixtures;
only a separately authorized tightly bounded live probe could follow. No eligible
live-source step is currently executable. Paid access/servers/schedulers remain
outside scope. No Phase 4 advancement or Phase 3 exit claim.

## Production preservation and security

Production was accessed read-only at the existing absolute private authority:
`C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\information.sqlite3`.
Before/after counts remain **1,291 observations, 146 source histories,
171 coverage, 0 gaps**; integrity `ok`, foreign-key/application-reference checks
pass, four row digests unchanged, 114 supersession links and 871 content versions.
SHA256 remains:
`ea3739b621e02f188b0f19c45203ba29e632bcd8464679b2cd214140874800f2`.

No production writer/migration or alternate operational DB was used. No source
mirror, frozen fixture, authority configuration, tools or diagnosis was changed.
No downloads/installers, credential use, Defender exclusions, execution-policy
changes or bypass. Small commands and direct patches were used. Historical
`Ransom:PowerShell/FileFix.DZ!MTB` remains unresolved; no new tool-reported block
was observed, which is not a Defender audit or a false-positive determination.
Scoped validated code/tests/docs are committed locally only; the final Work
report supplies the commit SHA rather than embedding it into its own content.

Limitations: normalized inputs are not provider wire parsers; exact live metadata,
side semantics, endpoint reachability and rights remain unverified. Ingestion is
serialized per source and scans canonical history, suitable for bounded offline
validation, not a verified high-volume/concurrent collector. The rights gate
enforces supplied reviewed attributes; it cannot itself establish legal rights.
