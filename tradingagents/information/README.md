# Information collection and replay

## Phase 1.2 BTC Spot OHLCV

**Purpose:** collect public Binance Spot BTC/USDT one-minute candles and retain
the observation history needed to reconstruct an information view at a decision
time.

**Inputs:** UTC-aware, minute-aligned `start` and `end` bounds (`start`
inclusive, `end` exclusive). Collection is caller-driven; this package does not
schedule or continuously run a poller.

**Output:** normalized `Observation` records and explicit `MarketDataGap`
records. Candle numbers are stored as decimal strings to avoid losing source
precision. Source identity, raw endpoint reference, transformations, candle
event time, and local first-seen/retrieval times are retained.

**Point-in-time rule:** candle open/close times describe the market interval;
they do not prove when this system knew the candle. Eligibility is determined
from `first_seen_time`, `retrieved_at`, and publication time when present. A
REST backfill retrieved today is therefore unavailable to a replay before its
retrieval time. A changed candle is appended as a new version and only
supersedes the earlier version after the correction's availability time.

**Durable replay:** `SQLiteInformationStore` appends observations and gaps to a
filesystem database. `view_at(decision_time)` filters both by their availability
time, returns the active revision of each observation, and reports only gaps not
yet filled by an eligible observation. Gap history remains stored. Repeating an identical
append is safe, including an unchanged candle fetched after a collector restart.
The store links a changed same-key candle to its prior stored version when the
collector has no in-memory revision link. Reusing an observation ID for
different content raises `ObservationStoreConflict`.

```python
from datetime import UTC, datetime

from tradingagents.information import BinanceSpotOHLCVCollector, SQLiteInformationStore

collector = BinanceSpotOHLCVCollector()
batch = collector.collect(
    datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
    datetime(2026, 1, 1, 1, 0, tzinfo=UTC),
)
store = SQLiteInformationStore("data/information.sqlite3")
store.append(batch)
view = store.view_at(datetime.now(UTC))
```

## Dependencies and downstream impact

- Python standard-library SQLite plus the repository's existing `requests`
  dependency; no credentials or trading endpoints are used.
- Downstream market-state code should consume `view_at(T)`, preserve decimal
  strings until choosing an explicit numeric representation, and handle gaps
  and stale freshness explicitly.
- The database is append-only at the observation level. This component does not
  schedule polling, make cross-exchange comparisons, provide an analytics
  schema, or claim source reliability. Binance source reliability remains
  `UNKNOWN` until measured.
- The store currently expects JSON-compatible payload values. The source
  registry definition is in code and is not copied into each SQLite database.

## Phase 2 initial slice: reproducible BTC spot state

`build_btc_spot_market_state(view_at_T)` creates a deterministic spot snapshot
from the replay view. It currently includes the latest closed BTCUSDT 1-minute
OHLC, base and quote volume, trade count, latest consecutive one-bar close
return, and population standard deviation of close-to-close percentage returns
(up to 20 returns by default). Return and volatility calculations use only the
contiguous candle run ending at the latest bar; they do not bridge gaps or reuse
returns from before a gap. Volatility is not annualized. Prices, volumes, and
derived values use `Decimal`.

Only Binance observations eligible at the view cutoff and whose candle
`close_time` is at or before that cutoff contribute. Freshness age is measured
from the latest candle `close_time`; the default is `fresh` through two minutes
and `stale` afterward. A view with no eligible closed candle reports
`freshness="unknown"`. This is a spot-state layer, not a derived market regime
or trade recommendation. The combined state builder is described below.

Example:

```python
from tradingagents.information import build_btc_market_state, build_btc_spot_market_state

view = store.view_at(decision_time)
spot_state = build_btc_spot_market_state(view)
state = build_btc_market_state(view)
```

The combined `build_btc_market_state(view)` adds the latest eligible USDⓈ-M
funding rate, open-interest snapshot, mark/index basis, spot/perpetual
divergence, symbol trading status, recent liquidation-stream snapshot count,
Treasury 10-year yield, selected macro series, and upcoming scheduled events.
Each value retains its evidence and availability time. Funding freshness
defaults to 12 hours; open interest and perpetual price/status freshness default
to five minutes. If an eligible record is not in the view, its state is
`unknown`. These are initial defaults, not empirically calibrated thresholds.

