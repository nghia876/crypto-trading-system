"""Opt-in, four-request Kraken BTC/USD spot sample. No polling or trading.

Raw receipts stay in the canonical private store. Only derived metrics are
rendered by the consumer. Public API private-research assessment: see the dated
C2B handoff; this is not a redistribution or model-training licence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import requests

from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.observations import Observation
from tradingagents.information.polling import job_lock
from tradingagents.information.reconciliation import read_rows, validate
from tradingagents.information.runtime_store import runtime_store_path
from tradingagents.information.sources import Source
from tradingagents.information.spot_microstructure import (
    DEPTH,
    RECEIPT,
    RIGHTS,
    TRADES,
    SpotEvidenceConfig,
    ingest_spot_evidence,
    normalize_spot_response,
)
from tradingagents.information.store import ObservationStoreConflict, SQLiteInformationStore

SOURCE_ID = "spot.kraken.btcusd.public"
PRICE = "spot.price.sample"
PRIVATE = "spot.private.wire.receipt"
BASE = "https://api.kraken.com/0/public/"
MAX_BYTES = 262144
URLS = {
    "AssetPairs": BASE + "AssetPairs?pair=XBTUSD",
    "Ticker": BASE + "Ticker?pair=XBTUSD",
    "Depth": BASE + "Depth?pair=XBTUSD&count=10",
    "Trades": BASE + "Trades?pair=XBTUSD&count=20",
}


def configuration(metadata, *, enabled=False):
    pair = result(metadata)["XXBTZUSD"]
    if (pair["base"], pair["quote"], pair["altname"], pair["wsname"], pair["status"]) != (
        "XXBT", "ZUSD", "XBTUSD", "XBT/USD", "online"
    ):
        raise ValueError("unexpected or unavailable BTC/USD spot instrument")
    for key in ("pair_decimals", "lot_decimals"):
        if type(pair[key]) is not int or not 0 <= pair[key] <= 18:
            raise ValueError("invalid pair precision")
    source = Source(
        SOURCE_ID, "public_spot_api", "Kraken", BASE,
        "manual bounded official REST; four GETs; no authentication", version="c2b-1",
        asset_scope=("BTC/USD",), metric_scope=(DEPTH, TRADES, RECEIPT, PRICE, PRIVATE),
        rate_limit="at most one request per second; no retries", polling_frequency="manual only",
        publication_semantics="untrusted exchange time; available only after local receipt",
        limitations=("sampled L2, not continuous history", "recent trades are an incomplete window",
                     "REST quantities may be rounded by venue", "reported side; aggressor unknown"),
        legal_constraints=("personal private research only", "raw API data stays local",
                           "no redistribution or model training; compact derived inference only"),
        metadata=tuple((f"c2_{right}", "permitted") for right in RIGHTS) + (
            ("c2_free", "true"), ("c2_redistribution", "denied"),
            ("c2_export", "derived_only"), ("raw_model_export", "denied"),
            ("rights_assessed_at", "2026-11-06"),
            ("rights_basis", "scoped public API private research assessment; not express AI licence"),
            ("rights_reference", "https://blog.kraken.com/product/api/unlocked-3-the-market-data-feeds-systematic-traders-use"),
        ),
    )
    # Pair precision is order-entry precision. REST serializes prices padded to
    # five places and volumes to eight; accept exact wire strings up to 18 places
    # without claiming the wire precision equals the order tick size.
    return SpotEvidenceConfig(source, "kraken", enabled=enabled, level_cap=10, trade_cap=20)


def result(wire):
    if not isinstance(wire, dict) or wire.get("error") != [] or not isinstance(wire.get("result"), dict):
        raise ValueError("Kraken error or malformed response")
    return wire["result"]


def exchange_time(value):
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise ValueError("exact numeric exchange timestamp required")
    value = Decimal(value)
    if not value.is_finite() or not 0 <= value <= Decimal("253402300799"):
        raise ValueError("exchange timestamp outside bounds")
    # Explicit microsecond truncation, never binary-float rounding/backdating PIT.
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=int(value * 1000000))


def parse_depth(wire):
    payload = result(wire)
    if set(payload) != {"XXBTZUSD"}:
        raise ValueError("unexpected depth pair")
    parsed = {}
    for side in ("bids", "asks"):
        rows = payload["XXBTZUSD"][side]
        if not isinstance(rows, list) or len(rows) > 10:
            raise ValueError("depth exceeds requested bound")
        parsed[side] = []
        for row in rows:
            if not isinstance(row, list) or len(row) != 3:
                raise ValueError("invalid level")
            exchange_time(row[2])  # per-level last update, NOT snapshot time
            parsed[side].append(row[:2])
    return parsed  # no snapshot timestamp/sequence supplied by this REST endpoint


def parse_trades(wire):
    payload = result(wire)
    if set(payload) != {"XXBTZUSD", "last"} or not isinstance(payload["last"], str):
        raise ValueError("unexpected trades pair/cursor")
    rows = payload["XXBTZUSD"]
    if not isinstance(rows, list) or len(rows) > 20:
        raise ValueError("trades exceed requested bound")
    trades, seen = [], {}
    for row in rows:
        if (not isinstance(row, list) or len(row) != 7 or row[3] not in {"b", "s"}
                or row[4] not in {"m", "l"} or not isinstance(row[5], str)
                or type(row[6]) is not int or row[6] < 0):
            raise ValueError("invalid trade fields/ID")
        # Identical overlap is deduplicated; contradictory IDs reject the batch.
        if row[6] in seen:
            if row != seen[row[6]]:
                raise ValueError("conflicting duplicate trade ID")
            continue
        seen[row[6]] = row
        trades.append({"trade_id": str(row[6]), "price": row[0], "quantity": row[1],
                           "exchange_event_at": exchange_time(row[2]),
                           "aggressor_side": {"b": "buy", "s": "sell"}[row[3]], "granularity": "unknown"})
    trades.sort(key=lambda t: (t["exchange_event_at"], int(t["trade_id"])))
    return {"trades": trades, "cursor": payload["last"]}


def parse_price(wire):
    from tradingagents.information.spot_microstructure import _decimal
    payload = result(wire)
    if set(payload) != {"XXBTZUSD"}:
        raise ValueError("unexpected ticker pair")
    return _decimal(payload["XXBTZUSD"]["c"][0])


class PublicClient:
    """Fixed URL allowlist, verified TLS, bounded bytes/time; no redirects/retries."""

    def __init__(self, session, *, clock=None, monotonic=time.monotonic, sleep=time.sleep):
        self.session = session
        self.clock = clock or (lambda: datetime.now(UTC))
        self.monotonic, self.sleep, self.last = monotonic, sleep, None
        self.calls = 0

    def get(self, endpoint):
        if endpoint not in URLS or self.calls >= 4:
            raise ValueError("request outside bounded acquisition")
        if self.last is not None:
            self.sleep(max(0, 1.1 - (self.monotonic() - self.last)))
        self.last = self.monotonic()
        self.calls += 1
        start = self.monotonic()
        try:
            with self.session.get(URLS[endpoint], timeout=(5, 10), stream=True,
                                  allow_redirects=False, headers={"User-Agent": "PrivateBTCResearch/1.0"}) as response:
                if response.status_code != 200:
                    raise ConnectionError(f"public API HTTP {response.status_code}; no retry")
                chunks, size = [], 0
                for chunk in response.iter_content(8192):
                    size += len(chunk)
                    if size > MAX_BYTES or self.monotonic() - start > 20:
                        raise ConnectionError("public response byte/time bound exceeded")
                    chunks.append(chunk)
                raw = b"".join(chunks)
        except requests.RequestException as exc:
            raise ConnectionError("public API transport unavailable; no retry") from exc
        received = self.clock()
        wire = json.loads(raw, parse_float=Decimal)
        result(wire)
        return {"endpoint": endpoint, "url": URLS[endpoint], "raw": raw.decode("utf-8"),
                "sha256": hashlib.sha256(raw).hexdigest(), "received_at": received, "wire": wire}


def acquire(client, *, enabled=False):
    if not enabled:
        raise PermissionError("explicit manual acquisition opt-in required")
    receipts = [client.get("AssetPairs")]
    config = configuration(receipts[0]["wire"], enabled=True)
    config.require_permission(("kraken",))
    for endpoint in ("Ticker", "Depth", "Trades"):
        receipts.append(client.get(endpoint))
    price = parse_price(receipts[1]["wire"])
    depth = parse_depth(receipts[2]["wire"])
    trades = parse_trades(receipts[3]["wire"])
    # Validate ALL data before any write. Ordering, decimal syntax and caps are
    # validated again by the source-independent ingestion contract.
    normalize_spot_response(config, DEPTH, depth, receipts[2]["received_at"])
    normalize_spot_response(config, TRADES, trades, receipts[3]["received_at"])
    times = [r["received_at"] for r in receipts]
    if times != sorted(times):
        raise ValueError("local receive clock rollback")
    return config, receipts, price, depth, trades


def persist(store, acquisition, *, run_id):
    """Replay of the same run/receipts is idempotent; append-only partial failures."""
    from tradingagents.information.spot_microstructure import _label
    _label(run_id, "run_id")
    config, receipts, price, depth, trades = acquisition
    config.require_permission(("kraken",))
    normalize_spot_response(config, DEPTH, depth, receipts[2]["received_at"])
    normalize_spot_response(config, TRADES, trades, receipts[3]["received_at"])
    raw_rows = []
    for receipt in receipts:
        at = receipt["received_at"]
        identity = hashlib.sha256(f"{run_id}:{receipt['endpoint']}".encode()).hexdigest()
        raw_rows.append(Observation(
            "kraken-wire:" + identity, SOURCE_ID, "kraken-wire:" + identity, PRIVATE,
            {k: v for k, v in receipt.items() if k != "wire"} | {
                "received_at": at.isoformat(), "export": "local_only",
                "retention": "private evidence history; no automatic deletion",
            }, at, at, at, schema_version="kraken-private-wire-v1",
        ))
    at = receipts[1]["received_at"]
    raw_rows.append(Observation(
        "kraken-price:" + hashlib.sha256(run_id.encode()).hexdigest(), SOURCE_ID,
        "kraken-price:" + run_id, PRICE, {"price": price, "symbol": "BTC/USD", "exchange_event_at": None},
        at, at, at, unit="USD/BTC", schema_version="kraken-price-v1",
    ))
    history = store.view_at(datetime.max.replace(tzinfo=UTC)).evidence_history
    existing = {r.observation_id: r for r in history}
    repeated = [r for r in raw_rows if r.observation_id in existing]
    if repeated:
        if len(repeated) != len(raw_rows) or any(existing[r.observation_id] != r for r in repeated):
            raise ObservationStoreConflict("manual run identity reused with different receipts")
    elif any(r.source_id == SOURCE_ID and r.retrieved_at > receipts[0]["received_at"] for r in history):
        raise ValueError("local receive clock rollback; no writes")
    store.append(MarketDataBatch(tuple(raw_rows), (), receipts[-1]["received_at"], source_definitions=(config.source,)))
    ids = []
    for kind, data, receipt in ((DEPTH, depth, receipts[2]), (TRADES, trades, receipts[3])):
        ids.extend(ingest_spot_evidence(store, config, kind=kind, data=data,
                   received_at=receipt["received_at"], receipt_id=run_id + ":" + receipt["endpoint"],
                   configured_venues=("kraken",), raw_reference="kraken-wire:" + hashlib.sha256(
                       f"{run_id}:{receipt['endpoint']}".encode()).hexdigest()))
    return ids


def render_derived(view, row):
    """Allowlisted scalar aggregates only. Never serialize wire payload or levels."""
    p = row.payload
    stale = (view.decision_time - row.retrieved_at).total_seconds() > p["stale_seconds"]
    if row.metric == DEPTH:
        bid, ask = Decimal(p["bid_depth_base"]), Decimal(p["ask_depth_base"])
        imbalance = str((bid - ask) / (bid + ask)) if bid + ask else "unknown"
        prices = [r for r in view.observations if r.source_id == SOURCE_ID and r.metric == PRICE]
        price = max(prices, key=lambda r: r.retrieved_at).payload["price"] if prices else "unknown"
        detail = (f"last_sampled_price_USD={price}; spread_USD={p['spread_quote']}; "
                  f"sampled_depth_BTC={bid}/{ask}; depth_imbalance={imbalance}; "
                  f"levels={len(p['bids'])}/{len(p['asks'])}; integrity={p['integrity']}")
    else:
        receipts = [r for r in view.observations if r.source_id == SOURCE_ID and r.metric == RECEIPT
                    and r.payload.get("kind") == TRADES]
        latest = max(receipts, key=lambda r: (r.retrieved_at, r.observation_id))
        ids = set(latest.payload["evidence_ids"])
        trades = [r for r in view.observations if r.observation_id in ids and r.metric == TRADES]
        volume = sum((Decimal(r.payload["quantity"]) for r in trades), Decimal(0))
        cost = sum((Decimal(r.payload["price"]) * Decimal(r.payload["quantity"]) for r in trades), Decimal(0))
        times = [datetime.fromisoformat(r.payload["exchange_event_at"]) for r in trades
                 if r.payload["exchange_event_at"]]
        exchange_stale = bool(times and (view.decision_time - max(times)).total_seconds() > p["stale_seconds"])
        skew = sum(t > latest.retrieved_at for t in times)
        detail = (f"recent_sample_executions={len(trades)}; volume_BTC={volume}; "
                  f"sample_VWAP_USD={cost / volume if volume else 'unknown'}; aggressor=unknown; "
                  f"exchange_stale_untrusted={exchange_stale}; future_exchange_clocks={skew}; "
                  f"sample_receipt_at={latest.retrieved_at.isoformat()}; "
                  "granularity=unknown; incomplete recent response; no continuous tape")
    return (f"- {row.observation_id}: Kraken BTC/USD derived private research; {detail}; "
            f"received_at={row.retrieved_at.isoformat()}; available_at={row.available_at.isoformat()}; "
            f"stale={stale}; exchange clock untrusted; no predictive signal; raw data LOCAL ONLY")


def collect(path, backup, *, run_id, client, enabled=False):
    if not enabled:
        raise PermissionError("explicit --allow-canonical-write required")
    from tradingagents.information.spot_microstructure import _label
    _label(run_id, "run_id")
    if len(run_id) > 140:
        raise ValueError("run_id too long for qualified receipt")
    path, backup = runtime_store_path(path), Path(backup).resolve()
    if backup.exists() or backup == path or not backup.parent.is_dir():
        raise ValueError("new distinct private backup path with existing parent required")
    with job_lock(SQLiteInformationStore(path, read_only=True)):
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as source:
            before = validate(source)
            original = read_rows(source)
            identity = hashlib.sha256(f"{run_id}:AssetPairs".encode()).hexdigest()
            if source.execute("SELECT 1 FROM observations WHERE observation_id=?", ("kraken-wire:" + identity,)).fetchone():
                raise ValueError("run already acquired; choose a new manual run ID, replay existing receipts offline")
            with backup.open("xb"):
                pass
            with sqlite3.connect(backup) as target:
                source.backup(target)
                if validate(target) != before:
                    raise ValueError("backup validation differs")
        before_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        backup_sha = hashlib.sha256(backup.read_bytes()).hexdigest()
        acquisition = acquire(client, enabled=True)
        ids = persist(SQLiteInformationStore(path), acquisition, run_id=run_id)
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
            after = validate(db)
            current = read_rows(db)
            if any(not set(original[t]) <= set(current[t]) for t in original):
                raise ValueError("preexisting rows changed; preserve files and backup")
        return {"run_id": run_id, "before": before, "after": after, "before_sha256": before_sha,
                    "after_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "backup_sha256": backup_sha,
                    "backup": str(backup), "evidence_ids": ids,
                    "receipts": [{k: v.isoformat() if isinstance(v, datetime) else v
                               for k, v in r.items() if k not in {"raw", "wire"}}
                              for r in acquisition[1]]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--allow-canonical-write", action="store_true")
    args = parser.parse_args(argv)
    with requests.Session() as session:
        print(json.dumps(collect(args.store, args.backup, run_id=args.run_id,
                         client=PublicClient(session), enabled=args.allow_canonical_write), indent=2))


if __name__ == "__main__":
    main()
