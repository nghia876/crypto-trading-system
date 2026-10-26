"""Tests for Treasury yield collection and point-in-time replay."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from tradingagents.information import (
    MarketDataCollectionError,
    SQLiteInformationStore,
    TreasuryYieldCollector,
    build_treasury_yield_state,
    parse_treasury_yield_csv,
)

T0 = datetime(2026, 10, 26, 12, tzinfo=UTC)
CSV = "Date,1 Mo,10 Yr\n10/23/2026,3.5,4.25\n10/26/2026,3.6,4.30\n"


def test_treasury_rows_use_local_availability_and_state_freshness(tmp_path):
    batch = parse_treasury_yield_csv(CSV, retrieved_at=T0, year=2026)
    assert len(batch.observations) == 2
    assert all(item.publication_time is None for item in batch.observations)
    store = SQLiteInformationStore(tmp_path / "info.sqlite")
    store.append(batch)
    before = store.view_at(T0 - timedelta(microseconds=1))
    after = store.view_at(T0)
    assert before.observations == ()
    state = build_treasury_yield_state(after)
    assert state.yield_pct == Decimal("4.30")
    assert state.freshness == "fresh"
    assert state.evidence_observation_id == batch.observations[-1].observation_id
    assert build_treasury_yield_state(store.view_at(T0 + timedelta(days=4))).freshness == "stale"


def test_treasury_revised_value_is_visible_only_after_new_ingestion(tmp_path):
    original = parse_treasury_yield_csv(CSV, retrieved_at=T0, year=2026).observations[-1]
    revised_csv = CSV.replace("4.30", "4.31")
    revised = parse_treasury_yield_csv(
        revised_csv, retrieved_at=T0 + timedelta(days=1), year=2026
    ).observations[-1]
    store = SQLiteInformationStore(tmp_path / "info.sqlite")
    from tradingagents.information import MarketDataBatch

    store.append(MarketDataBatch((original,), (), T0))
    store.append(MarketDataBatch((revised,), (), T0 + timedelta(days=1)))
    old_view = store.view_at(T0 + timedelta(hours=1))
    new_view = store.view_at(T0 + timedelta(days=1))
    assert build_treasury_yield_state(old_view).yield_pct == Decimal("4.30")
    assert build_treasury_yield_state(new_view).yield_pct == Decimal("4.31")
    assert len(new_view.observations) == 1


def test_collector_uses_current_year_public_csv_and_reports_transport_failure():
    class Response:
        text = CSV

        def raise_for_status(self):
            pass

    class Session:
        def __init__(self):
            self.url = None

        def get(self, url, timeout):
            self.url = url
            return Response()

    session = Session()
    collector = TreasuryYieldCollector(session=session, clock=lambda: T0)
    assert len(collector.collect().observations) == 2
    assert session.url.endswith("/2026/all")

    class BrokenSession:
        def get(self, *_args, **_kwargs):
            import requests

            raise requests.Timeout("timeout")

    with pytest.raises(MarketDataCollectionError, match="Treasury rates request failed"):
        TreasuryYieldCollector(session=BrokenSession(), clock=lambda: T0).collect()
