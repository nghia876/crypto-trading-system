"""C2-A SYNTHETIC evidence only; no venue payload or production database."""
import json
import socket
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
import requests

from tests.test_graph_end_to_end import PromptCapturingModel, _graph, offline  # noqa: F401
from tests.test_narrative_visibility import mixed_rows
from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.consumer import (
    build_analysis_information,
    render_analysis_information,
)
from tradingagents.information.narrative_events import (
    render_narrative_events,
    selected_narrative_events,
)
from tradingagents.information.observations import Observation
from tradingagents.information.sources import Source
from tradingagents.information.spot_microstructure import (
    DEPTH,
    RECEIPT,
    RIGHTS,
    TRADES,
    SpotEvidenceConfig,
    fetch_spot_once,
    ingest_spot_evidence,
    normalize_spot_response,
    render_spot_evidence,
    selected_spot_evidence,
)
from tradingagents.information.store import ObservationStoreConflict, SQLiteInformationStore

T = datetime(2026, 11, 5, 3, 28, tzinfo=UTC)
VENUES = ("synthetic",)


def config(**kwargs):
    source = Source("test.synthetic.spot", "synthetic", "SYNTHETIC", "https://example.test/offline",
                    "offline synthetic fixture", asset_scope=("BTC/USD",),
                    metric_scope=(DEPTH, TRADES, RECEIPT),
                    metadata=tuple((f"c2_{r}", "permitted") for r in RIGHTS) + (
                        ("c2_free", "true"), ("rights_reference", "SYNTHETIC ONLY; no licence claim"),
                        ("rights_assessed_at", "2026-11-06"), ("c2_redistribution", "denied")))
    return SpotEvidenceConfig(source, "synthetic", enabled=True, price_places=2, quantity_places=8, **kwargs)


def book(**kwargs):
    return {"bids": [["100.00", "1.00000000"], ["99", "2"]],
            "asks": [["101", "3"], ["102", "4"]], **kwargs}


def trades(**kwargs):
    return {"trades": [{"trade_id": "t-1", "price": "100", "quantity": "0.1",
                        "aggressor_side": "buy", "granularity": "raw", **kwargs}]}


def ingest(store, data=None, *, at=T, receipt="r-1", kind=DEPTH, cfg=None):
    return ingest_spot_evidence(store, cfg or config(), kind=kind, data=book() if data is None else data,
                                received_at=at, receipt_id=receipt, configured_venues=VENUES)


@pytest.fixture
def store(tmp_path):
    return SQLiteInformationStore(tmp_path / "DISPOSABLE-SYNTHETIC.sqlite3")


def test_receipts_restart_repeated_fetch_and_exact_pit(store):
    ids = ingest(store, book(snapshot_id="s-1", sequence=10, exchange_event_at=T-timedelta(days=8)))
    assert ingest(store, book(snapshot_id="s-1", sequence=10, exchange_event_at=T-timedelta(days=8))) == ids
    assert not store.view_at(T-timedelta(microseconds=1)).observations
    at = T+timedelta(seconds=10)
    restarted = SQLiteInformationStore(store.path)
    assert ingest(restarted, book(snapshot_id="s-1", sequence=10, exchange_event_at=T-timedelta(days=8)),
                  at=at, receipt="r-2") == ids
    view = restarted.view_at(at)
    assert len(view.observations) == 3  # one evidence + two immutable receipts
    evidence = next(r for r in view.observations if r.metric == DEPTH)
    assert evidence.first_seen_time == evidence.available_at == T
    assert evidence.payload["exchange_event_at"] == (T-timedelta(days=8)).isoformat()
    assert evidence.event_time == T  # local anchor explicitly distinguished
    assert evidence.payload["bids"] == (("100", "1"), ("99", "2"))
    assert evidence.payload["bid_depth_base"] == "3" and evidence.payload["spread_quote"] == "1"
    assert len(view.coverage) == 2 and all(c.status.value == "unknown" for c in view.coverage)
    assert len(view.source_definitions) == 1  # view projects latest; SQLite retains both histories
    with store._connection() as db:
        assert {table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in ("observations", "source_definitions", "coverage", "data_gaps")} == {
                    "observations": 3, "source_definitions": 2, "coverage": 2, "data_gaps": 0}
    with pytest.raises(TypeError):
        evidence.payload["bids"][0] = ("1", "2")


