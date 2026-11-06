"""Manual, private BTC inverse perpetual sample; no scheduler or trading.

Two official public REST calls. Raw wire data is local-only. The scoped personal
API assessment is documented in C2D_DERIVATIVES_20261106.md, not an AI licence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext
from pathlib import Path

import requests

from tradingagents.information.binance_spot import (
    CoverageRecord,
    CoverageStatus,
    MarketDataBatch,
    MarketDataGap,
)
from tradingagents.information.observations import Observation
from tradingagents.information.polling import job_lock
from tradingagents.information.reconciliation import read_rows, schema, validate
from tradingagents.information.runtime_store import runtime_store_path
from tradingagents.information.sources import Source
from tradingagents.information.store import ObservationStoreConflict, SQLiteInformationStore

SOURCE_ID = "derivatives.deribit.btc_perpetual.public"
SUBJECT = "deribit:BTC-PERPETUAL"
SAMPLE = "derivatives.qualified.sample"
PRIVATE = "derivatives.private.wire"
INGEST = "derivatives.ingest.receipt"
METADATA = "derivatives.instrument.metadata"
BASE = "https://www.deribit.com/api/v2/public/"
URLS = {name: BASE + name + "?instrument_name=BTC-PERPETUAL"
        for name in ("get_instrument", "ticker")}
SOURCE = Source(
    SOURCE_ID, "public_derivatives_api", "Deribit", BASE,
    "manual bounded official REST; two GETs; no authentication", version="c2d-1",
    asset_scope=(SUBJECT,), metric_scope=(SAMPLE, PRIVATE, INGEST, METADATA),
    polling_frequency="manual only", rate_limit="two calls spaced >=1.1s; no retries; stop on denial",
    publication_semantics="local receipt drives availability; exchange timestamp untrusted",
    limitations=("single venue inverse perpetual", "OI measurement time/delay unknown: postponed Nov5 change",
                 "funding fields are reported rates, not guaranteed future costs", "off-session coverage unknown"),
    legal_constraints=("personal private research only; no redistribution or training",
                       "raw responses local only; compact metrics for personal inference"),
    metadata=(("collection", "permitted"), ("private_retention", "permitted"),
              ("personal_inference", "permitted"), ("raw_model_export", "denied"),
              ("redistribution", "denied"), ("free", "true"),
              ("rights_assessed_at", "2026-11-06"),
              ("rights_basis", "scoped personal public API assessment; no express AI licence"),
              ("rights_reference", "https://support.deribit.com/hc/en-us/articles/25944532191645-Deribit-Exchange-Membership-Terms-Deribit-FZE")),
)


def permission(source=SOURCE):
    meta = dict(source.metadata)
    if source.source_id != SOURCE_ID or any(meta.get(k) != "permitted" for k in (
        "collection", "private_retention", "personal_inference"
    )) or meta.get("raw_model_export") != "denied" or meta.get("free") != "true":
        raise PermissionError("personal-use source assessment missing or denied")


def decimal(value, *, signed=False, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("exact decimal required")
    if isinstance(value, Decimal) and (not value.is_finite() or value.adjusted() > 23
                                       or value.as_tuple().exponent < -18):
        raise ValueError("decimal magnitude/precision bound")
    text = format(value, "f") if isinstance(value, Decimal) else str(value)
    if len(text) > 64 or not re.fullmatch(r"-?\d{1,24}(?:\.\d{1,18})?", text):
        raise ValueError("invalid decimal syntax/precision")
    number = Decimal(text)
    if not number.is_finite() or (not signed and number < 0) or (positive and number <= 0):
        raise ValueError("invalid decimal sign/value")
    return format(number, "f")


def utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("aware local receipt time required")
    return value.astimezone(UTC)


def timestamp(value):
    if value is None:
        return None
    if type(value) is not int or not 0 <= value <= 253402300799999:
        raise ValueError("invalid exchange millisecond timestamp")
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=value)


def result(wire):
    if (not isinstance(wire, dict) or wire.get("jsonrpc") != "2.0" or "error" in wire
            or wire.get("testnet") is True or not isinstance(wire.get("result"), dict)):
        raise ValueError("Deribit API error/testnet/malformed result")
    return wire["result"]


def instrument(wire):
    p = result(wire)
    required = {"instrument_name": "BTC-PERPETUAL", "kind": "future", "base_currency": "BTC",
                "quote_currency": "USD", "settlement_currency": "BTC",
                "instrument_type": "reversed", "settlement_period": "perpetual", "price_index": "btc_usd"}
    if any(p.get(k) != v for k, v in required.items()) or p.get("is_active") is not True:
        raise ValueError("unexpected/inactive inverse BTC perpetual")
    size = decimal(p.get("contract_size"), positive=True)
    if Decimal(size) != 10:
        raise ValueError("unexpected BTC contract multiplier")
    return {**required, "venue": "deribit", "contract_size": size, "contract_size_unit": "USD/contract",
            "inverse": True, "expiry": None, "expiry_semantics": "perpetual; sentinel expiry not maturity",
            "tick_size": decimal(p.get("tick_size"), positive=True),
            "min_trade_amount": decimal(p.get("min_trade_amount"), positive=True)}


def normalize(metadata, wire, received_at):
    received_at = utc(received_at)
    spec, p = instrument(metadata), result(wire)
    if p.get("instrument_name") != "BTC-PERPETUAL" or p.get("state") != "open":
        raise ValueError("unexpected/unavailable ticker instrument")
    event = timestamp(p.get("timestamp"))
    mark = decimal(p.get("mark_price"), positive=True)
    index = decimal(p.get("index_price"), positive=True)
    oi = decimal(p.get("open_interest"))
    current = decimal(p.get("current_funding"), signed=True)
    eight = decimal(p.get("funding_8h"), signed=True)
    if max(abs(Decimal(current)), abs(Decimal(eight))) > 1:
        raise ValueError("implausible funding fraction")
    with localcontext() as ctx:
        ctx.prec = 50
        premium = format((Decimal(mark) / Decimal(index) - 1) * 100, "f")
        contracts = format(Decimal(oi) / Decimal(spec["contract_size"]), "f")
    return {"instrument": spec, "exchange_event_at": event.isoformat() if event else None,
            "received_at": received_at.isoformat(), "available_at": received_at.isoformat(),
            "exchange_future_clock": event is not None and event > received_at,
            "exchange_age_seconds": str((received_at-event).total_seconds()) if event else None,
            "current_funding": current, "funding_8h": eight, "funding_unit": "fraction",
            "funding_interval_hours": 8, "funding_semantics": "continuous accrual; current 8h-expressed rate and reported funding_8h statistic; not a settled payment or predicted guaranteed cost",
            "open_interest": oi, "oi_unit": "USD", "oi_contracts_equivalent": contracts,
            "oi_exchange_event_at": None, "oi_delay_seconds": None,
            "oi_delay_status": "UNKNOWN; Nov5 eight-hour-delay release postponed; do not assert realtime",
            "mark_price": mark, "index_price": index, "price_unit": "USD/BTC",
            "mark_index_premium_pct": premium, "basis_kind": "same ticker mark/index premium proxy",
            "traded_spot_futures_basis": None, "annualized_basis": None,
            "stale_seconds": 120, "coverage": "sample only; off intervals UNKNOWN"}


class PublicClient:
    """Fixed production allowlist, TLS, byte/time limits, no retry or redirects."""

    def __init__(self, session, *, clock=None, monotonic=time.monotonic, sleep=time.sleep):
        self.session, self.clock = session, clock or (lambda: datetime.now(UTC))
        self.monotonic, self.sleep, self.last = monotonic, sleep, None
        self.calls = 0

    def get(self, endpoint):
        if endpoint not in URLS or self.calls >= 2:
            raise ValueError("outside two-request one-shot")
        if self.last is not None:
            self.sleep(max(0, 1.1 - (self.monotonic() - self.last)))
        self.last = self.monotonic()
        self.calls += 1
        start = self.monotonic()
        with self.session.get(URLS[endpoint], timeout=(5, 10), stream=True, allow_redirects=False,
                              headers={"User-Agent": "PrivateBTCResearch/1.0"}) as response:
            if response.status_code != 200:
                raise ConnectionError(f"Deribit HTTP {response.status_code}; no retry")
            parts, count = [], 0
            for chunk in response.iter_content(8192):
                count += len(chunk)
                if count > 262144 or self.monotonic() - start > 20:
                    raise ConnectionError("response byte/time bound")
                parts.append(chunk)
            raw = b"".join(parts).decode("utf-8")
        at = utc(self.clock())
        wire = json.loads(raw, parse_float=Decimal)
        result(wire)
        return {"endpoint": endpoint, "url": URLS[endpoint], "raw": raw,
                "sha256": hashlib.sha256(raw.encode()).hexdigest(), "received_at": at, "wire": wire,
                "status": 200, "elapsed_seconds": self.monotonic()-start}


def acquire(client, *, enabled=False):
    if not enabled:
        raise PermissionError("explicit manual acquisition opt-in required")
    permission()
    metadata = client.get("get_instrument")
    instrument(metadata["wire"])
    ticker = client.get("ticker")
    if utc(ticker["received_at"]) < utc(metadata["received_at"]):
        raise ValueError("local receive clock rollback")
    normalize(metadata["wire"], ticker["wire"], ticker["received_at"])
    return metadata, ticker


def persist(store, acquisition, *, run_id):
    permission()
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9:_-]{1,120}", run_id):
        raise ValueError("invalid run ID")
    metadata, ticker = acquisition
    if [r["endpoint"] for r in acquisition] != list(URLS):
        raise ValueError("wrong receipt order")
    for r in acquisition:
        if (r["url"] != URLS[r["endpoint"]] or hashlib.sha256(r["raw"].encode()).hexdigest() != r["sha256"]
                or json.loads(r["raw"], parse_float=Decimal) != r["wire"]):
            raise ValueError("receipt hash/URL/wire mismatch")
    at = utc(ticker["received_at"])
    if at < utc(metadata["received_at"]):
        raise ValueError("local receive clock rollback")
    payload = normalize(metadata["wire"], ticker["wire"], at)
    history = [r for r in store.view_at(datetime.max.replace(tzinfo=UTC)).evidence_history
               if r.source_id == SOURCE_ID]
    prefix = "c2d:" + hashlib.sha256(run_id.encode()).hexdigest()
    rows = []
    for r in acquisition:
        t = utc(r["received_at"])
        rows.append(Observation(prefix+":"+r["endpoint"], SOURCE_ID, prefix+":"+r["endpoint"], PRIVATE,
                    {k: v for k, v in r.items() if k not in {"wire", "received_at"}} |
                    {"received_at": t.isoformat(), "export": "local_only"}, t, t, t,
                    schema_version="deribit-private-v1"))
    mt = utc(metadata["received_at"])
    rows.append(Observation(prefix+":instrument", SOURCE_ID, prefix+":instrument", METADATA,
                instrument(metadata["wire"]), mt, mt, mt, raw_reference=rows[0].observation_id,
                schema_version="deribit-instrument-v1"))
    # Local receipt anchors identity. Nullable untrusted exchange times are only
    # payload metadata, never backdating availability or fabricating OI time.
    sample = Observation(prefix+":sample", SOURCE_ID, SUBJECT, SAMPLE, payload, at, at, at,
                         raw_reference=rows[1].observation_id, schema_version="deribit-sample-v1",
                         unit="qualified mixed metrics")
    rows.append(sample)
    rows.append(Observation(prefix+":ingest", SOURCE_ID, prefix+":ingest", INGEST,
                {"run_id": run_id, "sample_id": sample.observation_id,
                 "wire_ids": [r.observation_id for r in rows[:2]], "status": "sampled",
                 "complete": False, "export": "local_only"}, at, at, at,
                schema_version="deribit-ingest-v1"))
    existing = {r.observation_id: r for r in history}
    repeated = [r for r in rows if r.observation_id in existing]
    if repeated:
        if len(repeated) != len(rows) or any(existing[r.observation_id] != r for r in rows):
            raise ObservationStoreConflict("run identity collision; no writes")
        return sample.observation_id
    if any(r.metric == SAMPLE and r.retrieved_at == at for r in history):
        raise ObservationStoreConflict("ambiguous same-time sample; no writes")
    if any(r.retrieved_at > mt for r in history):
        raise ValueError("local receipt clock rollback; no writes")
    prior = [r for r in history if r.metric == SAMPLE]
    gaps = ()
    if prior and at-max(r.retrieved_at for r in prior) > timedelta(seconds=240):
        gaps = (MarketDataGap(SUBJECT, SAMPLE, max(r.retrieved_at for r in prior)+timedelta(microseconds=1), at,
                              "unobserved manual sampling interval", "unknown"),)
    coverage = tuple(CoverageRecord(prefix+":"+kind, SOURCE_ID, SUBJECT, kind, at,
                     CoverageStatus.UNKNOWN, detail, (sample.observation_id,)) for kind, detail in (
        ("funding", "Reported current/8h rates only; continuous accrual; payment history unknown"),
        ("open_interest", "USD amount; measurement time/delay unknown; no directional long/short signal"),
        ("basis", "same-ticker mark/index premium proxy; traded spot/futures and annualized basis unavailable")))
    # All rows, definitions, coverage and gaps are in the store's one transaction.
    store.append(MarketDataBatch(tuple(rows), gaps, at, coverage, (SOURCE,)))
    return sample.observation_id


def selected(view):
    definitions = [(s, t) for s, t in view.source_definitions if s.source_id == SOURCE_ID]
    if not definitions:
        return ()
    latest = max(t for _, t in definitions)
    try:
        for source, t in definitions:
            if t == latest:
                permission(source)
    except PermissionError:
        return ()
    rows = [r for r in view.observations if r.source_id == SOURCE_ID and r.metric == SAMPLE
            and r.schema_version == "deribit-sample-v1" and r.available_at <= view.decision_time]
    return (max(rows, key=lambda r: (r.retrieved_at, r.observation_id)),) if rows else ()


def render(view):
    lines = []
    for row in selected(view):
        p = row.payload
        stale = (view.decision_time-row.retrieved_at).total_seconds() > 120
        gaps = sum(g.subject == SUBJECT for g in view.gaps)
        lines.append(f"- {row.observation_id}: ATTRIBUTED Deribit BTC-PERPETUAL inverse, BTC-settled, 10 USD/contract; "
                     f"current_funding={p['current_funding']}; funding_8h={p['funding_8h']} fraction; "
                     "8h-expressed continuous accrual, reported statistic; realized payment/prediction UNKNOWN; "
                     f"OI={p['open_interest']} USD ({p['oi_contracts_equivalent']} contract equivalents); "
                     "OI time/delay UNKNOWN (postponed Nov5 change), never directional long/short; "
                     f"mark_index_premium={p['mark_index_premium_pct']}%; same-ticker proxy, not traded spot/futures basis; "
                     f"received/available={row.available_at.isoformat()}; stale={stale}; "
                     f"exchange_time={p['exchange_event_at']}; exchange_age_s={p['exchange_age_seconds']}; future_clock={p['exchange_future_clock']}; "
                     f"gaps={gaps}; off intervals UNKNOWN; no guaranteed funding cost; raw LOCAL ONLY")
    return lines


def collect(path, backup, *, client, run_id, enabled=False):
    if not enabled:
        raise PermissionError("explicit canonical write opt-in required")
    permission()
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9:_-]{1,120}", run_id):
        raise ValueError("invalid run ID before transport")
    path, backup = runtime_store_path(path), Path(backup).resolve()
    if backup.exists() or backup == path or not backup.parent.is_dir():
        raise ValueError("new distinct backup path required")
    with job_lock(SQLiteInformationStore(path, read_only=True)):
        with sqlite3.connect(path.as_uri()+"?mode=ro", uri=True) as db:
            before, original, structure = validate(db), read_rows(db), schema(db)
            prefix = "c2d:"+hashlib.sha256(run_id.encode()).hexdigest()
            if db.execute("SELECT 1 FROM observations WHERE observation_id=?", (prefix+":sample",)).fetchone():
                raise ValueError("already acquired; replay private receipts offline")
            with backup.open("xb"):
                pass
            with sqlite3.connect(backup) as target:
                db.backup(target)
                assert validate(target) == before and read_rows(target) == original and schema(target) == structure
        before_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        acquisition = acquire(client, enabled=True)
        evidence = persist(SQLiteInformationStore(path), acquisition, run_id=run_id)
        with sqlite3.connect(path.as_uri()+"?mode=ro", uri=True) as db:
            after, current = validate(db), read_rows(db)
            if schema(db) != structure or any(not set(v) <= set(current[t]) for t, v in original.items()):
                raise ValueError("original history/schema changed; safe stop, preserve backup")
        return {"before": before, "after": after, "before_sha256": before_sha,
                "after_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "evidence_id": evidence,
                "backup": str(backup), "backup_sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
                "receipts": [{k: v.isoformat() if isinstance(v, datetime) else v for k, v in r.items()
                              if k not in {"raw", "wire"}} for r in acquisition]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--allow-canonical-write", action="store_true")
    args = parser.parse_args(argv)
    with requests.Session() as session:
        print(json.dumps(collect(args.store, args.backup, run_id=args.run_id, client=PublicClient(session),
                                 enabled=args.allow_canonical_write), indent=2))


if __name__ == "__main__":
    main()
