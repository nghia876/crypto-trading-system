"""Synthetic official-wire-shaped fixtures; never contact an exchange."""
import copy
import json
from datetime import timedelta
from decimal import Decimal

import pytest
import requests

from tests.test_graph_end_to_end import PromptCapturingModel, _graph, offline  # noqa: F401
from tests.test_spot_microstructure import T
from tradingagents.information.kraken_spot import (
    PRIVATE,
    SOURCE_ID,
    PublicClient,
    acquire,
    collect,
    configuration,
    parse_depth,
    parse_price,
    parse_trades,
    persist,
)
from tradingagents.information.spot_microstructure import (
    DEPTH,
    TRADES,
    normalize_spot_response,
    render_spot_evidence,
)
from tradingagents.information.store import SQLiteInformationStore


def envelope(value):
    return {"error": [], "result": value}


def wires():
    return {
        "AssetPairs": envelope({"XXBTZUSD": {"base": "XXBT", "quote": "ZUSD", "altname": "XBTUSD",
            "wsname": "XBT/USD", "status": "online", "pair_decimals": 1, "lot_decimals": 8}}),
        "Ticker": envelope({"XXBTZUSD": {"c": ["100.10000", "0.01000000"]}}),
        "Depth": envelope({"XXBTZUSD": {"bids": [["100.10000", "1.00000000", 1793849000]],
                                       "asks": [["100.20000", "2.00000000", 1793849001]]}}),
        "Trades": envelope({"XXBTZUSD": [
            ["100.10000", "0.01000000", Decimal("1793849000.123456789"), "b", "m", "", 1],
            ["100.20000", "0.02000000", Decimal("1793849001.123456"), "s", "l", "", 4]],
            "last": "1793849001123456789"}),
    }


class FixtureClient:
    def __init__(self, data=None, offset=0):
        self.data, self.calls, self.offset = data or wires(), [], offset

    def get(self, endpoint):
        self.calls.append(endpoint)
        return {"endpoint": endpoint, "url": "synthetic:" + endpoint, "raw": "PRIVATE_RAW_SENTINEL",
                "sha256": "synthetic", "received_at": T + timedelta(seconds=self.offset + len(self.calls)),
                "wire": self.data[endpoint]}


def test_disabled_before_transport_and_config_metadata():
    client = FixtureClient()
    with pytest.raises(PermissionError):
        acquire(client)
    assert client.calls == []
    cfg = configuration(wires()["AssetPairs"])
    assert not cfg.enabled and dict(cfg.source.metadata)["raw_model_export"] == "denied"


def test_exact_wire_parsing_and_timestamp_semantics():
    cfg = configuration(wires()["AssetPairs"])
    depth = normalize_spot_response(cfg, DEPTH, parse_depth(wires()["Depth"]), T)[0]
    assert depth["exchange_event_at"] is None and depth["spread_quote"] == "0.1"
    assert parse_price(wires()["Ticker"]) == "100.1"
    rows = normalize_spot_response(cfg, TRADES, parse_trades(wires()["Trades"]), T)
    assert rows[0]["exchange_event_at"].endswith(".123456+00:00")
    assert rows[0]["reported_side"] == "buy" and rows[1]["reported_side"] == "sell"
    assert all(r["aggressor_side"] == "unknown" and r["granularity"] == "unknown" for r in rows)


@pytest.mark.parametrize("change", ["pair", "precision", "error", "missing_id", "side", "ordering", "cap", "conflict"])
def test_malformed_batch_rejected_before_writes(change, tmp_path):
    data = wires()
    if change == "pair":
        data["AssetPairs"]["result"]["XXBTZUSD"]["quote"] = "USDT"
    elif change == "precision":
        data["AssetPairs"]["result"]["XXBTZUSD"]["lot_decimals"] = True
    elif change == "error":
        data["Trades"]["error"] = ["EGeneral:Invalid arguments"]
    elif change == "missing_id":
        data["Trades"]["result"]["XXBTZUSD"][0].pop()
    elif change == "side":
        data["Trades"]["result"]["XXBTZUSD"][0][3] = "unknown"
    elif change == "ordering":
        data["Depth"]["result"]["XXBTZUSD"]["bids"].append(["101", "1", 1793849001])
    elif change == "cap":
        data["Trades"]["result"]["XXBTZUSD"] *= 11
    else:
        duplicate = copy.deepcopy(data["Trades"]["result"]["XXBTZUSD"][0])
        duplicate[0] = "99"
        data["Trades"]["result"]["XXBTZUSD"].append(duplicate)
    with pytest.raises((ValueError, KeyError)):
        acquire(FixtureClient(data), enabled=True)
    assert not list(tmp_path.iterdir())