def test_trade_versions_collision_reversion_and_restart(store):
    first = ingest(store, trades(), kind=TRADES)
    with pytest.raises(ObservationStoreConflict):
        ingest(store, trades(price="101"), kind=TRADES)
    second = ingest(store, trades(price="101"), kind=TRADES, at=T+timedelta(seconds=1), receipt="r-2")
    third = ingest(SQLiteInformationStore(store.path), trades(), kind=TRADES,
                   at=T+timedelta(seconds=2), receipt="r-3")
    assert len(set(first+second+third)) == 3
    for offset, ids in enumerate((first, second, third)):
        view = store.view_at(T+timedelta(seconds=offset))
        rows = [r for r in view.observations if r.metric == TRADES]
        assert [r.observation_id for r in rows] == list(ids)
        assert rows[0].first_seen_time == T
    assert len([r for r in view.evidence_history if r.metric == TRADES]) == 3
    assert rows[0].payload["identity_conflict"]


@pytest.mark.parametrize("data", [
    book(bids=[["NaN", "1"]]), book(bids=[[100.0, "1"]]),
    book(bids=[["1e2", "1"]]), book(bids=[["100.001", "1"]]),
    book(bids=[["100", "-1"]]), book(bids=[["100", "0"]]),
    book(bids=[["100", "0.123456789"]]), book(bids=[["99", "1"], ["100", "1"]]),
    book(bids=[["100", "1"], ["100.00", "2"]]),
    book(asks=[["102", "1"], ["101", "1"]]), book(sequence=-1), book(sequence=True),
    book(bids=[["100", "1"]]*501), book(exchange_event_at=datetime(2026, 1, 1)),
])
def test_atomic_malformed_rejection(store, data):
    with pytest.raises(ValueError):
        ingest(store, data)
    assert not store.view_at(T).observations and not store.view_at(T).coverage


@pytest.mark.parametrize("data", [book(bids=[]), book(asks=[]), book(asks=[["99", "1"]]), book(asks=[["100", "1"]])])
def test_empty_crossed_locked_book_is_preserved_as_invalid_not_good_depth(store, data):
    ids = ingest(store, data)
    row = store.evidence_by_ids(ids, T)[0]
    assert row.payload["integrity"] == "invalid" and row.quality.value == "low"
    assert store.view_at(T).coverage[0].status.value == "low_quality"
    assert "integrity=invalid" in "\n".join(render_spot_evidence(store.view_at(T)))


def test_caps_units_unknown_precision_and_sequence_reversal(store):
    cfg = replace(config(level_cap=1), price_places=None, quantity_places=None)
    ingest(store, book(sequence=10), cfg=cfg)
    ingest(store, book(sequence=8), cfg=cfg, at=T+timedelta(seconds=2), receipt="r-2")
    row = selected_spot_evidence(store.view_at(T+timedelta(seconds=2)))[0]
    assert len(row.payload["bids"]) == 1 and row.payload["received_levels"]["bids"] == 2
    assert row.payload["precision_status"] == "unknown" and row.payload["out_of_order_sequence"]
    assert row.payload["base_unit"] == "BTC" and row.payload["quote_unit"] == "USD"
    with pytest.raises(ValueError):
        replace(cfg, instrument="perpetual")


def test_trade_side_requires_explicit_provider_definition_and_granularity(store):
    ids = ingest(store, trades(exchange_event_at=T+timedelta(days=1)), kind=TRADES)
    row = store.evidence_by_ids(ids, T)[0]
    assert row.payload["aggressor_side"] == "unknown" and row.payload["reported_side"] == "buy"
    assert row.payload["clock_skew"] and row.available_at == T
    ids = ingest(store, trades(trade_id="aggregate-1", granularity="aggregated"), kind=TRADES,
                 receipt="r-2", cfg=config(aggressor_definition="SYNTHETIC provider explicitly says taker side"))
    row = store.evidence_by_ids(ids, T)[0]
    assert row.payload["aggressor_side"] == "buy" and row.payload["granularity"] == "aggregated"


@pytest.mark.parametrize("trade", [{"trade_id": None}, {"quantity": "-1"}, {"price": "Infinity"},
                                  {"granularity": "guessed"}, {"aggressor_side": "maker"}])
