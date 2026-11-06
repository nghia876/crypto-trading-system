# C2-C repeated real Kraken BTC/USD acquisition — November 6, 2026

**Bounded repeated acquisition and continuity VERIFIED. Live overlapping-trade case NOT OBSERVED. Phase 3 remains IN_PROGRESS.**

Existing repository `nghia876/crypto-trading-system`, feature branch `phase-3-event-narrative-slice`, starting HEAD `782bff5c084ac37a751e135c758ce8926e2854f2`. Initial tracked tree clean; existing untracked `.phase12-tools/` and diagnosis preserved. No push, fetch, main, merge, rebase or force operation. Remote references were not freshly checked.

Read adopted v1.1 revised Product Blueprint, Master Prompt, Resource Manifest, project status, SECURE_EXECUTION, C2 eligibility/contracts/rights history and C2-B handoff. The later approved C2-B private public-API assessment and current explicit C2-C authorization govern this scope. Existing source eligibility guard remains enabled; raw data remains private/local, with compact derived inference only. No express AI licence, redistribution or model training is claimed.

## Actual acquisition sessions

Two separate user-invoked process runs, four fixed HTTPS GETs each, no probes or retries. All eight responses were HTTP 200 with Kraken `error=[]`. TLS stayed enabled; redirects disabled, 256 KiB/response cap, existing timeouts and at least 1.1 seconds between request starts. Official [public rate guidance](https://support.kraken.com/articles/206548367-what-are-the-api-rate-limits-) and [depth](https://docs.kraken.com/api-reference/market-data/get-order-book)/[trades](https://docs.kraken.com/api-reference/market-data/get-recent-trades) contracts were rechecked.

UTC+07:00 is Asia/Bangkok and Asia/Saigon on this date. Times below are actual local process and receipt measurements; no fabricated exchange snapshot time.

### Run 1: `c2c-20261106-session01`

UTC: 2026-11-06T08:00:52.361898+00:00 → 2026-11-06T08:00:56.956028+00:00; elapsed **4.594130 seconds**.
Asia/Bangkok: 2026-11-06T15:00:52.361898+07:00 → 2026-11-06T15:00:56.956028+07:00.

| Endpoint | Actual received_at UTC | Status |
| --- | --- | --- |
| `https://api.kraken.com/0/public/AssetPairs?pair=XBTUSD` | 2026-11-06T08:00:53.102275+00:00 | HTTP 200; error=[] |
| `https://api.kraken.com/0/public/Ticker?pair=XBTUSD` | 2026-11-06T08:00:53.991724+00:00 | HTTP 200; error=[] |
| `https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=10` | 2026-11-06T08:00:55.311360+00:00 | HTTP 200; error=[] |
| `https://api.kraken.com/0/public/Trades?pair=XBTUSD&count=20` | 2026-11-06T08:00:56.335809+00:00 | HTTP 200; error=[] |

### Run 2: `c2c-20261106-session02`

UTC: 2026-11-06T08:02:12.878639+00:00 → 2026-11-06T08:02:17.441824+00:00; elapsed **4.563185 seconds**.
Asia/Bangkok: 2026-11-06T15:02:12.878639+07:00 → 2026-11-06T15:02:17.441824+07:00.

| Endpoint | Actual received_at UTC | Status |
| --- | --- | --- |
| `https://api.kraken.com/0/public/AssetPairs?pair=XBTUSD` | 2026-11-06T08:02:13.830526+00:00 | HTTP 200; error=[] |
| `https://api.kraken.com/0/public/Ticker?pair=XBTUSD` | 2026-11-06T08:02:14.570747+00:00 | HTTP 200; error=[] |
| `https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=10` | 2026-11-06T08:02:15.713029+00:00 | HTTP 200; error=[] |
| `https://api.kraken.com/0/public/Trades?pair=XBTUSD&count=20` | 2026-11-06T08:02:16.840725+00:00 | HTTP 200; error=[] |

Run 2 started **75.922611 seconds after Run 1 completed**. No service, timer, background poller or scheduler was installed.

The AssetPairs response content hash was unchanged across the two C2-C runs; ticker, depth and trades response hashes all changed. New receipt identities preserve each separate retrieval even when metadata content is unchanged. Exact URLs, wire hashes and private contents remain traceable in canonical receipts.

## Canonical persistence and identity

Canonical absolute path: `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\information.sqlite3`. Active authority independently resolved and matched. Initial hash/counts matched C2-B exactly before any write.

| Table | Before C2-C | After run 1 | After run 2 |
| --- | ---: | ---: | ---: |
| observations | 1319 | 1347 | 1375 |
| source_definitions | 148 | 150 | 152 |
| coverage | 173 | 175 | 177 |
| data_gaps | 0 | 2 | 2 |

Each run added 28 observations: four private raw response receipts, one ticker sample, one book snapshot, twenty new venue-ID execution records and two normalized receipts. Each added two source-history and two coverage records. No revisions or overwritten records. All original pre-C2 1,291 observations and the first C2-B 28 are preserved byte-for-byte, including all original source histories/coverage/gaps and schema. Existing 114 supersession links, 871 content versions and 26 source IDs remain.

Two gap rows were correctly added on run 1, one each for book/trades after the long C2-B interval. Run 2 did not exceed the configured gap threshold. This does not establish continuous coverage between the C2-C samples: all off intervals and missing executions are UNKNOWN.

| Sample | Venue execution IDs | New vs all prior samples | Overlap | Revisions | Within-response duplicate IDs |
| --- | --- | ---: | ---: | ---: | ---: |
| c2b-manual-20261106 | 114573860–114573879 (20 retained; range is not completeness) | 20 | 0 | 0 | 0 |
| c2c-20261106-session01 | 114574877–114574896 (20 retained; range is not completeness) | 20 | 0 | 0 | 0 |
| c2c-20261106-session02 | 114575032–114575051 (20 retained; range is not completeness) | 20 | 0 | 0 | 0 |

The two new samples have **zero live overlapping trade IDs**, including against C2-B: 20 new/0 unchanged/0 revised execution identities in each C2-C sample. No overlapping real-trade dedup success is invented. Existing isolated restart/overlap tests pass; all three actual stored run receipts also replay idempotently in a disposable clone with **zero row changes**. Overlap is not counted as new trading activity. Books lack venue snapshot IDs, so each independently received sample has a new local identity, even if levels match. Repeated receipt URLs do not measure narrative virality.

## Observed sampled market changes

- c2b-manual-20261106: ticker last price **75543.8 USD/BTC**; execution exchange-time window 2026-11-06T07:51:58.912459+00:00 → 2026-11-06T07:52:08.152580+00:00.
- c2c-20261106-session01: ticker last price **75468.4 USD/BTC**; execution exchange-time window 2026-11-06T08:00:51.382108+00:00 → 2026-11-06T08:00:55.101572+00:00.
  - c2-evidence:0c22130233ea631a71d8908632c5949e2bd451b12b63a6c852a6b076d26e2613: Kraken BTC/USD derived private research; last_sampled_price_USD=75468.4; spread_USD=0.1; sampled_depth_BTC=0.011/4.639; depth_imbalance=-0.9952688172043010752688172043; levels=10/10; integrity=ordered_uncrossed; received_at=2026-11-06T08:00:55.311360+00:00; available_at=2026-11-06T08:00:55.311360+00:00; stale=False; exchange clock untrusted; no predictive signal; raw data LOCAL ONLY
  - c2-evidence:f992068e0bce087f4f6ad4a848dbbb268436bf7a2baa8aba1927d89c56789c0b: Kraken BTC/USD derived private research; recent_sample_executions=20; volume_BTC=0.01472653; sample_VWAP_USD=75456.95774843089308886750647; aggressor=unknown; exchange_stale_untrusted=False; future_exchange_clocks=0; sample_receipt_at=2026-11-06T08:00:56.335809+00:00; granularity=unknown; incomplete recent response; no continuous tape; received_at=2026-11-06T08:00:56.335809+00:00; available_at=2026-11-06T08:00:56.335809+00:00; stale=False; exchange clock untrusted; no predictive signal; raw data LOCAL ONLY
  Compared with the preceding retained book: 10/10 bid positions and 10/10 ask positions changed price and/or quantity. This compares sampled positions only; it does not identify orders or executions.
- c2c-20261106-session02: ticker last price **75504 USD/BTC**; execution exchange-time window 2026-11-06T08:01:59.445738+00:00 → 2026-11-06T08:02:14.200272+00:00.
  - c2-evidence:d4e2c81fdf883c9c1ebe04edd2f8302733ae42c02137a5dcc6e103e77c060d42: Kraken BTC/USD derived private research; last_sampled_price_USD=75504; spread_USD=0.1; sampled_depth_BTC=0.994/0.164; depth_imbalance=0.7167530224525043177892918826; levels=10/10; integrity=ordered_uncrossed; received_at=2026-11-06T08:02:15.713029+00:00; available_at=2026-11-06T08:02:15.713029+00:00; stale=False; exchange clock untrusted; no predictive signal; raw data LOCAL ONLY
  - c2-evidence:fc206a1591fafd528c6ff2cf12105ae5c57f7ae5238ce050e799a69afa685a1d: Kraken BTC/USD derived private research; recent_sample_executions=20; volume_BTC=0.01782032; sample_VWAP_USD=75495.44797888028946730473976; aggressor=unknown; exchange_stale_untrusted=False; future_exchange_clocks=0; sample_receipt_at=2026-11-06T08:02:16.840725+00:00; granularity=unknown; incomplete recent response; no continuous tape; received_at=2026-11-06T08:02:16.840725+00:00; available_at=2026-11-06T08:02:16.840725+00:00; stale=False; exchange clock untrusted; no predictive signal; raw data LOCAL ONLY
  Compared with the preceding retained book: 10/10 bid positions and 10/10 ask positions changed price and/or quantity. This compares sampled positions only; it does not identify orders or executions.

Ticker is sampled reported last price; its exchange event time is unknown. Book is sampled aggregated L2 resting liquidity, ten levels per side; quote/size changes cannot establish executions, cancellations, actor identity or intent. Only the Trades endpoint reports executions. Reported buy/sell is retained; aggressor and execution aggregation semantics remain UNKNOWN. No directional BTC signal or execution is enabled.

REST book per-level update times remain in private wire receipts; no snapshot event timestamp or sequence is fabricated. Trade exchange timestamps are untrusted, explicitly truncated to microseconds. Receipt/first-seen/available_at drive visibility; none is backdated to exchange time. All six normalized real receipts have zero future-clock flags. Cursor is opaque, no ID-contiguity assumption or complete-feed reconstruction. Each observation becomes stale after 120 seconds; these samples must not be described as current after expiry.

## Independent restart, PIT and actual graph verification

New process reopened canonical history and verified **70 historical cutoff views**, four historical WORLD graph cutoffs on Nov 5/6, **11 earlier availability boundaries**, **56 new observations at before/at/after boundaries (168 checks)** and **1707 original protected-file hashes**. Separate C2-B baseline protection also passed (1,658 hashes, including authority). Synced sources, frozen fixtures/archive originals, tools and diagnosis remain unchanged.

Actual `TradingAgentsGraph.propagate` used scripted models, mocked vendors and denied socket/DNS/requests/curl networking. All selected WORLD IDs, C1/candidate context and funding/macro sections reach Market Analyst alongside compact C2 evidence after its recorded availability. Private payloads and book/trade records are absent from every model prompt. This verifies wiring, not model quality or profitable decisions. Scripted proposal outputs are test scaffolding only.

| Graph cutoff UTC | Narrative chars | Mixed chars | Largest individual prompt |
| --- | ---: | ---: | ---: |
| 2026-11-05T03:27:10.527275+00:00 | 5744 | 15810 | 23418 |
| 2026-11-05T03:27:26.528491+00:00 | 5429 | 15441 | 23049 |
| 2026-11-06T02:38:10.235518+00:00 | 5429 | 15441 | 22953 |
| 2026-11-06T02:38:29.353157+00:00 | 5429 | 15448 | 22960 |
| 2026-11-06T08:00:53.102274+00:00 | 5430 | 16628 | 24140 |
| 2026-11-06T08:00:56.335809+00:00 | 5430 | 16625 | 24137 |
| 2026-11-06T08:00:56.335810+00:00 | 5430 | 16625 | 24137 |
| 2026-11-06T08:02:57.335809+00:00 | 5430 | 16622 | 24134 |
| 2026-11-06T08:02:13.830525+00:00 | 5430 | 16625 | 24137 |
| 2026-11-06T08:02:16.840725+00:00 | 5430 | 16622 | 24134 |
| 2026-11-06T08:02:16.840726+00:00 | 5430 | 16622 | 24134 |
| 2026-11-06T08:04:17.840725+00:00 | 5430 | 16619 | 24131 |

Every narrative <=6,000; every mixed context and individual prompt <=28,000. The run-1 +121-second historical view correctly uses the newer run-2 sample when available; run-2 +121-second view explicitly marks both selected metrics stale. Earlier observation availability/first_seen remains immutable on replay.

## Backup, recovery and SHA256

Fresh preflight and per-run SQLite online backups passed full integrity, foreign-key and application-reference validation, exact row reconciliation and schema comparison. Each backup was restored into an independent disposable file with the same exact rows, schema and validation; no operational authority was switched and production was never replaced. SQLite backup page layout can yield a different file hash despite equal logical rows.

| Canonical state | SHA256 |
| --- | --- |
| Before | `1469142d87792fa61e0603f3012e6ba253a1fb7408b075e6a096afb7ea14384c` |
| After run 1 | `2b9431cfb515b083f9be04cfe335d3639006b3070210d49d6e9f9f6643052a99` |
| After run 2 / final verified | `f64c666fe525acbcd1e44dd3f7d71cc5fe9f2bf489b202eab67ddd251dc079f4` |

| Verified private backup | SHA256 |
| --- | --- |
| `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\backups\c2c-before-20261106.sqlite3` | `8aa9beab78f7458c3fc608911a3bc98fb431766baf440e8bd2ce11a09dba284b` |
| `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\backups\c2c-run1-20261106.sqlite3` | `8aa9beab78f7458c3fc608911a3bc98fb431766baf440e8bd2ce11a09dba284b` |
| `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\backups\c2c-run2-20261106.sqlite3` | `7ffadb8b018f7a18a94c31bc145a50dbefd5fdfcbc9acf2d1bbfb9383a780a16` |
| `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\backups\c2c-after-20261106.sqlite3` (post-acquisition) | `1950e270e658e089a10ff218eefbab5526e17cc14944ba99f89424426917d356` |

Rollback remains manual: stop writers, preserve current DB and sidecars, validate the selected named backup, then use a reviewed SQLite restore into the exact active canonical path. Do not silently replace history after partial ingestion. No recovery was needed in production.

## Tests, limitations and next checkpoint

- Full offline regression: **1,765 passed +99 subtests**, four existing skips, one integration deselected, 20 existing warnings.
- C2 focused: **67 passed**. Existing overlap/dedup, timestamp, rights, malformed input, transport failure, restart and graph tests included.
- Ruff on C2 adapter/contracts/tests, AST syntax and Git whitespace/diff checks pass.
- No actual acquisition or ingestion failure occurred. A read-only diagnostic initially used a relative path and was correctly refused before access; the absolute canonical path corrected it. The private verification harness was corrected to distinguish expiry of an older sample from a newer available sample. These are verification issues, not production ingestion defects. No product-code fix was needed.
- Offline graph runs emitted existing scripted-model structured-output fallback notices and unavailable Yahoo settlement-price warnings under denied networking. No live settlement price or real-model analytical result is claimed. The initial direct status patch also refused legacy non-UTF-8 text; an ASCII prefix was then added while preserving every prior byte.
- Historical Defender `Ransom:PowerShell/FileFix.DZ!MTB` remains unresolved. No new tool-reported block observed; no Defender audit or false-positive determination. Small commands/direct patches, existing environment, no downloads, exclusions, policy changes or bypass.
- Single-venue, sampled spot evidence only. Live overlapping-trade case unobserved; no always-on feed, complete execution tape, exact missing-trade count, historical backfill, paid API, model training, raw exfiltration, or trading.

Next practical checkpoint: bounded **BTC derivatives and positioning** acquisition, prioritizing funding, open interest and available basis, with exact venue/instrument/units, source eligibility, receipt timing and sampled coverage. Liquidations/options remain explicit free-coverage gaps until demonstrated. Preserve WORLD/political/macro context and the same canonical SQLite/PIT path. Phase 3 remains IN_PROGRESS.

Verification completed UTC: 2026-11-06T08:13:56.481686+00:00. Only this report and the project status entry are intended local Git changes; private database, backups, receipts and verification artifacts remain outside Git.
