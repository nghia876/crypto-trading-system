# C2 source eligibility checkpoint — November 6, 2026

**BLOCKED at source eligibility; activation withheld. Phase 3 IN_PROGRESS.**
No venue/pair is approved for C2 acquisition. This is a bounded review of
Kraken, Coinbase and the existing Binance source, not proof that no eligible
venue exists anywhere. The user's explicit instruction to stop activation when
rights cannot be confirmed controls this result. No claim of licensed access.

## Checkout and scope

Started at `7077df64003cf1beb0583092ab2efcf58712d19a` on
`phase-3-event-narrative-slice`. Tracked tree and staging were clean. Existing
untracked `.phase12-tools/` and
`docs/project-handoff/PHASE_3_BOTTLENECK_DIAGNOSIS.md` were preserved.
Remote feature `0a2a06f...` and main `1394a3f...` are supplied historical snapshots;
neither was freshly verified here. No push, fetch, merge, rebase or main change.

Consulted adopted workspace v1.1 revised Blueprint, Master Prompt and Resource
Manifest, read-only historical attachments, current project status, C1 and
November 6 longitudinal reports, secure-execution and source-rights guidance.
Inspected existing Binance spot OHLCV, source registry and SQLite contracts.
Existing `market.binance.spot` covers BTCUSDT candles; it is not permission for
new depth/trade acquisition. The append-only store retains source definitions,
observations, coverage and gaps. No alternate production store was introduced.

## Current independently retrieved official policies

Research surface: Work web/network retrieval on November 6, 2026. Policy and
documentation retrieval succeeded as described below. Documentation examples
are not live exchange responses, and research access does not establish Python
endpoint reachability, user jurisdiction eligibility or permission to collect.