def test_invalid_trade_fields(store, trade):
    with pytest.raises(ValueError):
        ingest(store, trades(**trade), kind=TRADES)
    assert not store.view_at(T).observations


def test_duplicates_empty_missing_id_jumps_disconnections_and_health(store):
    def fetch():
        return trades()
    ids = fetch_spot_once(store, config(), kind=TRADES, receipt_id="r-1", fetch=fetch,
                          clock=lambda: T, configured_venues=VENUES)
    assert ingest(store, trades(), kind=TRADES, at=T+timedelta(seconds=1), receipt="r-2") == ids
    ingest(store, {"trades": []}, kind=TRADES, at=T+timedelta(seconds=130), receipt="r-3")
    ingest(store, trades(trade_id="t-999"), kind=TRADES, at=T+timedelta(seconds=131), receipt="r-4")
    def disconnected():
        raise ConnectionError("synthetic disconnect; no actual connection")
    assert fetch_spot_once(store, config(), kind=TRADES, receipt_id="r-5", fetch=disconnected,
                           clock=lambda: T+timedelta(seconds=132), configured_venues=VENUES) == ()
    view = store.view_at(T+timedelta(seconds=132))
    assert len(view.coverage) == 5 and view.coverage[-1].status.value in {"unknown", "unavailable"}
    assert len(view.gaps) == 2 and all("unknown" in r.reason for r in view.gaps)
    receipts = [r for r in view.observations if r.metric == RECEIPT]
    assert sum(r.payload["duplicates"] for r in receipts) == 1
    # A jump from t-1 to t-999 is not interpreted as 997 missing executions.
    assert len([r for r in view.observations if r.metric == TRADES]) == 2
    assert any(r.payload["failure"] == "transport_unavailable" for r in receipts)
    assert len(view.observations) == 7
    text = "\n".join(render_spot_evidence(view))
    assert "last_transport_failure=transport_unavailable" in text and "recorded_gaps=2" in text


def test_clock_rollback_and_receipt_time_collision_are_rejected(store):
    ingest(store)
    with pytest.raises(ValueError, match="rollback"):
        ingest(store, at=T-timedelta(seconds=1), receipt="old")
    with pytest.raises(ObservationStoreConflict):
        ingest(store, at=T-timedelta(seconds=1))


@pytest.mark.parametrize("right", RIGHTS)
@pytest.mark.parametrize("value", ["unknown", "denied", "true"])
def test_fail_closed_before_network_or_storage(store, right, value):
    cfg = config()
    metadata = dict(cfg.source.metadata)
    metadata[f"c2_{right}"] = value
    cfg = replace(cfg, source=replace(cfg.source, metadata=tuple(metadata.items())))
    def deny():
        pytest.fail("rights denial must precede transport")
    with pytest.raises(PermissionError):
        fetch_spot_once(store, cfg, kind=DEPTH, receipt_id="denied", fetch=deny, clock=deny, configured_venues=VENUES)
    assert not store.view_at(T).observations


def test_no_default_enabled_venue_and_third_party_rights_rechecked_at_cutoff(store):
    with pytest.raises(PermissionError):
        ingest_spot_evidence(store, config(), kind=DEPTH, data=book(), received_at=T, receipt_id="r")
    ids = ingest(store)
    assert ids and selected_spot_evidence(store.view_at(T))
    metadata = dict(config().source.metadata)
    metadata["c2_third_party_processing"] = "unknown"
    revoked = replace(config().source, version="2", metadata=tuple(metadata.items()))
    later = T+timedelta(seconds=1)
    store.append(MarketDataBatch((), (), later, source_definitions=(revoked,)))
    assert not selected_spot_evidence(store.view_at(later))
    assert selected_spot_evidence(store.view_at(T))


def test_stale_after_threshold_empty_trade_batch_duplicate_ids(store):
    ingest(store, cfg=config(stale_seconds=10))
    assert "stale=True" in "\n".join(render_spot_evidence(store.view_at(T+timedelta(seconds=11))))
    data = trades()
    data["trades"] *= 2
    with pytest.raises(ValueError, match="duplicate"):
        ingest(store, data, kind=TRADES, receipt="duplicates")