def test_sqlite_restart_dedup_pit_and_private_export(tmp_path):
    store = SQLiteInformationStore(tmp_path / "isolated.db")
    sample = acquire(FixtureClient(), enabled=True)
    ids = persist(store, sample, run_id="r1")
    end = T + timedelta(seconds=4)
    count = len(store.view_at(end).observations)
    assert count == 10  # four wire, price, depth, two trades, two receipts
    assert persist(SQLiteInformationStore(store.path), sample, run_id="r1") == ids
    assert len(store.view_at(end).observations) == count
    assert not render_spot_evidence(store.view_at(T + timedelta(seconds=2)))
    rendered = "\n".join(render_spot_evidence(store.view_at(end)))
    assert "PRIVATE_RAW_SENTINEL" not in rendered and "trade=1" not in rendered
    assert "recent_sample_executions=2" in rendered and "sampled_depth_BTC=1/2" in rendered
    next_sample = acquire(FixtureClient(offset=10), enabled=True)
    again = persist(store, next_sample, run_id="r2")
    assert again[1:] == ids[1:]  # immutable venue trade IDs dedup across new runs
    view = store.view_at(T + timedelta(seconds=20))
    assert len([r for r in view.observations if r.metric == TRADES]) == 2
    assert len([r for r in view.observations if r.metric == PRIVATE]) == 8
    assert all(r.raw_reference.startswith("kraken-wire:") for r in view.observations if r.metric in {DEPTH, TRADES})
    before = view.evidence_history
    with pytest.raises(ValueError, match="rollback"):
        persist(store, sample, run_id="backdated")
    assert store.view_at(T + timedelta(seconds=20)).evidence_history == before


class Response:
    status_code = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def iter_content(self, size):
        yield json.dumps(envelope({})).encode()


def test_transport_limits_no_redirect_retry_and_safe_errors():
    class Session:
        def get(self, url, **kwargs):
            assert url.startswith("https://api.kraken.com/0/public/")
            assert kwargs["allow_redirects"] is False and kwargs["timeout"] == (5, 10)
            return Response()
    sleeps = []
    client = PublicClient(Session(), clock=lambda: T, monotonic=lambda: 0, sleep=sleeps.append)
    for endpoint in ("AssetPairs", "Ticker", "Depth", "Trades"):
        client.get(endpoint)
    assert sleeps == [1.1] * 3
    with pytest.raises(ValueError):
        client.get("Trades")
    class Unavailable:
        def get(self, *args, **kwargs):
            raise requests.Timeout("private transport details")
    with pytest.raises(ConnectionError, match="no retry"):
        PublicClient(Unavailable()).get("Depth")


@pytest.mark.parametrize("status", [302, 403, 429, 500])
def test_http_failures_stop_without_following(status):
    class Session:
        def get(self, *args, **kwargs):
            response = Response()
            response.status_code = status
            return response
    with pytest.raises(ConnectionError, match=str(status)):
        PublicClient(Session()).get("Depth")


def test_transport_byte_bound():
    class Oversized(Response):
        def iter_content(self, size):
            yield b"x" * 262145
    class Session:
        def get(self, *args, **kwargs):
            return Oversized()
    with pytest.raises(ConnectionError, match="byte/time"):
        PublicClient(Session()).get("Depth")


def test_consistent_backup_and_old_rows_preserved(tmp_path):
    path, backup = tmp_path / "canonical.db", tmp_path / "backup.db"
    SQLiteInformationStore(path)
    report = collect(path, backup, run_id="manual", client=FixtureClient(), enabled=True)
    assert report["before"]["counts"]["observations"] == 0
    assert report["after"]["counts"]["observations"] == 10
    assert len(SQLiteInformationStore(backup, read_only=True).view_at(T).observations) == 0
    with pytest.raises(ValueError):
        collect(path, backup, run_id="manual", client=FixtureClient(), enabled=True)


@pytest.mark.usefixtures("offline")
def test_actual_graph_sees_only_derived_evidence(tmp_path, monkeypatch):
    import socket
    def deny(*args, **kwargs):
        raise AssertionError("network denied")
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(requests.Session, "request", deny)
    store = SQLiteInformationStore(tmp_path / "graph.db")
    ids = persist(store, acquire(FixtureClient(), enabled=True), run_id="graph")
    for cutoff in (T, T + timedelta(seconds=4)):
        model = PromptCapturingModel()
        graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
        state, _ = graph.propagate("BTCUSDT", T.date().isoformat(), asset_type="crypto", decision_time=cutoff)
        market = "\n".join(p for p in model.prompts if "get_verified_market_snapshot" in p)
        assert "PRIVATE_RAW_SENTINEL" not in "\n".join(model.prompts)
        assert len(state["analysis_information"]) <= 28000 and max(map(len, model.prompts)) <= 28000
        assert (ids[0] in market) == (cutoff > T)
        if cutoff > T:
            assert "recent_sample_executions=2" in market and "Macro series:" in market
            assert "Funding rate:" in market and SOURCE_ID in market
