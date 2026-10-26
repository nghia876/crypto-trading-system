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

## Acceptance and verification

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
- No live Binance call, scheduler, full project test suite, or production
  retention policy has been verified in this phase.