def test_extreme_decimals_no_binary_or_context_rounding():
    cfg = replace(config(), price_places=18, quantity_places=18)
    data = book(bids=[["999999999999999999999998.000000000000000001", "999999999999999999999999.000000000000000001"]],
                asks=[["999999999999999999999998.000000000000000002", "0.000000000000000001"]])
    parsed = normalize_spot_response(cfg, DEPTH, data, T)[0]
    assert parsed["spread_quote"] == "0.000000000000000001"
    assert parsed["bid_depth_base"] == "999999999999999999999999.000000000000000001"


def test_explicit_reported_gap_and_opaque_cursor_receipt_collision(store):
    data = {**trades(), "cursor": "opaque:10000000000000001", "continuity": "gap_reported"}
    ingest(store, data, kind=TRADES)
    view = store.view_at(T)
    receipt = next(r for r in view.observations if r.metric == RECEIPT)
    assert receipt.payload["cursor"] == data["cursor"] and len(view.gaps) == 1
    assert "count unknown" in view.gaps[0].reason
    with pytest.raises(ObservationStoreConflict):
        ingest(store, {**data, "cursor": "other"}, kind=TRADES)


def test_conflicting_same_time_rights_definitions_fail_closed(store):
    ingest(store)
    metadata = dict(config().source.metadata)
    metadata["c2_internal_ai_inference"] = "denied"
    denied = replace(config().source, version="denied", metadata=tuple(metadata.items()))
    store.append(MarketDataBatch((), (), T, source_definitions=(denied,)))
    assert not selected_spot_evidence(store.view_at(T))


def test_same_instant_conflicting_identity_and_empty_sequence_collisions(store):
    ingest(store, book(snapshot_id="s1"))
    with pytest.raises(ObservationStoreConflict, match="same local receive time"):
        ingest(store, book(snapshot_id="s1", bids=[["98", "1"]]), receipt="r2")
    ingest(store, {"trades": [], "sequence": 10}, kind=TRADES, receipt="empty")
    with pytest.raises(ObservationStoreConflict):
        ingest(store, {"trades": [], "sequence": 11}, kind=TRADES, receipt="empty")


@pytest.mark.usefixtures("offline")
def test_actual_graph_network_denied_pit_and_world_core_reservations(store, tmp_path, monkeypatch):
    from curl_cffi import requests as curl_requests
    def deny(*args, **kwargs):
        raise AssertionError("C2-A test denies actual networking")
    for target, name in ((socket.socket, "connect"), (socket.socket, "connect_ex"),
                         (socket, "getaddrinfo"), (requests.Session, "request"),
                         (curl_requests.Session, "request"), (curl_requests.AsyncSession, "request")):
        monkeypatch.setattr(target, name, deny)
    old, news = mixed_rows()
    funding = Observation("synthetic-core-funding", "derivatives.binance.usdm.funding", "BTCUSDT",
                           "derivatives.funding_rate.usdm", {"funding_rate": "0.001"}, T, T, T)
    store.append(MarketDataBatch((*old, *news, funding), (), T))
    depth_ids = ingest(store)
    trade_ids = ingest(store, trades(), kind=TRADES, receipt="trades")
    before = T-timedelta(microseconds=1)
    for cutoff in (before, T):
        model = PromptCapturingModel()
        graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
        state, _ = graph.propagate("BTCUSDT", T.date().isoformat(), asset_type="crypto", decision_time=cutoff)
        market = "\n".join(p for p in model.prompts if "get_verified_market_snapshot" in p)
        assert len(state["analysis_information"]) <= 28000 and max(map(len, model.prompts)) <= 28000
        view = store.view_at(cutoff)
        print(json.dumps({"cutoff": cutoff.isoformat(), "narrative_chars": len("\n".join(render_narrative_events(view))),
                          "mixed_chars": len(state["analysis_information"]), "largest_prompt_chars": max(map(len, model.prompts))}))
        assert len("\n".join(render_narrative_events(view))) <= 6000
        assert all(r.observation_id in market for r in selected_narrative_events(view))
        if cutoff == before:
            assert all(i not in market for i in depth_ids+trade_ids)
        else:
            assert all(i in market for i in depth_ids+trade_ids)
            assert "publisher-a" in market and "publisher-b" in market and "synthetic-core-funding" in market
            assert "Macro series:" in market and "Funding rate:" in market
            assert "Original-publisher liquidity:" in market
    rendered = render_analysis_information(build_analysis_information(store, T))
    assert "completeness UNKNOWN" in rendered and "aggressor=unknown" in rendered
