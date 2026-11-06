# C2-B bounded Kraken BTC/USD integration — November 6, 2026

Working public adapter, private canonical receipts and derived analyst context.
Phase 3 remains IN_PROGRESS. Local development only; no push or trading.

## Scope and source decision

The current user explicitly supersedes the earlier rights-only stop and
authorizes one bounded production acquisition after backup and validation.
Read the adopted workspace revised v1.1 Blueprint, Master Prompt, Resource
Manifest, C1 handoff, C2-A contracts/rights findings and SECURE_EXECUTION.
Earlier C2/C2-A BLOCKED reports describe their historical authorization and
assessment; they are not a finding that this personal public-API use is banned.

Kraken is selected for ordinary bounded personal/private research using its
official anonymous Spot REST API. This is a scoped engineering assessment,
not an express exchange AI licence or legal determination. Its official
[market-data guidance](https://blog.kraken.com/product/api/unlocked-3-the-market-data-feeds-systematic-traders-use)
describes public book, trade-history, OHLCV and ticker feeds for strategy research
and backtesting. [Terms section 8](https://www.kraken.com/legal/global-terms)
allows content use for one's own benefit; section 9 has broad automation and
third-party restrictions. Reading those alongside the intentionally automated
public API supports this limited private API workflow in our assessment; it
does not establish unlimited storage, redistribution, commercial data products,
model training, or unrestricted third-party payload processing rights.

Source metadata's `permitted` flags are operational decisions with this basis,
scope and date, not claims of separately granted contractual rights. Raw payloads,
books, individual executions and their receipts remain private/local. Only
allowlisted scalar derived metrics enter the model-facing context, solely for
this private inference workflow. Transformation itself is not a licence.
No raw-data export or model training is enabled. Reassess on an actual terms,
use-case or technical restriction change, rather than repeat speculative reviews.

Price, OHLCV, depth and executions are separate interfaces. This slice acquires
ticker price, depth and executions; it does not add or fetch OHLCV and does not
relabel USD as USDT or modify the existing candle collector.

## Implemented acquisition

`python -m tradingagents.information.kraken_spot` is disabled without explicit
`--allow-canonical-write`. It selects the existing active authority through
`runtime_store_path`, requires a new private backup, and takes the shared
collector lock. SQLite's online backup API precedes market acquisition/writes;
full integrity, foreign-key and application-reference validation must match.
Before/after checks require every original row to remain byte-for-byte present.
No production migration, alternative production store or scheduler is added.

Exactly four fixed HTTPS GETs per successful invocation:

1. `AssetPairs?pair=XBTUSD` validates internal `XXBTZUSD`, base `XXBT`, quote
   `ZUSD`, altname `XBTUSD`, display `XBT/USD`, online status and entry precision.
2. `Ticker?pair=XBTUSD` obtains the reported last price (`c[0]`); exchange event
   time remains unknown. This is a sampled last price, not a candle or new trade.
3. `Depth?pair=XBTUSD&count=10` retains up to ten aggregated L2 levels per side.
4. `Trades?pair=XBTUSD&count=20` retains up to twenty recent executions with
   required venue IDs and the opaque `last` cursor. No pagination or backfill.

The [official depth contract](https://docs.kraken.com/api-reference/market-data/get-order-book)
defines aggregated L2 quantities and limits 1–500; the
[trade contract](https://docs.kraken.com/api-reference/market-data/get-recent-trades)
allows 1–1000. [Public rate guidance](https://support.kraken.com/articles/206548367-what-are-the-api-rate-limits-)
says one request/second or less. This client spaces request starts at least
1.1 seconds, permits only four calls, caps decoded responses at 256 KiB each,
uses 5-second connection/10-second read timeouts and checks elapsed streaming
time against 20 seconds between chunks. A blocked read can extend that check
by its read timeout. TLS verification remains on; no credentials, retries,
redirects, alternate hosts, paid service or access-control workaround.
Non-200 responses, API errors, malformed data and exhausted bounds stop the run.
Acquisition/parser failures occur before evidence writes; the validated backup
remains. Such failed attempts currently do not append canonical failure receipts;
retain the invocation error locally. Existing generic C2 disconnect ingestion
and subsequent successful-run sampling-gap accounting remain available.

JSON numbers use Decimal. Price/quantity strings remain exact; padded REST
decimals are not incorrectly rejected using order-entry tick precision.
Metadata reports price entry precision 1 / lot precision 8; actual retained wire
values use venue formatting. Canonical wire precision is explicitly unknown
rather than inventing an exact tick precision for all reported quantities.
Trade `b`/`s` is retained as reported buy/sell. Aggressor is UNKNOWN because
this REST contract does not unambiguously define aggressor semantics.
Granularity also remains UNKNOWN; an execution is not claimed to identify an
individual order/participant. Exact duplicate IDs within a response collapse;
conflicting duplicates reject it. Trade-ID jumps never manufacture trades/gaps.

## Persistence, timing and export

Reuse `spot-microstructure-v1`, canonical observations/source history/coverage/gaps.
Add four immutable `spot.private.wire.receipt` observations with exact response
text, URL, hash and local receipt time, plus one `spot.price.sample`. Wire records
have `local_only` export and private evidence-history retention, with no automatic
deletion. Store them and backups outside Git, protected like the canonical DB.
Book/trade evidence and normalized receipts link their original private wire
receipt via `raw_reference`. Repeated identical receipts/run replays are idempotent;
venue trade IDs deduplicate across new runs. Reusing a run with changed responses
rejects before writes. The CLI refuses reacquisition under an already stored run
ID before transport. Local receive-clock rollback rejects before writes.

Per-level book update times are retained in raw receipts, not fabricated into
a snapshot timestamp. Trade timestamps are untrusted exchange times, parsed
exactly and truncated explicitly to microseconds. Local received/first-seen and
conservative availability drive PIT; exchange times cannot backdate visibility.
Old/future exchange clocks remain visible through receipt diagnostics and derived
trade freshness/skew. Book receipt freshness does not certify every resting order
was recently updated. No sequence or continuous-book reconstruction is claimed.

The existing consumer emits compact price/spread, retained depth/imbalance and
recent-sample execution count/base volume/VWAP. It does not serialize levels,
individual trade records or raw payloads. Evidence IDs and receipt/availability
times remain traceable locally. Existing WORLD/C1, funding and macro reservations
are preserved; narrative <=6,000 and prompts <=28,000 characters.

Writes are append-only batches (raw/price, depth, trades), not one all-or-nothing
multi-batch transaction. An exceptional persistence failure may retain partial
new history. Preserve both files and inspect; never silently restore over them.
Rollback: stop every writer, validate the named pre-acquisition backup, preserve
the failed/current database and SQLite sidecars, then use a reviewed SQLite
restore to the exact active canonical path. No automatic rollback or alternate
authority activation is performed.

## Verification and production result

Synthetic fixtures are in a new test module;
all existing frozen fixtures and synced sources remain read-only. Actual live
wire responses remain outside the repository. Scripted graph runs mock models
and vendors and deny socket/DNS/requests/curl networking; they validate wiring,
PIT and prompt contents, not model quality, forecasts or trading returns.

Initial checkout: `6b9a8a127a16e2666271dfb3fbe816431ccfa524` on
`phase-3-event-narrative-slice`. Read-only remote verification: feature
`0a2a06fcf43251795bdddde3c7b5407e7cab5069`, main
`1394a3f72aa4393e1a98f51b382434c4b4c2d972`. No fetch/push/merge/rebase/force.
Existing `.phase12-tools/` and untracked diagnosis preserved.

Canonical path:
`C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\information.sqlite3`.
Starting counts: 1,291 observations /146 source histories /171 coverage /0 gaps.
Starting SHA256:
`ea3739b621e02f188b0f19c45203ba29e632bcd8464679b2cd214140874800f2`.
Preflight SQLite-consistent backup: `local-runtime/backups/c2b-before-20261106.sqlite3`;
SHA256 `d09b2abe0d6f8e8451ea73118140987e56f0aefc302d48d91f9073cde83c9fe1`.
Backup file hash differs because SQLite backup reconstructs pages; all four
logical row digests, counts and semantic integrity checks match the original.

SECURE_EXECUTION followed: small auditable commands/direct patches, existing
reviewed Python environment, no downloads, Defender changes, exclusions,
policy persistence or bypass. Historical severe detection remains unresolved.
No new tool-reported security block was observed; that is not a Defender audit.

## Completed live result

One production acquisition `c2b-manual-20261106` completed. Four real public
responses were received at the following UTC times on 2026-11-06 (add seven hours
for Asia/Saigon): metadata 07:52:06.307330, ticker 07:52:07.159869,
depth 07:52:08.288629, executions 07:52:09.480647. These are observed live
responses, not documentation examples or synthetic market prices.

Retained: ten ordered uncrossed bids and ten asks; twenty executions; one
ticker last-price observation; four complete private wire receipts; two
normalized C2 receipts. No new trade is inferred from ticker/book changes.
Compact sample metrics: last ticker USD 75,543.8/BTC, spread USD 0.1,
retained bid/ask depth 3.457/0.266 BTC, twenty-execution sample volume
0.04061508 BTC and sample VWAP USD 75,549.3255980291/BTC. These are observations
at that sample, not a current quote or trading recommendation.

| Canonical table | Before | After | Added |
| --- | ---: | ---: | ---: |
| observations | 1291 | 1319 | 28 |
| source_definitions | 146 | 148 | 2 |
| coverage | 171 | 173 | 2 |
| data_gaps | 0 | 0 | 0 |

No prior C2 sampling interval existed in this production store. Zero gap rows
does not establish continuous collection; both samples have UNKNOWN completeness.
All original rows and schema remain unchanged; SQLite integrity, SQL foreign
keys, application references and source boundaries pass. Existing 114
supersession links and 871 content versions remain intact; source count 25 ->26.

After SHA256:
`1469142d87792fa61e0603f3012e6ba253a1fb7408b075e6a096afb7ea14384c`.
Immediate pre-write backup: `local-runtime/backups/c2b-manual-20261106.sqlite3`,
SHA256 `d09b2abe0d6f8e8451ea73118140987e56f0aefc302d48d91f9073cde83c9fe1`.
Both backups match the pre-acquisition logical rows and validation exactly.
Raw response SHA256 and URLs are retained in canonical receipts; none of the raw
payloads is committed or transmitted to a third-party model.

Actual `TradingAgentsGraph.propagate` on the canonical production history used
scripted models with all socket/DNS/requests/curl networking denied. New C2 IDs
were absent at 07:52:06.307329 UTC; at 07:52:09.480647 UTC both derived packets
reached Market Analyst with existing five selected WORLD IDs, C1 candidate
context, funding and macro sections. Each of the 28 new observations was also
checked immediately before and at its own recorded availability boundary.

Market Analyst's book evidence ID (received/available 07:52:08.288629 UTC):
`c2-evidence:69d69997a4532d7d459be36fe8b925c1e94abc439e87c295208375f804c50f14`.
Its trade-aggregate representative ID (received/available 07:52:09.480647 UTC):
`c2-evidence:fbd1f3250590ba527e808a9980fe6169e9512a7f0a3d113fdc37f35788b27dba`.
The local normalized receipt references all twenty executions; one selected ID
does not mean only one execution was aggregated.

| Canonical graph cutoff UTC | Narrative | Combined context | Largest model prompt |
| --- | ---: | ---: | ---: |
| Nov 6 07:52:06.307329 | 5430 | 15449 | 22961 |
| Nov 6 07:52:09.480647 | 5430 | 16631 | 24143 |
| Nov 5 03:27:10.527275 | 5744 | 15810 | 23418 |
| Nov 5 03:27:26.528491 | 5429 | 15441 | 23049 |
| Nov 6 02:38:10.235518 | 5429 | 15441 | 22953 |
| Nov 6 02:38:29.353157 | 5429 | 15448 | 22960 |

Final focused: **67 passed**. Final full offline: **1765 passed +99 subtests**,
four existing skips, one integration deselected and twenty existing warnings.
Lint and whitespace checks pass. All **70 historical cutoff views, 11 earlier
Nov5/Nov6 boundaries and 1707 protected-file hashes** pass. Final code's actual
production receipts replayed in a disposable SQLite-consistent clone with zero
row changes, four verified raw hashes and all private raw-reference links valid.
Production remained unchanged by verification and disposable replay.

Before production, an isolated real-response test and a disposable combined
canonical-history graph test also passed. One earlier live probe parsed its
responses but the operational store guard correctly refused creation of a new
isolated database under the active authority. Its responses were discarded;
the corrected test isolated authority only in its own process. No operational
authority file was changed. Initial endpoint DNS failed under restricted network;
the requested network grant resolved that technical issue. There was no
provider rejection or access-control bypass. Across investigation and validation:
one successful metadata-only check, two four-request probes, and exactly one
four-request production acquisition. No automatic retry loop ran.

Manual reuse: invoke the module with the existing canonical `--store`, a NEW
absolute private `--backup` path, a NEW unique `--run-id` and
`--allow-canonical-write`. Existing run IDs/backups are deliberately refused
before a fresh acquisition. No scheduler is registered. Evidence becomes stale
after its configured 120-second threshold; further freshness requires another
explicit manual run. This checkpoint establishes working bounded acquisition
and analyst wiring, not Phase 3 completion or any trading capability.