Focused coverage is in `tests/test_btc_spot_market_state.py`.

## Phase 2 derivatives acquisition slice

`BinanceUsdmDerivativesCollector` adds two caller-driven public endpoints for
BTCUSDT:

- USDⓈ-M funding history (`/fapi/v1/fundingRate`), where `fundingTime` is the
  settlement event time. A historical row collected now is available to replay
  only from its local retrieval/first-seen time. Binance documents inclusive
  time bounds, ascending results, and up to 1,000 rows per call; its current
  documentation does not specify total archive depth.
- Current open interest (`/fapi/v1/openInterest`), whose response `time` is an
  exchange transaction time. The endpoint is a current snapshot, so durable
  history depends on prospective caller polling and local persistence.
- Mark and index prices (`/fapi/v1/premiumIndex`), whose response time bounds
  a current snapshot. `build_btc_market_state` derives mark/index basis and,
  when the spot candle and mark snapshot are within 90 seconds, mark-versus-spot
  divergence.
- Contract status (`/fapi/v1/exchangeInfo`) for the BTCUSDT perpetual symbol.
  This is symbol trading status, not an exchange-wide health signal.

The separate sampled open-interest history endpoint
(`/futures/data/openInterestHist`) documents only the latest month; its periods
with no trades can be omitted. This collector does not use that series. The
source metadata and observations preserve the distinction between event time
and local availability. A one-time unauthenticated smoke check on 2026-10-26
returned three funding rows for the prior 24 hours and one current open-interest
snapshot. All four records were persisted to a temporary SQLite database,
reopened, and replayed: zero were visible just before their recorded
availability, and all four were visible at or after availability. This confirms
basic endpoint and replay behavior only; reliability remains `UNKNOWN` because
one smoke check does not measure ongoing availability or data quality.

Official endpoint references: [funding rate history](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History), [current open interest](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest), and [open-interest statistics](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics).

The [mark price endpoint](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) provides both mark and index prices; the same catalog documents exchange information and symbol status. The public `!forceOrder@arr` stream is normalized by `parse_binance_usdm_liquidation_event`. Binance describes it as a maximum one largest-order snapshot per symbol per second, so the stored records are censored samples, not complete liquidation history. The code parses supplied stream messages but does not manage a persistent WebSocket connection.

```python
from tradingagents.information import BinanceUsdmDerivativesCollector

collector = BinanceUsdmDerivativesCollector()
funding = collector.collect_funding(start, end)
open_interest = collector.collect_open_interest()
store.append(funding)
store.append(open_interest)
```

Focused mocked coverage is in `tests/test_binance_usdm_collector.py`.

## Scheduled macro event contract

`ScheduledMacroEvent` converts a normalized calendar entry into the existing
observation envelope, with the scheduled event time kept separate from local
first-seen/retrieval time. `upcoming_macro_events(view_at_T)` returns only
future events that were available by `T`. A historical calendar row ingested
today therefore cannot appear in an earlier replay, even when its event date is
in the future relative to that replay. The source event ID is the storage
subject, so distinct releases at the same time remain distinct. A reschedule
appends a new version under the same source/event ID; replay uses the latest
version known by the cutoff, and a cancellation suppresses that event.

`FOMCCalendarCollector` downloads the public [Federal Reserve FOMC calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm)
without credentials and normalizes meeting date ranges. The page supplies dates,
not intraday meeting times, so records use `time_precision="date"` and a local
date window ending at midnight after the final meeting day. A meeting is marked
tentative until the preceding meeting has concluded, which matches the calendar's
confirmation rule. This avoids inventing a release timestamp. Meeting IDs
are stable by year and listed order, so a date change can supersede the prior
schedule at replay time.

A live unauthenticated read on 2026-10-26 parsed eleven upcoming date windows,
including the 2028 date in the page note. A SQLite replay check after reopening
the temporary database returned no meetings just before local retrieval and
all eleven at retrieval. Ten windows were marked tentative based on the
preceding-meeting confirmation rule. This validates the current parser and
availability rule, not long-term feed reliability. Calendar pages do not
provide a per-event publication time, so local retrieval/first-seen time
remains the conservative availability bound.