| Candidate | Current finding | C2 disposition |
| --- | --- | --- |
| Coinbase Exchange, prospective BTC-USD | [Market Data Terms](https://www.coinbase.com/legal/market_data), updated August 7, 2026: personal/internal research licence, external redistribution restrictions, and section 3.5 broadly restricting AI development and operation without written consent. Internal inference cannot safely be treated as cleared. | Withheld; no data probe. |
| Kraken Spot, prospective BTC/USD (legacy XBTUSD / XXBTZUSD identifiers) | [Global Terms](https://www.kraken.com/legal/global-terms), sections 8–9: limited own-benefit permission plus restrictions on copying, extraction, automation and third-party applications without prior written consent. Official API documentation invites automated public market access, but the applicable exception and durable retention/AI-processing scope were not established. | Unresolved conflict; withheld rather than claiming all Kraken API use is prohibited. |
| Binance Spot, prospective BTCUSDT | [Vision Dataset Terms v1.0](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md), August 26, 2026, provide conditional noncommercial dataset reuse, attribution/share-alike and defined research uses. This does not independently settle application to the exact live REST endpoints. The [general terms page](https://www.binance.com/en/terms) returned navigation without its substantive terms. | Exact live depth/trade retention and AI scope unverified; existing candle code is not grandfathered C2 permission. |

No account, key, paid licence, contact with a provider or acceptance flow was
initiated. External redistribution and sending data to a third-party model are
separate rights questions from local collection and retention. No AI-specific
permission was invented. No robots approval is claimed: no live collection was
attempted after the rights gate failed. Robots permission would not cure it.

## One preferred technical candidate, still unapproved

Kraken BTC/USD would be the narrow candidate for a follow-up rights clarification.
The official [depth documentation](https://docs.kraken.com/api-reference/market-data/get-order-book)
advertises `https://api.kraken.com/0/public/Depth`, 1–500 levels per side,
default 100. The [trades documentation](https://docs.kraken.com/api-reference/market-data/get-recent-trades)
advertises `https://api.kraken.com/0/public/Trades`, 1–1000 trades, default 1000,
with a since cursor and source pair identifiers. These are documentation facts,
not verified current instrument metadata or successful responses for this user.
The [public rate-limit guidance](https://support.kraken.com/articles/206548367-what-are-the-api-rate-limits-),
updated October 1, 2026, says at most one public call per second remains within
limits; Trades/OHLC are scoped by IP/pair and other public methods by IP.
Any later approved probe should use a lower aggregate frequency, no retry loop,
and honor denials/backoff. No polling frequency was activated or observed.

## Implementation and evidence status

No C2 provider adapter, normalized schema, source ID, migration, registry entry,
collector CLI or analyst wiring was implemented or activated. No synthetic C2
parser fixtures were added. No live depth/trade response was requested or retained,
even in scratch storage. Therefore live API reachability, actual precision,
instrument flags, side semantics, raw-versus-aggregated execution granularity,
sequence completeness and source clock quality remain UNKNOWN.

The following are requirements for a later implementation, not verified features:

- Source-qualified immutable snapshot and execution identities; decimal strings,
  BTC base quantities and USD quote prices; validated tick/lot metadata where known.
- Separate nullable/untrusted exchange event time, local receive/first-known and
  conservative availability times; no fallback timestamp presented as exchange time.
- Sampled resting depth only, without claiming reconstructed L2, continuous
  coverage or interpreting quote changes as executions. No directional signals.
- Verify taker/aggressor semantics independently; otherwise UNKNOWN. Preserve
  trade IDs, cursor/sequence/snapshot markers, aggregation and missing-field flags.
- Reject malformed/crossed books and invalid decimals; explicitly handle partial,
  empty, stale, duplicate, reversed/out-of-order, skewed and disconnected responses.
  Record unknown coverage and gaps rather than infer missing trades from ID jumps.
- Same SQLite source-definition/coverage/health contracts; deterministic revisions,
  idempotent replay and restart; rights denial before networking or storage.
- Compact PIT-qualified Market Analyst summaries retaining WORLD/C1 and
  macro/liquidity reservations, narrative <=6000 and all contexts/prompts <=28000.

## Verification and preservation

Existing regression results verify the unchanged baseline, not the unimplemented
C2 requirements:

- Full offline: **1698 passed, 99 subtests passed**, 4 skipped, 1 integration
  deselected, 20 warnings. Focused spot/store/C1/context: **38 passed**.
- Used existing inspected `visibility_tests.py` test-authority isolation in the
  correct repository working directory. An initial direct suite run failed 241
  tests because the active installation authority rejected disposable test-store
  creation; a wrong-directory wrapper attempt was interrupted. Neither run is
  counted as passing. Correct isolation changes only a process-local authority
  pointer; it does not modify installation configuration or relax production rules.
- Private preservation verifier: **70 historical cutoff views**, **11 Nov5/Nov6
  availability boundaries**, and **1707 protected file hashes** pass. Source
  attachments, frozen fixtures/manifests, tools, diagnosis and recovery material
  remain unchanged against the C1 baseline.
- Four actual scripted-model graph runs on the existing disposable C1 copy,
  socket/DNS/requests/curl networking denied. Selected narrative evidence IDs
  reach Market Analyst; funding and macro context remain present. These validate
  existing evidence visibility, not nonexistent new C2 market evidence.
- Inspected spot/source/store modules pass Ruff and AST syntax checks. No product
  Python code changed. Documentation whitespace/staged diff checked before commit.

| Graph cutoff UTC | Narrative chars | Mixed chars | Largest prompt chars |
| --- | ---: | ---: | ---: |
| Nov 5 03:27:10.527275 | 5744 | 15810 | 23418 |
| Nov 5 03:27:26.528491 | 5429 | 15441 | 23049 |
| Nov 6 02:38:10.235518 | 5429 | 15441 | 22953 |
| Nov 6 02:38:29.353157 | 5429 | 15448 | 22960 |

All narrative/mixed/individual limits pass. Intermediate graph counts need not
equal prior private harness outputs; final post-session counts match C1. Scripted
model output is scaffolding. An unavailable historical settlement-price message
occurred under denied networking; no fresh price or trade decision is claimed.
Private verification script/results remain outside Git; only this handoff is
the scoped repository change. No new C2 edge-case acceptance claim is made.

Production absolute authority remained read-only:
`C:\Users\Admin\.codex\.chatgpt-projects\g-p-6abd2d4723108191b62604f41eb86231\local-runtime\information.sqlite3`.
Observed 1291 observations, 146 source histories, 171 coverage rows and 0 gaps;
SQLite integrity `ok`, foreign-key check empty. Required SHA256:
`ea3739b621e02f188b0f19c45203ba29e632bcd8464679b2cd214140874800f2`.
Zero gaps does not establish continuous historical coverage.

## Security and next action

No downloads/installers, credentials, execution-policy or Defender settings,
exclusions, bypasses or persistent scheduling. The earlier
`Ransom:PowerShell/FileFix.DZ!MTB` remains unresolved; this session is not a
Defender event-log audit or a verified false-positive finding.

Next prerequisite: establish an applicable official permission/exception for one
venue covering automated public spot depth/trades, private durable retention and
internal AI inference (including any third-party processing), with redistribution
kept separately restricted. This can be free written clarification or another
eligible free venue; paid access is outside scope. No provider message was sent.
Then resume isolated implementation and its C2 edge-case/PIT tests. Only after
those pass should a separately approved bounded real collection be proposed,
with exact endpoints, request count, timing, retention and stop conditions.
Production collection remains separately unauthorized. No Phase 4–6 advancement.
