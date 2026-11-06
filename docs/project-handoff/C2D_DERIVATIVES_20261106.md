# C2-D BTC derivatives acquisition — November 6, 2026

Phase 3 remains **IN_PROGRESS**. Local implementation; no GitHub push, main,
merge, rebase, force, scheduler or trading. Real acquisition and final verification
passed; measured results are recorded below.

## Checkout, authority and protection

Verified branch `phase-3-event-narrative-slice`, starting local HEAD
`926f6b03b77054d2b791f28200b5ef4c018eb1a5`. Only preexisting untracked
`.phase12-tools/` and `docs/project-handoff/PHASE_3_BOTTLENECK_DIAGNOSIS.md`
were present. Both remain protected. The supplied remote backup through
`0a2a06fcf43251795bdddde3c7b5407e7cab5069` was not freshly queried.

Read adopted workspace v1.1 revised Product Blueprint, Master Prompt and Resource
Manifest; SECURE_EXECUTION; C1, C2-A rights/contracts, C2-B and C2-C handoffs;
existing Binance derivatives, Kraken, source/store/runtime/consumer and actual
graph/test code. Historical `sources/` and frozen original material stay read-only.

Active installation authority resolves to the sole production store:
`C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\information.sqlite3`.
Other legacy SQLite files are not selected or promoted. Initial full integrity,
foreign-key and application-reference validation passed. Initial counts were
**1375 observations / 152 source histories / 177 coverage / 2 gaps**, SHA256
`f64c666fe525acbcd1e44dd3f7d71cc5fe9f2bf489b202eab67ddd251dc079f4`.

Fresh online backup `local-runtime/backups/c2d-before-20261106.sqlite3` and
isolated `c2d-private/DISPOSABLE-RECOVERY.sqlite3` have exactly matching rows,
schema, references and integrity. Backup SHA256:
`1950e270e658e089a10ff218eefbab5526e17cc14944ba99f89424426917d356`.
They are private recovery/test artifacts, never competing operational authority.

## Venue, endpoints and scoped usage assessment

Selected **Deribit BTC-PERPETUAL**. Free anonymous official production HTTPS GETs:

1. `https://www.deribit.com/api/v2/public/get_instrument?instrument_name=BTC-PERPETUAL`
2. `https://www.deribit.com/api/v2/public/ticker?instrument_name=BTC-PERPETUAL`