The BLS ICS and earlier release-calendar HTML requests returned HTTP 403 in
this environment. The official [annual schedule page](https://www.bls.gov/schedule/2026/)
is now supported by a caller-driven parser and collector; mocked contract tests
pass. A live request from the repository runtime returned HTTP 403. The parser
uses dates and Eastern Times shown on the schedule, while local retrieval time
remains the availability bound. A Treasury XML feed request timed out
during the earlier event source investigation. Treasury yield collection is
now covered by the DGS10 slice below. The FRED API requires a registered key,
but FRED graph CSV downloads are public; the new collector uses those downloads
and conservatively records local retrieval as availability.

`BEAReleaseCalendarCollector` uses BEA's public [release schedule](https://www.bea.gov/news/schedule/full)
for the current year and its [next-year schedule](https://www.bea.gov/news/schedule/next-year)
for the following year. It normalizes explicitly scheduled GDP, personal
income/outlays, trade, and other BEA releases. “To Be Announced” entries are
skipped because no time is supplied. Fixture tests pass. A one-time live
repository-runtime read fetched the upcoming entries; SQLite replay exposed
zero before local retrieval and all at retrieval. This does not establish
ongoing reliability.

```python
from tradingagents.information import FOMCCalendarCollector, upcoming_macro_events

batch = FOMCCalendarCollector().collect()
store.append(batch)
known_upcoming = upcoming_macro_events(store.view_at(decision_time))
```

Focused coverage is in `tests/test_scheduled_events.py`.

## Phase 1.2 acceptance and verification

- A mocked public-source response normalizes BTC/USDT candles and writes them to
  SQLite.
- After reopening the database, replay before ingestion excludes the candle;
  replay after ingestion includes it; a later correction only appears after its
  own ingestion time.
- Repeated appends are idempotent, gaps are replay-time-filtered, and an
  observation ID collision with changed content is rejected. Identical candles
  across collector restarts are deduplicated without moving first-seen time.
- Focused tests are in `tests/test_binance_spot_collector.py`,
  `tests/test_information_contract.py`, and `tests/test_information_store.py`.
- One-time live unauthenticated Binance Spot and USDⓈ-M smoke checks completed;
  these do not measure ongoing source reliability.
- No scheduler, full project test suite, or production retention policy has
  been verified in this phase.

## Public FRED macro series

`FredPublicSeriesCollector` downloads selected [FRED graph CSV](https://fred.stlouisfed.org/help/data/downloading/using-the-download-data-link/) series without an API key. It currently collects the 2-year Treasury constant-maturity rate (`DGS2`), WTI spot crude oil (`DCOILWTICO`), nominal broad U.S. dollar index (`DTWEXBGS`), Chicago Fed National Financial Conditions Index (`NFCI`), S&P 500 (`SP500`), and CBOE Volatility Index (`VIXCLS`). The broad dollar index is a contextual proxy, not the ICE DXY. S&P 500 and VIX are subject to their originating providers' data terms; this project does not redistribute downloaded values.

The observation date is reference time only. FRED graph CSV does not provide historical release timestamps or vintage availability, so records use local first-seen/retrieval time and cannot be replayed before ingestion. Corrections are retained as later versions by the information store. `build_macro_state(view_at_T)` returns deterministic values, evidence IDs, age, freshness, and proxy metadata; the combined BTC state uses the same point-in-time view.

The collector is caller-driven. A one-time repository-runtime check fetched three recent WTI rows and confirmed they were unavailable just before local retrieval and visible at retrieval. This does not measure source reliability. Selected series have different originating agencies and data terms; the source registry records those origins, and this project does not redistribute downloaded series values.

## Phase 2 acceptance and closure status

The blueprint's Phase 2 exit criteria are reproducible market/derivatives/macro
state, freshness monitoring, and historical reconstruction. **Acceptance: PASS;
Phase 2 can close against those exit criteria.** The review distinguishes these
criteria from broader source coverage and one-time live-access evidence:

- **Reproducible state — PASS.** `build_btc_market_state(view_at_T)` deterministically
  derives spot, funding, open interest, perpetual basis and spot divergence,
  contract status, sampled liquidation evidence, Treasury DGS10, selected FRED
  series, and upcoming FOMC/BLS/BEA events from one point-in-time view. Values
  preserve their evidence IDs and availability times. Liquidation records are
  censored snapshots, not a complete tape.
- **Freshness monitoring — PASS.** State builders report `fresh`, `stale`, or
  `unknown` for spot, funding, open interest, mark price, contract status,
  Treasury yield, and selected macro series. Freshness is evaluated when a
  caller builds state; no scheduler or alerts are specified by the Phase 2 exit
  criteria.
- **Historical reconstruction — PASS for locally ingested information.** The
  SQLite view gates on `max(first_seen_time, retrieved_at, publication_time)`
  when publication time exists. Reference/event dates do not establish
  availability. Tests cover replay before and after ingestion, revisions,
  rescheduling, and late data; replay cannot reconstruct source publication
  times or historical vintages that providers do not supply.
- **Macro universe and calendar breadth — PARTIAL.** Rates, oil, a nominal broad
  dollar index, financial conditions, S&P 500, VIX, FOMC, BLS, and BEA are
  represented. The dollar series is explicitly a broad-index proxy, not the ICE
  DXY. BLS and BEA are not exhaustive coverage of major U.S. releases; the
  blueprint does not specify an exact dollar-index provider or require a live
  BLS request as Phase 2 exit evidence.
- **Live-source evidence — PARTIAL.** Recorded one-time checks include Spot and
  USDⓈ-M observations, FOMC, BEA, and WTI. They demonstrate endpoint/parser and
  local replay behavior only, not ongoing reliability. The BLS annual page
  returned HTTP 403 in this environment (**runtime access BLOCKED**); Treasury
  live persistence/reopen replay remains **NOT VERIFIED** after its earlier
  timeout. These are runtime evidence limitations, not failures of the
  documented replay contract.
- **Focused automated verification — PASS.** Nine focused test files passed 70
  tests with shared `tests/conftest.py` disabled. Ruff lint, Ruff format check,
  and `git diff --check` pass for the Phase 2 changes.
- **Full project test suite — NOT VERIFIED.** Shared test setup requires
  `yfinance` and `curl_cffi`, unavailable in this environment.

Phase 2 is accepted against its stated exit criteria. The partial source
coverage above should remain visible when interpreting the macro state; it does
not change the acceptance result or imply that uncollected values are known.
## Treasury macro observation contract (DGS10)

`TreasuryYieldCollector` fetches the Treasury's public current-year daily par-yield CSV and normalizes only its `10 Yr` column. The stable source ID, metric (`macro.treasury_10y_par_yield_pct`), U.S. subject, observation/reference date (`event_time` and `effective_time`), units, endpoint, and transformation are stored in the existing `Observation` envelope. The CSV does not expose an exact publication timestamp or vintage history, so `publication_time` stays unset and `first_seen_time`/`retrieved_at` conservatively determine replay availability. Backfilled rows are never available before local ingestion.

A changed value for the same source, subject, metric, and event date is appended as a new observation; the store links it to the prior version, preserving what was known before the later retrieval. `build_treasury_yield_state` uses only the supplied point-in-time view and reports the latest rate, evidence ID, observation age, and a configurable freshness label (default stale after three calendar days). This is one daily 10-year par-yield proxy, not a broad macro state or a real-time yield. The collector is caller-driven; freshness thresholds are initial defaults and source reliability is unmeasured. The Treasury documents CSV downloads and separate static historical archives, but does not provide old data vintages in the current feed.


## Phase 3 first slice: official monetary announcements

See `docs/project-handoff/PHASE_3_ARCHITECTURE.md` for timing, identity,
credibility, independence, lifecycle, coverage and replay contracts. A caller can
poll and append without enabling any trading capability:

```python
from tradingagents.information.narrative_events import FedMonetaryCollector
from tradingagents.information.store import SQLiteInformationStore

batch = FedMonetaryCollector().collect()
SQLiteInformationStore("information.sqlite3").append(batch)
```

The existing optional graph information-store setting exposes eligible events
alongside macro/calendar and micro market-state evidence, within the same total
28,000-character context budget. Headlines are source claims; independent
confirmation, contradictions and market reaction remain unknown or unsearched.
No scheduler, causal inference, full-release extraction, or complete news coverage
is claimed. Failures raise `MarketDataCollectionError`; the caller owns operational
failure recording and retries. This does not complete Phase 3.
