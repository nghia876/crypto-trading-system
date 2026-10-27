"""Point-in-time public FRED graph CSV contract tests."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from tradingagents.information import (
    FRED_SERIES,
    FredPublicSeriesCollector,
    MarketDataCollectionError,
    SQLiteInformationStore,
    build_macro_state,
    parse_fred_graph_csv,
)

RETRIEVED = datetime(2026, 10, 26, 12, tzinfo=UTC)
SPEC = next(spec for spec in FRED_SERIES if spec.series_id == "DTWEXBGS")


def test_fred_graph_csv_is_available_only_from_local_retrieval():
    batch = parse_fred_graph_csv(
        "observation_date,DTWEXBGS\n2026-10-22,121.4\n2026-10-23,.\n",
        spec=SPEC,
        retrieved_at=RETRIEVED,
    )

    assert len(batch.observations) == 1
    observation = batch.observations[0]
    assert observation.event_time == datetime(2026, 10, 22, tzinfo=UTC)
    assert observation.available_at == RETRIEVED
    assert observation.publication_time is None
    assert observation.payload["proxy_for"] == SPEC.proxy_for
    assert observation.unit == SPEC.units
    assert observation.schema_version == "fred-series-v1"
    assert batch.coverage[0].evidence_ids == tuple(item.observation_id for item in batch.observations)
    assert batch.source_definitions == (SPEC.source,)


def test_macro_state_replays_only_known_latest_values_and_reports_freshness(tmp_path):
    store = SQLiteInformationStore(tmp_path / "information.sqlite3")
    batch = parse_fred_graph_csv(
        "observation_date,DTWEXBGS\n2026-10-20,120.0\n2026-10-22,121.4\n",
        spec=SPEC,
        retrieved_at=RETRIEVED,
    )
    store.append(batch)

    before = build_macro_state(store.view_at(RETRIEVED - timedelta(seconds=1)))
    assert all(series.value is None for series in before.series)

    after = build_macro_state(store.view_at(RETRIEVED))
    dollar = next(series for series in after.series if series.series_id == "DTWEXBGS")
    assert dollar.value == Decimal("121.4")
    assert dollar.freshness == "fresh"
    assert dollar.evidence_observation_id == batch.observations[-1].observation_id
    assert dollar.proxy_for == SPEC.proxy_for

    stale = build_macro_state(store.view_at(RETRIEVED + timedelta(days=10)))
    assert (
        next(series for series in stale.series if series.series_id == "DTWEXBGS").freshness
        == "stale"
    )


def test_fred_parser_rejects_wrong_series_and_future_reference_date():
    with pytest.raises(MarketDataCollectionError, match="does not match"):
        parse_fred_graph_csv(
            "observation_date,DCOILWTICO\n2026-10-20,100.0\n",
            spec=SPEC,
            retrieved_at=RETRIEVED,
        )

    with pytest.raises(MarketDataCollectionError, match="future"):
        parse_fred_graph_csv(
            "observation_date,DTWEXBGS\n2026-10-27,121.4\n",
            spec=SPEC,
            retrieved_at=RETRIEVED,
        )


def test_fred_collector_uses_public_graph_csv_without_api_key():
    class Response:
        text = "observation_date,DCOILWTICO\n2026-10-20,107.89\n"

        def raise_for_status(self):
            return None

    class Session:
        calls = []

        def get(self, url, *, params, timeout):
            self.calls.append((url, params, timeout))
            return Response()

    session = Session()
    collector = FredPublicSeriesCollector(session=session, clock=lambda: RETRIEVED)
    batch = collector.collect("DCOILWTICO", start=date(2026, 10, 1), end=date(2026, 10, 26))

    assert len(batch.observations) == 1
    assert session.calls[0][1] == {
        "id": "DCOILWTICO",
        "cosd": "2026-10-01",
        "coed": "2026-10-26",
    }