Current official [instrument](https://docs.deribit.com/api-reference/market-data/public-get_instrument)
and [ticker](https://docs.deribit.com/api-reference/market-data/public-ticker)
contracts were checked. The [API usage policy](https://docs.deribit.com/articles/api-usage-policy)
explicitly supports unauthenticated public market requests and discourages
redundant polling. [Rate guidance](https://docs.deribit.com/articles/rate-limits)
says anonymous requests have per-IP limits; authenticated default 20/s is NOT
assumed to be the anonymous allowance. This implementation permits only two
calls, >=1.1s between starts, no retries/redirects, verified TLS, 256 KiB per
response, 5s connect/10s read timeout, and a 20s elapsed streaming check between
chunks. A blocking read can extend that check by its read timeout. Any denial,
API error, malformed input or exhausted bound stops acquisition.

[Current exchange terms](https://support.deribit.com/hc/en-us/articles/25944532191645-Deribit-Exchange-Membership-Terms-Deribit-FZE),
version August 13, 2026, clause 2.10 permits personal market/derived data use and
restricts other aggregation/forwarding/processing; clause 2.11 supports provided
APIs/software. Clause 27.1(i) contains broad automated data collection restrictions.
Read alongside the API-specific policy and market-data collection guidance, our
bounded engineering assessment treats these two ordinary supported personal API
queries as within the provided API workflow, not permission for bulk harvesting
or unrestricted scraping. The [Panama terms](https://support.deribit.com/hc/en-us/articles/25944471089437-Terms-of-Service-DRB-Panama-Inc)
also distinguish personal from other uses (32.3). No jurisdiction/account
eligibility is inferred from timezone; no account or trading service is used.

This is a scoped personal/private research assessment, not express AI licensing
or a legal determination. Personal local retention and compact personal inference
are the recorded scope; no commercial reuse, publication, redistribution, training
or raw third-party model export. No express AI consent is claimed. Compact data
does not evade a restriction: both raw and derived data remain subject to the
same personal-use scope. All graph verification uses local scripted models with
network denied, so no real external-model transmission is claimed or tested.
Reassess before changing that use, or on an actual policy/access restriction.

## Instrument and measurement semantics

- Source ID: `derivatives.deribit.btc_perpetual.public`; qualified instrument:
  `deribit:BTC-PERPETUAL`. Metadata must match BTC base, USD quote, BTC settlement,
  future kind, `reversed` inverse type, active perpetual, `btc_usd` index and
  **10 USD per contract**. Actual tick/minimum quantity are retained. Perpetual
  expiry is null; an exchange sentinel date is not represented as a maturity.
- OI is the reported outstanding **USD amount**, not a count of contracts or BTC.
  Dividing by the verified USD10 multiplier gives labeled contract equivalents.
  No inferred BTC OI/notional or long-versus-short direction is supplied.
- `current_funding` and `funding_8h` are preserved separately as exact fractions.
  [Inverse perpetual specification](https://support.deribit.com/hc/en-us/articles/31424954847133-Inverse-Perpetual)
  describes continuously accrued funding expressed on an eight-hour basis;
  these ticker fields are not a realized position payment ledger or guaranteed
  next-period cost. No prediction, eight-hour payment-event timestamp or
  annualized funding return is fabricated. Historical settled funding is deferred.
- Mark/index prices come from the SAME ticker and contract, both USD/BTC.
  `(mark/index - 1) * 100` is labeled a **mark/index premium proxy**. It is not
  traded spot–futures basis, executable arbitrage, or annualized dated-futures
  basis. No expiry annualization or cross-exchange Kraken price comparison.
- The official [November 5 notice](https://support.deribit.com/hc/en-us/articles/40275495462301-5-November-2026)
  describes an eight-hour public OI delay BUT prominently says the release is
  postponed until further notice. Initial search-preview wording omitted this
  qualifier; full-page review corrected it before implementation/acquisition.
  Therefore actual OI delay and OI measurement event time remain **UNKNOWN**;
  neither immediate nor eight-hour-old OI is asserted. Ticker timestamp is not
  silently assigned as OI measurement time.

## Persistence, replay and analyst wiring

`deribit_public.py` adds an explicit opt-in two-request CLI. Before writing it
resolves existing authority, takes the shared collection lock and creates a new
verified SQLite online backup. Acquisition validates all data before append.
Source definitions, raw wires, metadata, normalized sample, ingest receipt,
coverage and any gap append in ONE existing store transaction; no schema change.

Each successful run has five observations: two private raw wires, instrument
metadata, one qualified funding/OI/premium sample and one ingest receipt; one
source history and three UNKNOWN-completeness coverage records. Raw SHA256,
URLs, local receipt times and references preserve lineage. Run-ID replay is
idempotent across restart; changed receipt under that ID and ambiguous same-time
samples reject before writes. New manual samples are immutable observations,
not overwritten historical values. Every original row remains intact.

Exchange event time is nullable/untrusted. Envelope event time is explicitly the
local sample identity anchor, not an invented exchange event. Local receipt,
first-seen and availability gate PIT; exchange clocks never backdate evidence.
Future clocks are flagged and exchange age is shown. New evidence expires for
current use after 120s; OI measurement freshness remains unknown even on fresh
receipt. Repeated manual samples >240s apart create an unknown interval gap
beginning immediately AFTER the prior sample, so the store cannot mistake that
interval for a resolved prior observation. All off intervals remain unknown,
including shorter intervals and the unsampled period before the first sample.

Consumer renders only one allowlisted compact ATTRIBUTED Deribit record in its
existing Signals reservation; never raw JSON or general payload dumps. Existing
WORLD/C1/politics, spot, Binance funding and macro lines remain separate. Latest
source rights at each cutoff gate selection, including revocation and conflicting
same-time definitions. Existing narrative <=6000 and mixed/prompt <=28000 budgets
are retained. No interpretation, positioning score or trading logic is added.

## Security and recoverability

Small auditable shell operations and direct patches only. No installers,
credential access, security-setting changes, AV exclusion/bypass or PowerShell
policy change. The earlier `Ransom:PowerShell/FileFix.DZ!MTB` remains unresolved;
absence of a new tool-reported block is not a Defender audit or host clearance.
The session network grant is limited to the approved public collection scope;
model networking remains denied in graph tests.

Rollback is MANUAL: stop writers, preserve current canonical DB and sidecars,
validate the selected named backup, restore first into an isolated path and
compare exact rows/schema/integrity, then use a reviewed SQLite restore into the
same active canonical path. Do not silently replace partial ingestion history.
No production rollback is performed by this checkpoint.

## Actual bounded collection and final results

**PASS: real derivatives sample persisted and reached actual scripted graph. Phase 3 IN_PROGRESS.**

Run `c2d-20261106-one-shot`: UTC **2026-11-06T15:36:29.153808+00:00 → 2026-11-06T15:36:31.555218+00:00**, elapsed 2.401410s. Asia/Bangkok / Asia/Saigon **2026-11-06T22:36:29.153808+07:00 → 2026-11-06T22:36:31.555218+07:00**.
Exactly two real production API requests, no retries/backfill. No synthetic observations entered canonical. The SAME real receipts passed isolated-copy ingestion/idempotency before the canonical append.

| Endpoint | Received UTC | HTTP | Response seconds | Wire SHA256 |
| --- | --- | ---: | ---: | --- |
| get_instrument | 2026-11-06T15:36:29.994329+00:00 | 200 | 0.839391 | `1b8db3a5b0014f38373163742345f06c67a588781092d64475b1ad5e92c36f13` |
| ticker | 2026-11-06T15:36:30.659370+00:00 | 200 | 0.403743 | `94506fc072974bcc9807de816eac958f1da92227868a05101bfc22ea0116aeaf` |

| Canonical table | Before | After |
| --- | ---: | ---: |
| observations | 1375 | 1380 |
| source_definitions | 152 | 153 |
| coverage | 177 | 180 |
| data_gaps | 2 | 2 |

Canonical before SHA256: `f64c666fe525acbcd1e44dd3f7d71cc5fe9f2bf489b202eab67ddd251dc079f4`. After: `e0748d58c589679266fe4a671e58a7be40b37b0aae2bd2d74beeafbe4c341ca3`.
All original 1375 observation rows, 152 source-history rows, 177 coverage rows and two gaps remain exact; schema unchanged. Original 114 supersession links and 871 historical content versions remain unchanged. Five new observation identities, zero content revisions. One new source ID. Three new coverage records are UNKNOWN completeness; no claim of continuous coverage or zero missing activity.

Real sampled current_funding **0.0**, funding_8h **0.00000727**, both fractions; OI **707371690 USD**, **70737169** USD10-contract equivalents. Mark/index **75264.82/75249.83 USD/BTC**; same-ticker mark/index premium **0.0199203107834263545844555396337772457426149667000%**. Ticker exchange timestamp **2026-11-06T15:36:30.093000+00:00**, received/available **2026-11-06T15:36:30.659370+00:00**; future-clock flag **False**. These are historical samples, stale after 120s. OI event time/delay remains unknown. No realized funding payments, OI change/direction, traded basis or predictive signal established.

Normalized evidence: `c2d:82b0d64fd138782ca6181900455bcf8c12703e5629e3d5ca72b7dacd6673dafa:sample`. Each private wire and metadata/ingest identity uses the same `c2d:<run-sha256>:` prefix with suffix `get_instrument`, `ticker`, `instrument`, `ingest`. The source ID and all receipt references are stored canonically; exact raw data remains private.

## Verification and graph evidence

Production verified **70 historical views + 11 Nov5/Nov6 boundaries**, **15** before/at/after checks for all five new observations; **1707 protected-file hashes**. Restart replay of the real receipts makes zero row changes.
Actual `TradingAgentsGraph.propagate` executed with local scripted models, mocked vendors and denied socket/DNS/requests/curl networking. Eight isolated synthetic-copy and eight production-store cutoff runs include four historical WORLD boundaries and just-before/at/after/new stale views. All selected WORLD/C1 IDs and spot IDs reach Market Analyst; political regressions pass, funding/macro remain present. New derived ID appears only at/after availability. Raw wire JSON and raw spot books are absent from all captured prompts. Scripted outputs demonstrate wiring, not analytical quality.

| Production cutoff UTC | Narrative chars | Mixed chars | Largest prompt | Derivative visible |
| --- | ---: | ---: | ---: | --- |
| 2026-11-05T03:27:10.527275+00:00 | 5744 | 15810 | 23418 | no |
| 2026-11-05T03:27:26.528491+00:00 | 5429 | 15441 | 23049 | no |
| 2026-11-06T02:38:10.235518+00:00 | 5429 | 15441 | 22953 | no |
| 2026-11-06T02:38:29.353157+00:00 | 5429 | 15448 | 22960 | no |
| 2026-11-06T15:36:30.659369+00:00 | 5413 | 16601 | 24113 | no |
| 2026-11-06T15:36:30.659370+00:00 | 5413 | 17343 | 24855 | yes |
| 2026-11-06T15:36:30.659371+00:00 | 5413 | 17343 | 24855 | yes |
| 2026-11-06T15:38:31.659370+00:00 | 5413 | 17342 | 24854 | yes |

Compact attributed record at availability:

```text
- c2d:82b0d64fd138782ca6181900455bcf8c12703e5629e3d5ca72b7dacd6673dafa:sample: ATTRIBUTED Deribit BTC-PERPETUAL inverse, BTC-settled, 10 USD/contract; current_funding=0.0; funding_8h=0.00000727 fraction; 8h-expressed continuous accrual, reported statistic; realized payment/prediction UNKNOWN; OI=707371690 USD (70737169 contract equivalents); OI time/delay UNKNOWN (postponed Nov5 change), never directional long/short; mark_index_premium=0.0199203107834263545844555396337772457426149667000%; same-ticker proxy, not traded spot/futures basis; received/available=2026-11-06T15:36:30.659370+00:00; stale=False; exchange_time=2026-11-06T15:36:30.093000+00:00; exchange_age_s=0.56637; future_clock=False; gaps=0; off intervals UNKNOWN; no guaranteed funding cost; raw LOCAL ONLY
```

**Final full offline suite: 1807 passed +99 subtests**, four existing skips, one integration deselected, 20 existing warnings. **Focused: 109 passed**. Ruff, three-file AST syntax, whitespace/diff checks pass. Tests cover exact signed funding, invalid/oversized decimals and exponent attacks, wrong/inactive contract, invalid OI/mark/index/time, future/missing exchange clocks, local rollback, receipt/hash collisions, same-time ambiguity, backup/opt-in gates, idempotency/restart, rights revocation, PIT/stale views, gap visibility, 301/403/429/500 stops, pacing and byte caps. Synthetic fixture quantities occur only in disposable test databases. Initial test failures identified gap-anchor and exception-order issues; both were corrected before live writes, and the final focused/full suites pass. Existing scripted-model structured-output fallback and unavailable historical settlement warnings are scaffolding limitations.

## Final backups, limitations and next action

Fresh live prewrite backup: `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\backups\c2d-live-before-20261106.sqlite3`, SHA256 `1950e270e658e089a10ff218eefbab5526e17cc14944ba99f89424426917d356`. Final private backup: `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\backups\c2d-after-20261106.sqlite3`, SHA256 `9dd1bf2daef7821e7d342b6b348e735d91e546e6e55830c5299a5655426bff52`. Final isolated rollback copy: `C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\c2d-private\DISPOSABLE-FINAL-RESTORE.sqlite3`. Both final files match canonical exact rows/schema/integrity/references. Online-backup file layout may differ from canonical despite logical equality. No rollback was needed.

Private receipt/audit location: workspace `c2d-private/` (outside Git), including per-response raw files, attempt/live timing manifests, stage/production graph checks and final audit. Canonical is the only authority. No raw data, private SQLite, local configuration or private test harness is staged.

Remaining limitations: one manual sample and one venue; no continuity, OI change history or live repeated sample dedup claim; OI measurement time/delay unknown; current/8h funding rather than realized payment history; premium proxy rather than traded dated-futures basis; no liquidation/options acquisition; no external-model quality or data-transmission test; unresolved historical Defender finding. Existing source adapters and historical samples are not represented as fresh.

**Precise next action:** accept this bounded C2-D acquisition/wiring checkpoint, then authorize a separate bounded repeat derivatives session to measure funding/OI sample changes and freshness/gaps, optionally adding hourly historical funding with explicit realized-versus-reported semantics. Confirm an active OI delay announcement before treating it as current. Traded dated-futures basis, liquidations and options remain later scope. No scheduler or Phase 4 interpretation is enabled. **Phase 3 remains IN_PROGRESS.**
