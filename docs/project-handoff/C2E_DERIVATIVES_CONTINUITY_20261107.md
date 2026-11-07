# C2-E repeated Deribit BTC derivatives acquisition — November 7, 2026

**C2-E passed. Two manual Deribit samples were acquired, preserved and verified through Market Analyst. Phase 3 remains IN_PROGRESS.**

Repository `nghia876/crypto-trading-system`, branch `phase-3-event-narrative-slice`. Starting local HEAD `21892828453fa1c6aa61152cacb50f96e38eb809`. Remote branch verified read-only at `0a2a06fcf43251795bdddde3c7b5407e7cab5069`. The local commit containing this handoff is identifiable by this file. No GitHub push.

The adopted v1.1 Blueprint, Master Prompt and Resource Manifest govern this checkpoint alongside the C2-C and C2-D handoffs, SECURE_EXECUTION and the Deribit source assessment. The collector used the existing one-shot public API adapter and source ID `derivatives.deribit.btc_perpetual.public`. Raw response bodies and private audit files stay in `c2e-private/` outside Git. Canonical SQLite is the only authority. No scheduler, external model or trading path was used.

## Sessions and receipts

Each distinct process used a fresh HTTPS session and exactly two GETs to `https://www.deribit.com/api/v2/public/{endpoint}?instrument_name=BTC-PERPETUAL`, with at least 1.1 s between request starts, TLS verification, no redirects or retries, and a 256 KiB response cap. The pacing was below the published 20 requests/s standard non-matching sub-account rate and its 100-request burst. Anonymous traffic has a separate per-IP limit whose numerical threshold is unspecified in the guidance. Neither session encountered throttling. A local invocation rejected by the minimum separation check made zero requests. Session 2 began 81.837380 s after session 1 ended. [Deribit API rate guidance](https://docs.deribit.com/articles/rate-limits)

### Session 1 · `c2e-20261107-session01`

- UTC 2026-11-07T08:41:20.990963+00:00 to 2026-11-07T08:41:22.335798+00:00.
- Asia/Bangkok and Asia/Saigon 2026-11-07T15:41:20.990963+07:00 to 2026-11-07T15:41:22.335798+07:00. Elapsed 1.344835 s.

| Endpoint | Receipt UTC | HTTP | Duration (s) | Wire SHA-256 |
| --- | --- | ---: | ---: | --- |
| `get_instrument` | 2026-11-07T08:41:21.480257+00:00 | 200 | 0.489577 | `eda38b284c6ba0a47bbedc66167bf2257a8a956eefe5afa8e2c34b60d6a12336` |
| `ticker` | 2026-11-07T08:41:22.330788+00:00 | 200 | 0.238408 | `056b8e37b694e09d177330cd3c713438e51047918b2b57c87c2f589e7fcd353a` |

### Session 2 · `c2e-20261107-session02`

- UTC 2026-11-07T08:42:44.173178+00:00 to 2026-11-07T08:42:45.540154+00:00.
- Asia/Bangkok and Asia/Saigon 2026-11-07T15:42:44.173178+07:00 to 2026-11-07T15:42:45.540154+07:00. Elapsed 1.366976 s.

| Endpoint | Receipt UTC | HTTP | Duration (s) | Wire SHA-256 |
| --- | --- | ---: | ---: | --- |
| `get_instrument` | 2026-11-07T08:42:44.853095+00:00 | 200 | 0.679260 | `3c3c24966b8b2b3f28caf8076c3f39b9813e6ed7de981644e074b619f09253ef` |
| `ticker` | 2026-11-07T08:42:45.538059+00:00 | 200 | 0.263792 | `3ac8ee100955899f7b27c149db75799cd72f3422d9984451e63b6ec853c5f752` |

All four replies passed production JSON-RPC and adapter validation. Instrument fields were unchanged after normalization across C2-D and both C2-E samples. The instrument is active `BTC-PERPETUAL`, inverse, BTC-settled, USD-quoted, 10 USD/contract, minimum 10 USD and tick 0.5 USD/BTC. The new instrument results were identical field for field. Their wire bodies differed in `usDiff`, `usIn` and `usOut`. Each ticker wire body and normalized sample differs.

The normalized ticker inputs were `instrument_name`, `current_funding`, `funding_8h`, `open_interest`, `mark_price`, `index_price` and `timestamp`. The raw ticker also returned best bid and ask prices and amounts, estimated delivery price, interest value, last price, min/max price, settlement price, state and stats. These extra fields stayed in private receipts. Book quotes do not evidence executions.

## Observed values

| Sample | Current funding (fraction) | Funding 8h (fraction) | OI (USD) | Contracts | Mark (USD/BTC) | Index (USD/BTC) | Mark/index premium (%) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C2-D | 0.0 | 0.00000727 | 707371690 | 70737169 | 75264.82 | 75249.83 | 0.019920310783 |
| C2-E 1 | 0.0 | 0.00000462 | 684430630 | 68443063 | 76025.67 | 76020.71 | 0.006524537853 |
| C2-E 2 | 0.0 | 0.00000459 | 684454130 | 68445413 | 76025.94 | 76021.24 | 0.006182482685 |
| Δ C2-D → C2-E 1 | +0.0 | -0.00000265 | -22941060 | -2294106 | +760.85 | +770.88 | -0.013395772931 |
| Δ C2-E 1 → C2-E 2 | +0.0 | -0.00000003 | +23500 | +2350 | +0.27 | +0.53 | -0.000342055168 |

Funding is reported under continuous accrual. The fields give reported rates and do not establish realized position payments or guaranteed future costs. The mark/index premium is a same-ticker proxy, rounded here to 12 decimal places. Traded spot/dated-futures basis and annualized basis remain unavailable. OI measurement timestamp and reporting delay are unknown. The Nov 5 notice describes a postponed eight-hour-delay release. Aggregate OI does not establish net direction. [Deribit release notice](https://support.deribit.com/hc/en-us/articles/40275495462301-5-November-2026)

| Sample | Evidence ID | Retrieved / first seen / available UTC | Reported exchange timestamp UTC (untrusted) | Receipt minus exchange (s) |
| --- | --- | --- | --- | ---: |
| C2-D | `c2d:82b0d64fd138782ca6181900455bcf8c12703e5629e3d5ca72b7dacd6673dafa:sample` | 2026-11-06T15:36:30.659370+00:00 | 2026-11-06T15:36:30.093000+00:00 | 0.56637 |
| C2-E 1 | `c2d:60954be7169030004c320e7ef0c6f9d9e8bdb2c8bf09c03edaa08a702cf2ebbe:sample` | 2026-11-07T08:41:22.330788+00:00 | 2026-11-07T08:41:22.800000+00:00 | -0.469212 |
| C2-E 2 | `c2d:60a0b1d4b7134f18a56ceea79ed6afafd9003c1021ddf5c35170bb9d016a8248:sample` | 2026-11-07T08:42:45.538059+00:00 | 2026-11-07T08:42:45.988000+00:00 | -0.449941 |

Local receipt marks first knowledge in the acquisition process. Later SQLite ingestion retains that provenance. The existing observation envelope requires an event-time field and uses the receipt as its local sampling anchor. Nullable exchange event time is held separately in the payload and never controls availability. Both new ticker timestamps were ahead of the local receipt clock and flagged. The freshness window is 120 seconds from receipt, inclusive. Thereafter the latest eligible sample is presented as historical and stale. At the time of this handoff both new records are historical.

## Preservation and recovery

| Table | Before | After session 1 | After session 2 |
| --- | ---: | ---: | ---: |
| observations | 1380 | 1385 | 1390 |
| source_definitions | 153 | 154 | 155 |
| coverage | 180 | 183 | 186 |
| data_gaps | 2 | 3 | 3 |

Each session added five observations, two private receipts, instrument metadata, one sample and one ingest receipt. The observation ID prefix is the existing `c2d:` namespace plus the SHA-256 of each distinct run ID. Source definitions added one history row per session under the same source ID. Each session added three UNKNOWN coverage rows for funding, OI and basis. The long C2-D to C2-E interval added one UNKNOWN gap. The 83.207271 s ticker-to-ticker interval did not cross the adapter's >240 s gap-row threshold. Off-session coverage remains unknown throughout.

The gap runs from 2026-11-06T15:36:30.659371+00:00 to 2026-11-07T08:41:22.330788+00:00 UTC. The gap records lack of observation during manual sampling, with no finding of an exchange outage.

There were two new samples, no identical normalized samples and zero revisions. Current funding and normalized instrument metadata were unchanged. Re-ingesting each of the same wire receipts under its existing run ID in a disposable store caused zero row changes. This tests exact receipt replay, independently of whether a future live ticker repeats values.

All preexisting rows, source histories, coverage, gaps, schema and relationships matched exactly, including C2-D, WORLD, Kraken and C1. The 1,707 protected files matched their recorded hashes.

| Checkpoint | Canonical file SHA-256 |
| --- | --- |
| Before | `e0748d58c589679266fe4a671e58a7be40b37b0aae2bd2d74beeafbe4c341ca3` |
| After session 1 | `98b701c038e551221b1014c964352dc6ed9694251b0a05f131bc8741fef2bad0` |
| After session 2 | `c626c4e462c63e7079b5d2d25f6917380923b27f0adfcd11d22e2fac8200ea7c` |

| Table | Before row SHA-256 | Final row SHA-256 |
| --- | --- | --- |
| observations | `a342e5f90aba29ac9db414d106b6339a9b3d47f2c194e8ba8e65c623c3ce32a5` | `b244a983c0f45da036e7fe8c1ca5500025ba7fc9351a793a11171fce7ad0846f` |
| source_definitions | `d084ec31bf3891138ae018d839bc4e2af3c059972f548ae13c7fb7ee0e84e807` | `19c86e70f0beba50783a3eaab043f75dbe26086d69f88845beb8fce2e265f3c9` |
| coverage | `a288bc53d8d36d1ec85961035e6c180c704a74e93a5659379a0e9f67fbc513c6` | `b4569a6c9a178639a5d6e9ede647570ff003ae9f0e71fc3608c09c892e1f70ef` |
| data_gaps | `e55e50dad052824a017aaa454bf0f38ea008f895548f324eb62448ff7bde937d` | `48e38c6d6a7323116f4a2b9d7e8c2bf0c65d2f827bc4052bc7f71e6a3242d9cb` |

Canonical path is `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\information.sqlite3`. Fresh prewrite SQLite backup `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\backups\c2e-before-20261107.sqlite3`, SHA-256 `9dd1bf2daef7821e7d342b6b348e735d91e546e6e55830c5299a5655426bff52`, was restored to a disposable clone before acquisition. Final SQLite backup `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\backups\c2e-after-20261107.sqlite3`, SHA-256 `dd346148f27101d0f636e24d5837c95f7d8126c39423c6e88d7eafe46345aba0`, was restored and audited for exact logical equality. SQLite online-backup layout can differ from the canonical file. The per-session write gate also made independent prewrite backups.

- Session 1 write-gate backup SHA-256 `9dd1bf2daef7821e7d342b6b348e735d91e546e6e55830c5299a5655426bff52`.
- Session 2 write-gate backup SHA-256 `b77ccb79b5f6efa35cace2b91b98ff54adcd0e0ea871fcd54a99bbb9351a2aff`.

## Point-in-time and Market Analyst verification

Before canonical writes, both real sessions were staged in sequence and the earlier 70 views and 11 previously verified boundaries were compared exactly. Both stage and a fresh process over the restored final store passed 45 before/at/after observation checks, including C2-D. Actual `TradingAgentsGraph.propagate` ran at 5 stage and 19 restored production cutoffs with scripted models and blocked network transports. The production replay narrative, mixed context and individual prompt maxima were 5,761, 17,704, 25,216 characters respectively against caps of 6,000 / 28,000 / 28,000.

| Cutoff UTC | Eligible samples | Selected | Older omitted as metrics (lineage only) | Future omitted | Visible non-sample rows omitted (private wire) | Kraken / WORLD IDs included (WORLD omitted) |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| 2026-11-05T03:27:10.527275+00:00 | 0 | None | 0 (0) | 3 | 0 (0) | 0 / 7 (815) |
| 2026-11-05T03:27:26.528491+00:00 | 0 | None | 0 (0) | 3 | 0 (0) | 0 / 5 (852) |
| 2026-11-06T02:38:10.235518+00:00 | 0 | None | 0 (0) | 3 | 0 (0) | 0 / 5 (852) |
| 2026-11-06T02:38:29.353157+00:00 | 0 | None | 0 (0) | 3 | 0 (0) | 0 / 5 (860) |
| 2026-11-06T15:36:30.659369+00:00 | 0 | None | 0 (0) | 3 | 2 (1) | 2 / 5 (860) |
| 2026-11-06T15:36:30.659370+00:00 | 1 | C2-D fresh | 0 (0) | 2 | 4 (2) | 2 / 5 (860) |
| 2026-11-06T15:36:30.659371+00:00 | 1 | C2-D fresh | 0 (0) | 2 | 4 (2) | 2 / 5 (860) |
| 2026-11-06T15:38:30.659370+00:00 | 1 | C2-D fresh | 0 (0) | 2 | 4 (2) | 2 / 5 (860) |
| 2026-11-06T15:38:30.659371+00:00 | 1 | C2-D stale | 0 (0) | 2 | 4 (2) | 2 / 5 (860) |
| 2026-11-07T08:41:22.330787+00:00 | 1 | C2-D stale | 0 (0) | 2 | 6 (3) | 2 / 6 (859) |
| 2026-11-07T08:41:22.330788+00:00 | 2 | C2-E 1 fresh | 1 (1) | 1 | 8 (4) | 2 / 6 (859) |
| 2026-11-07T08:41:22.330789+00:00 | 2 | C2-E 1 fresh | 1 (1) | 1 | 8 (4) | 2 / 6 (859) |
| 2026-11-07T08:42:45.538058+00:00 | 2 | C2-E 1 fresh | 1 (1) | 1 | 10 (5) | 2 / 6 (859) |
| 2026-11-07T08:42:45.538059+00:00 | 3 | C2-E 2 fresh | 2 (1) | 0 | 12 (6) | 2 / 6 (859) |
| 2026-11-07T08:42:45.538060+00:00 | 3 | C2-E 2 fresh | 2 (1) | 0 | 12 (6) | 2 / 6 (859) |
| 2026-11-07T08:43:22.330788+00:00 | 3 | C2-E 2 fresh | 2 (1) | 0 | 12 (6) | 2 / 6 (859) |
| 2026-11-07T08:43:22.330789+00:00 | 3 | C2-E 2 fresh | 2 (1) | 0 | 12 (6) | 2 / 6 (859) |
| 2026-11-07T08:44:45.538059+00:00 | 3 | C2-E 2 fresh | 2 (1) | 0 | 12 (6) | 2 / 6 (859) |
| 2026-11-07T08:44:45.538060+00:00 | 3 | C2-E 2 stale | 2 (1) | 0 | 12 (6) | 2 / 6 (859) |

The Market Analyst included the selected Kraken spot, WORLD/politics/C1 evidence and the macro section. Funding/OI used only the latest eligible Deribit sample. Raw Deribit receipt IDs and bodies were absent from all captured prompts. The table names the same full Deribit IDs listed above. The latest graph also included these exact compact evidence IDs:

- Kraken: `c2-evidence:d4e2c81fdf883c9c1ebe04edd2f8302733ae42c02137a5dcc6e103e77c060d42`, `c2-evidence:fc206a1591fafd528c6ff2cf12105ae5c57f7ae5238ce050e799a69afa685a1d`
- WORLD/politics/C1: `news:d2c0870c85b4c22ef51019b67d6004d5f11685169eb0ce482f136130bf62b436`, `news:f39d0d3242799f7585245b7d44e114e7cea242e7f40c580cc8f2a9a537dd6ba2`, `news:fefb924ffdb123c09b8bdf66784630401ca3fdf231be13a3d5270e3eca7497f8`, `news:ec9ff12316ffd9dfc7b9965f6fac3972b4e7a05108200fa11936b7198e97a49e`, `news:a34db6cd7a43e81653c5a92afb81181aeeb352aa468bbc0dbf4c6621f134efed`, `news:71e54595a837b958802d9326f8abd65ad7f9ea5ce27e3f716f8ddc673e09a7c7`
- Macro series lines in the final market prompt: DCOILWTICO (macro.oil.wti_usd_per_barrel): unknown; freshness: unknown; proxy for: none; evidence IDs: none / DGS2 (macro.treasury_2y_yield_pct): unknown; freshness: unknown; proxy for: none; evidence IDs: none / DTWEXBGS (macro.usd.broad_nominal_index): unknown; freshness: unknown; proxy for: a broad dollar-strength measure; not the ICE U.S. Dollar Index (DXY); evidence IDs: none / NFCI (macro.risk.financial_conditions_index): unknown; freshness: unknown; proxy for: U.S. financial conditions; not a direct market risk-on/risk-off price proxy; evidence IDs: none / SP500 (macro.risk.sp500_close): unknown; freshness: unknown; proxy for: broad U.S. equity risk appetite; evidence IDs: none / VIXCLS (macro.risk.vix_close): unknown; freshness: unknown; proxy for: U.S. equity implied volatility / risk aversion; evidence IDs: none
- Final mixed-context omissions by section (omitted / candidate rows): Recorded coverage 182/186, Point-in-time source definitions 36/39, Evidence metadata (schema and unit) 13/19

Focused offline suite: 74 passed in 16.46s. Full offline suite: 1807 passed, 4 skipped, 1 deselected, 20 warnings, 99 subtests passed in 88.46s (0:01:28). An initial test invocation loaded the private authority and failed when test fixtures tried to create disposable stores. The test harness then isolated that configuration in memory and reran the suite. The first graph audit predicate treated provenance references as duplicate metric lines. The final audit distinguishes these. Production code, configuration and fixtures were reused. Ruff passed on the existing adapter, consumer and focused adapter tests. The four private checkpoint scripts passed Python syntax checks. The historical Defender detection remains unresolved.

## Remaining scope

These are three observations from one venue across two dates. Manual intervals have unknown coverage. OI timing, historical realized funding, dated futures basis, liquidation and options evidence remain open. Next recommended checkpoint: scope a bounded historical funding pull with explicit accrual versus settlement semantics, then pair dated futures with timestamp-aligned spot for basis. Assess liquidity, ETF and on-chain sources separately for availability, rights, units and first-known time.

**Phase 3 remains IN_PROGRESS.**
