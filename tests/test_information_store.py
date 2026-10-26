"""Durable append and point-in-time replay tests for the information store."""

from datetime import UTC, datetime

import pytest

from tradingagents.information import (
    BinanceSpotOHLCVCollector,
    MarketDataBatch,
    MarketDataGap,
    Observation,
    ObservationStoreConflict,
    SQLiteInformationStore,
)


def make_observation(
    observation_id: str,
    *,
    close: str,
    available_at: datetime,
    supersedes: str | None = None,
) -> Observation:
    return Observation(
        observation_id=observation_id,
        source_id="market.binance.spot",
        subject="BTCUSDT",
        metric="spot_ohlcv.1m",
        payload={"open": "100.0", "close": close, "interval": "1m"},
        event_time=datetime(2026, 1, 1, tzinfo=UTC),
        first_seen_time=available_at,
        retrieved_at=available_at,
        effective_time=datetime(2026, 1, 1, tzinfo=UTC),
        raw_reference="https://example.test/kline",
        quality="unknown",
        supersedes_observation_id=supersedes,
    )


def test_reopen_store_reconstructs_only_known_revision_at_each_cutoff(tmp_path):
    database = tmp_path / "information.sqlite3"
    store = SQLiteInformationStore(database)
    original_time = datetime(2026, 1, 1, 0, 3, 30, tzinfo=UTC)
    revision_time = datetime(2026, 1, 1, 0, 4, 30, tzinfo=UTC)
    gap = MarketDataGap(
        "BTCUSDT", "spot_ohlcv.1m", datetime(2026, 1, 1, 0, 1, tzinfo=UTC), original_time
    )
    original = make_observation("version-1", close="100.5", available_at=original_time)
    revision = make_observation(
        "version-2", close="100.6", available_at=revision_time, supersedes="version-1"
    )

    store.append(MarketDataBatch((original,), (gap,), original_time))
    store.append(MarketDataBatch((revision,), (), revision_time))
    store = SQLiteInformationStore(database)  # simulate a process restart

    before_ingestion = store.view_at(datetime(2026, 1, 1, 0, 3, 29, tzinfo=UTC))
    before_revision = store.view_at(datetime(2026, 1, 1, 0, 4, 29, tzinfo=UTC))
    after_revision = store.view_at(revision_time)

    assert before_ingestion.observations == ()
    assert before_ingestion.gaps == ()
    assert [item.observation_id for item in before_revision.observations] == ["version-1"]
    assert before_revision.observations[0].payload["close"] == "100.5"
    assert len(before_revision.gaps) == 1
    assert [item.observation_id for item in after_revision.observations] == ["version-2"]
    assert after_revision.observations[0].payload["close"] == "100.6"
    assert after_revision.observations[0].supersedes_observation_id == "version-1"


def test_reappending_same_batch_is_idempotent(tmp_path):
    store = SQLiteInformationStore(tmp_path / "information.sqlite3")
    at = datetime(2026, 1, 1, 0, 3, 30, tzinfo=UTC)
    observation = make_observation("version-1", close="100.5", available_at=at)
    gap = MarketDataGap(
        "BTCUSDT", "spot_ohlcv.1m", observation.event_time.replace(minute=1), at
    )
    batch = MarketDataBatch((observation,), (gap,), at)

    store.append(batch)
    store.append(batch)

    view = store.view_at(at)
    assert len(view.observations) == 1
    assert len(view.gaps) == 1


def test_store_deduplicates_restarted_collector_and_links_unannounced_revision(tmp_path):
    store = SQLiteInformationStore(tmp_path / "information.sqlite3")
    first_time = datetime(2026, 1, 1, 0, 3, 30, tzinfo=UTC)
    duplicate_time = datetime(2026, 1, 1, 0, 4, 30, tzinfo=UTC)
    revision_time = datetime(2026, 1, 1, 0, 5, 30, tzinfo=UTC)
    first = make_observation("version-1", close="100.5", available_at=first_time)
    duplicate = make_observation("restart-version-1", close="100.5", available_at=duplicate_time)
    revision = make_observation("restart-version-2", close="100.6", available_at=revision_time)

    store.append(MarketDataBatch((first,), (), first_time))
    store.append(MarketDataBatch((duplicate,), (), duplicate_time))
    store.append(MarketDataBatch((revision,), (), revision_time))

    prior_view = store.view_at(duplicate_time)
    latest_view = store.view_at(revision_time)
    assert [item.observation_id for item in prior_view.observations] == ["version-1"]
    assert prior_view.observations[0].available_at == first_time
    assert [item.observation_id for item in latest_view.observations] == ["restart-version-2"]
    assert latest_view.observations[0].supersedes_observation_id == "version-1"


def test_late_candle_resolves_gap_only_after_its_ingestion_time(tmp_path):
    store = SQLiteInformationStore(tmp_path / "information.sqlite3")
    event_time = datetime(2026, 1, 1, tzinfo=UTC)
    gap_time = datetime(2026, 1, 1, 0, 3, 30, tzinfo=UTC)
    available_time = datetime(2026, 1, 1, 0, 4, 30, tzinfo=UTC)
    gap = MarketDataGap("BTCUSDT", "spot_ohlcv.1m", event_time, gap_time)
    observation = make_observation("late-candle", close="100.5", available_at=available_time)

    store.append(MarketDataBatch((), (gap,), gap_time))
    assert len(store.view_at(gap_time).gaps) == 1
    store.append(MarketDataBatch((observation,), (), available_time))

    assert store.view_at(datetime(2026, 1, 1, 0, 4, 29, tzinfo=UTC)).gaps
    resolved = store.view_at(available_time)
    assert [item.observation_id for item in resolved.observations] == ["late-candle"]
    assert resolved.gaps == ()


def test_observation_id_conflict_rolls_back_the_append(tmp_path):
    store = SQLiteInformationStore(tmp_path / "information.sqlite3")
    at = datetime(2026, 1, 1, 0, 3, 30, tzinfo=UTC)
    original = make_observation("version-1", close="100.5", available_at=at)
    conflicting = make_observation("version-1", close="101.5", available_at=at)
    store.append(MarketDataBatch((original,), (), at))

    with pytest.raises(ObservationStoreConflict, match="reused with different content"):
        store.append(MarketDataBatch((conflicting,), (), at))

    view = store.view_at(at)
    assert len(view.observations) == 1
    assert view.observations[0].payload["close"] == "100.5"


def test_revision_cannot_supersede_a_different_subject_or_metric(tmp_path):
    store = SQLiteInformationStore(tmp_path / "information.sqlite3")
    at = datetime(2026, 1, 1, 0, 3, 30, tzinfo=UTC)
    original = make_observation("version-1", close="100.5", available_at=at)
    unrelated = Observation(
        observation_id="unrelated-version",
        source_id=original.source_id,
        subject="ETHUSDT",
        metric=original.metric,
        payload={"close": "3000"},
        event_time=original.event_time,
        first_seen_time=at,
        retrieved_at=at,
        supersedes_observation_id=original.observation_id,
    )
    store.append(MarketDataBatch((original,), (), at))
    with pytest.raises(ObservationStoreConflict, match="revision must supersede the same"):
        store.append(MarketDataBatch((unrelated,), (), at))

    view = store.view_at(at)
    assert {item.observation_id for item in view.observations} == {"version-1"}


def test_point_in_time_cutoff_must_be_timezone_aware(tmp_path):
    store = SQLiteInformationStore(tmp_path / "information.sqlite3")
    with pytest.raises(ValueError, match="timezone-aware"):
        store.view_at(datetime(2026, 1, 1))


def test_memory_database_is_rejected_because_it_is_not_durable():
    with pytest.raises(ValueError, match="filesystem database path"):
        SQLiteInformationStore(":memory:")


class KlineResponse:
    status_code = 200
    headers = {}

    def __init__(self, rows):
        self.rows = rows

    def raise_for_status(self):
        return None

    def json(self):
        return self.rows


class KlineSession:
    def __init__(self):
        self.close_value = "100.5"

    def get(self, url, *, params, timeout):
        opened = 1_767_225_600_000
        return KlineResponse(
            [[opened, "100", "101", "99", self.close_value, "2.5", opened + 59_999,
              "250.0", 10, "1.1", "110.0", "0"]]
        )


def test_collector_to_durable_replay_preserves_ingestion_and_revision_times(tmp_path):
    database = tmp_path / "collector-replay.sqlite3"
    session = KlineSession()
    now = datetime(2026, 1, 1, 0, 3, 30, tzinfo=UTC)
    collector = BinanceSpotOHLCVCollector(session=session, clock=lambda: now)
    store = SQLiteInformationStore(database)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 1, 0, 1, tzinfo=UTC)

    first = collector.collect(start, end)
    store.append(first)
    now = datetime(2026, 1, 1, 0, 4, 30, tzinfo=UTC)
    session.close_value = "100.6"
    revised = collector.collect(start, end)
    store.append(revised)
    replay = SQLiteInformationStore(database)

    assert replay.view_at(datetime(2026, 1, 1, 0, 3, 29, tzinfo=UTC)).observations == ()
    assert replay.view_at(datetime(2026, 1, 1, 0, 4, 0, tzinfo=UTC)).observations[0].payload["close"] == "100.5"
    latest = replay.view_at(now).observations
    assert latest[0].payload["close"] == "100.6"
    assert latest[0].supersedes_observation_id == first.observations[0].observation_id
