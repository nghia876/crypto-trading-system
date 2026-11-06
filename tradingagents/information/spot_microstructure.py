"""C2-A source-independent sampled spot evidence. No enabled venue or HTTP client.

Inputs are normalized adapter mappings, not Kraken/Bitstamp wire responses. A
caller must supply an independently reviewed source and transport. No endpoint
invitation constitutes permission. All records use the existing append-only store.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext

from tradingagents.information.binance_spot import (
    CoverageRecord,
    CoverageStatus,
    MarketDataBatch,
    MarketDataGap,
)
from tradingagents.information.observations import Observation, ObservationQuality, _require_aware
from tradingagents.information.sources import Source
from tradingagents.information.store import InformationView, ObservationStoreConflict

SCHEMA = "spot-microstructure-v1"
DEPTH = "spot.depth.sample"
TRADES = "spot.executed_trade"
RECEIPT = "spot.microstructure.receipt"
RIGHTS = ("collection", "private_durable_retention", "internal_ai_inference", "third_party_processing")
# Deliberately empty: no operational registration, collector CLI or scheduler.
ENABLED_VENUES: tuple[str, ...] = ()


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _time(value, name):
    if not isinstance(value, datetime):
        raise ValueError(f"{name} must be an aware datetime")
    _require_aware(name, value)
    return value.astimezone(UTC)


def _label(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 160:
        raise ValueError(f"invalid {name}")
    return value


def _decimal(value, *, places=None, positive=True):
    # Refuse binary floats, exponents, NaN, Infinity, excessive precision/size.
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,24}(?:\.[0-9]{1,18})?", value):
        raise ValueError("bounded plain decimal string required")
    number = Decimal(value)
    if positive and number <= 0:
        raise ValueError("price/quantity must be positive")
    if places is not None and max(0, -number.as_tuple().exponent) > places:
        raise ValueError("decimal exceeds declared precision")
    return _plain(number)


def _plain(number):
    value = format(number, "f")
    return value.rstrip("0").rstrip(".") if "." in value else value


@dataclass(frozen=True)
class SpotEvidenceConfig:
    source: Source
    venue: str
    symbol: str = "BTC/USD"
    base: str = "BTC"
    quote: str = "USD"
    instrument: str = "spot"
    level_cap: int = 100
    trade_cap: int = 1000
    price_places: int | None = None
    quantity_places: int | None = None
    expected_interval_seconds: int = 60
    stale_seconds: int = 120
    aggressor_definition: str | None = None
    enabled: bool = False

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be explicit boolean")
        _label(self.venue, "venue")
        _label(self.symbol, "symbol")
        if self.instrument != "spot" or self.base != "BTC" or self.quote not in {"USD", "USDT"}:
            raise ValueError("BTC spot quoted in USD/USDT required; units are never interchangeable")
        if type(self.level_cap) is not int or type(self.trade_cap) is not int or not 1 <= self.level_cap <= 500 or not 1 <= self.trade_cap <= 1000:
            raise ValueError("invalid bounded level/trade cap")
        for value in (self.price_places, self.quantity_places):
            if value is not None and (type(value) is not int or not 0 <= value <= 18):
                raise ValueError("invalid precision")
        if type(self.expected_interval_seconds) is not int or type(self.stale_seconds) is not int or not 1 <= self.expected_interval_seconds <= 86400 or not 1 <= self.stale_seconds <= 86400:
            raise ValueError("invalid timing bound")
        if self.symbol not in self.source.asset_scope or not {DEPTH, TRADES, RECEIPT} <= set(self.source.metric_scope):
            raise ValueError("source must declare exact symbol and C2 metrics")

    @property
    def fingerprint(self):
        from dataclasses import asdict
        return _hash(asdict(self))

    def require_permission(self, configured_venues=()):
        metadata = dict(self.source.metadata)
        if not self.enabled or self.venue not in configured_venues:
            raise PermissionError("venue disabled/unconfigured")
        if any(metadata.get(f"c2_{right}") != "permitted" for right in RIGHTS):
            raise PermissionError("C2 use rights unknown or denied")
        if metadata.get("c2_free") != "true" or not metadata.get("rights_reference") or not metadata.get("rights_assessed_at"):
            raise PermissionError("free scoped permission evidence required")


def normalize_spot_response(config, kind, data, received_at):
    """Pure bounded normalized-input parser; no I/O or permission assertion."""
    received_at = _time(received_at, "received_at")
    if not isinstance(data, Mapping):
        raise ValueError("normalized response mapping required")
    event = data.get("exchange_event_at")
    event = _time(event, "exchange_event_at") if event is not None else None
    sequence = data.get("sequence")
    if sequence is not None and (type(sequence) is not int or sequence < 0):
        raise ValueError("sequence must be nonnegative integer or unknown")
    common = {
        "venue": config.venue, "symbol": config.symbol, "instrument": config.instrument,
        "base_unit": config.base, "quote_unit": config.quote,
        "price_places": config.price_places, "quantity_places": config.quantity_places,
        "precision_status": "declared" if config.price_places is not None and config.quantity_places is not None else "unknown",
        "exchange_event_at": event.isoformat() if event else None,
        "exchange_clock": "untrusted", "sequence": sequence,
        "stale_seconds": config.stale_seconds,
        "exchange_age_seconds": (received_at-event).total_seconds() if event else None,
        "clock_skew": bool(event and event > received_at),
    }
    if kind == DEPTH:
        levels = {}
        counts = {}
        for side in ("bids", "asks"):
            raw = data.get(side)
            if not isinstance(raw, (list, tuple)) or len(raw) > 500:
                raise ValueError("bounded levels required")
            parsed = []
            for row in raw:
                if not isinstance(row, (list, tuple)) or len(row) != 2:
                    raise ValueError("price/size level required")
                parsed.append((_decimal(row[0], places=config.price_places),
                               _decimal(row[1], places=config.quantity_places)))
            prices = [Decimal(p) for p, _ in parsed]
            if prices != sorted(set(prices), reverse=side == "bids"):
                raise ValueError("levels must be uniquely ordered best first")
            counts[side] = len(parsed)
            levels[side] = parsed[:config.level_cap]
        bids, asks = levels["bids"], levels["asks"]
        empty = not bids or not asks
        crossed = bool(not empty and Decimal(bids[0][0]) >= Decimal(asks[0][0]))
        with localcontext() as ctx:
            ctx.prec = 100
            spread = None if empty else _plain(Decimal(asks[0][0])-Decimal(bids[0][0]))
            bid_depth = _plain(sum((Decimal(q) for _, q in bids), Decimal(0)))
            ask_depth = _plain(sum((Decimal(q) for _, q in asks), Decimal(0)))
        snapshot = data.get("snapshot_id")
        if snapshot is not None:
            _label(snapshot, "snapshot_id")
        return [{**common, **levels, "snapshot_id": snapshot, "received_levels": counts,
                 "level_cap": config.level_cap, "empty": empty, "crossed": crossed,
                 "spread_quote": spread, "integrity": "invalid" if empty or crossed else "ordered_uncrossed",
                 "bid_depth_base": bid_depth,
                 "ask_depth_base": ask_depth,
                 "depth_scope": "retained sampled levels only; no continuous L2 or executions"}]
    if kind != TRADES:
        raise ValueError("unsupported C2 evidence kind")
    raw = data.get("trades")
    if not isinstance(raw, (list, tuple)) or len(raw) > config.trade_cap:
        raise ValueError("bounded normalized trades required")
    result = []
    seen = set()
    for trade in raw:
        if not isinstance(trade, Mapping):
            raise ValueError("trade mapping required")
        trade_id = _label(trade.get("trade_id"), "venue trade_id")
        if trade_id in seen:
            raise ValueError("duplicate trade ID inside response; adapter must disambiguate")
        seen.add(trade_id)
        granularity = trade.get("granularity", "unknown")
        if granularity not in {"raw", "aggregated", "unknown"}:
            raise ValueError("invalid trade granularity")
        side = trade.get("aggressor_side", "unknown")
        if side not in {"buy", "sell", "unknown"}:
            raise ValueError("invalid aggressor side")
        at = trade.get("exchange_event_at")
        at = _time(at, "trade.exchange_event_at") if at is not None else None
        result.append({**common, "trade_id": trade_id,
                       "price": _decimal(trade.get("price"), places=config.price_places),
                       "quantity": _decimal(trade.get("quantity"), places=config.quantity_places),
                       "exchange_event_at": at.isoformat() if at else None,
                       "exchange_age_seconds": (received_at-at).total_seconds() if at else None,
                       "clock_skew": bool(at and at > received_at),
                       "granularity": granularity,
                       "aggressor_side": side if config.aggressor_definition else "unknown",
                       "aggressor_definition": config.aggressor_definition,
                       "reported_side": side,
                       "completeness": "unknown; ID jumps do not prove missing executions"})
    return result


def ingest_spot_evidence(store, config, *, kind, data, received_at, receipt_id,
                         configured_venues=ENABLED_VENUES, failure=None):
    """Atomically append evidence, receipt, health/coverage and sampled gaps.

    Same source/config/kind receipt ID must have identical data/time. Trade/snapshot conflicts
    retain immutable versions rather than silently overwrite. Callers serialize
    ingestion per source; there is no scheduler or concurrent collector here.
    """
    config.require_permission(configured_venues)
    received_at = _time(received_at, "received_at")
    _label(receipt_id, "receipt_id")
    if kind not in {DEPTH, TRADES}:
        raise ValueError("unsupported C2 evidence kind")
    # Normalize before opening/writing anything; malformed responses are atomic failures.
    normalized = normalize_spot_response(config, kind, data, received_at) if failure is None else []
    cursor = data.get("cursor")
    if cursor is not None:
        _label(cursor, "opaque cursor")
    continuity = data.get("continuity", "unknown")
    if continuity not in {"unknown", "gap_reported"}:
        raise ValueError("continuity must remain unknown or an explicit reported gap")
    identity = _hash([config.source.source_id, config.fingerprint, kind, receipt_id])
    receipt_key = "c2-receipt:" + identity
    event = data.get("exchange_event_at")
    digest = _hash([normalized, failure, cursor, continuity, data.get("sequence"),
                    _time(event, "exchange_event_at").isoformat() if event is not None else None])
    # Validation may inspect future-known records solely to reject clock rollback
    # or identity reuse. They never enter normalization or analyst selection.
    all_history = store.view_at(datetime.max.replace(tzinfo=UTC)).evidence_history
    existing = tuple(r for r in all_history if r.observation_id == receipt_key)
    if existing:
        prior = existing[0]
        if prior.payload["response_hash"] != digest or prior.retrieved_at != received_at:
            raise ObservationStoreConflict("receipt identity collision")
        return tuple(prior.payload["evidence_ids"])
    # Full recorded history is intentional: restart does not depend on memory.
    if any(r.source_id == config.source.source_id and r.metric == RECEIPT and r.retrieved_at > received_at
           for r in all_history):
        raise ValueError("local receive clock rollback; quarantine instead of backdating")
    view = store.view_at(received_at)
    history = view.evidence_history
    receipts = [r for r in history if r.metric == RECEIPT and r.source_id == config.source.source_id
                and r.payload.get("config") == config.fingerprint and r.payload.get("kind") == kind]
    last = max(receipts, key=lambda r: (r.retrieved_at, r.observation_id), default=None)
    previous_sequence = max((r.payload["sequence"] for r in receipts if r.payload.get("sequence") is not None), default=None)
    sequence = data.get("sequence") if failure is None else None
    out_of_order = sequence is not None and previous_sequence is not None and sequence < previous_sequence
    rows, ids = [], []
    duplicates = 0
    for payload in normalized:
        logical = payload.get("trade_id") if kind == TRADES else payload.get("snapshot_id") or receipt_id
        subject = "c2:" + _hash([config.source.source_id, config.venue, config.symbol, kind, logical])
        versions = [r for r in history if r.subject == subject and r.metric == kind]
        versions.extend(r for r in rows if r.subject == subject)
        first_seen = min((r.first_seen_time for r in versions), default=received_at)
        # Receive-time diagnostics belong to receipts, not content-version identity.
        content = {k: v for k, v in payload.items() if k not in {"exchange_age_seconds", "clock_skew", "sequence"}}
        content_hash = _hash(content)
        latest = max(versions, key=lambda r: (r.retrieved_at, r.observation_id), default=None)
        same = latest if latest and latest.payload["content_hash"] == content_hash else None
        if same:
            ids.append(same.observation_id)
            duplicates += 1
            continue
        if latest and latest.retrieved_at == received_at:
            raise ObservationStoreConflict("conflicting identity at same local receive time")
        at = versions[0].event_time if versions else received_at
        row = Observation(
            observation_id="c2-evidence:" + _hash([subject, content_hash, receipt_key]),
            source_id=config.source.source_id, subject=subject, metric=kind,
            payload={**payload, "content_hash": content_hash, "received_at": received_at.isoformat(),
                     "out_of_order_sequence": out_of_order, "first_receipt": receipt_key,
                     "identity_conflict": bool(versions), "config": config.fingerprint},
            # Required envelope event_time is a LOCAL identity anchor, never a fabricated exchange time.
            event_time=at, first_seen_time=first_seen, retrieved_at=received_at,
            schema_version=SCHEMA, unit=f"{config.quote}/{config.base};quantity={config.base}",
            quality=ObservationQuality.LOW if payload.get("integrity") == "invalid" or versions else ObservationQuality.UNKNOWN,
            quality_notes=("exchange_event_at nullable/untrusted; envelope event_time is local identity anchor",),
        )
        rows.append(row)
        ids.append(row.observation_id)
    ids = tuple(dict.fromkeys(ids))
    gaps = []
    if last and received_at-last.retrieved_at > timedelta(seconds=config.expected_interval_seconds*2):
        gaps.append(MarketDataGap(config.symbol, kind, last.retrieved_at + timedelta(seconds=config.expected_interval_seconds),
                                  received_at, f"{config.venue}:sampling_gap; end={received_at.isoformat()}; unseen executions unknown"))
    if failure:
        gaps.append(MarketDataGap(config.symbol, kind, received_at, received_at, f"{config.venue}:disconnected; unseen executions unknown"))
    if continuity == "gap_reported":
        gaps.append(MarketDataGap(config.symbol, kind, received_at, received_at,
                                  f"{config.venue}:provider_reported_gap; missing record count unknown"))
    invalid = any(p.get("integrity") == "invalid" for p in normalized)
    receipt = Observation(
        receipt_key, config.source.source_id, "c2-receipt:" + identity, RECEIPT,
        {"kind": kind, "config": config.fingerprint, "venue": config.venue, "symbol": config.symbol,
         "response_hash": digest, "evidence_ids": ids, "duplicates": duplicates,
         "received_at": received_at.isoformat(), "sequence": sequence,
         "out_of_order_sequence": out_of_order, "failure": failure,
         "cursor": cursor, "continuity": continuity,
         "clock_skew_count": sum(p["clock_skew"] for p in normalized),
         "exchange_ages_seconds": [p["exchange_age_seconds"] for p in normalized],
         "coverage": "sampled; missing records unknown; no ID-contiguity assumption"},
        received_at, received_at, received_at, schema_version=SCHEMA,
    )
    detail = json.dumps({"config": config.fingerprint, "outcome": "failure" if failure else "invalid" if invalid else "sampled",
                         "received_records": len(normalized), "duplicates": duplicates,
                         "out_of_order_sequence": out_of_order, "completeness": "unknown"}, sort_keys=True)
    coverage = CoverageRecord("c2-coverage:" + identity, config.source.source_id, config.symbol, kind,
                              received_at, CoverageStatus.UNAVAILABLE if failure else CoverageStatus.LOW_QUALITY if invalid else CoverageStatus.UNKNOWN,
                              detail, (receipt_key, *ids))
    store.append(MarketDataBatch((*rows, receipt), tuple(gaps), received_at, (coverage,), (config.source,)))
    return ids


def fetch_spot_once(store, config, *, kind, receipt_id, fetch: Callable, clock: Callable,
                    configured_venues=ENABLED_VENUES):
    """Injected, single-attempt transport seam; denies before transport or storage.

    Transport owns bounded bytes/time and exact reviewed endpoint checks. This
    module supplies no network implementation. Unexpected programming errors fail.
    """
    config.require_permission(configured_venues)
    try:
        data = fetch()
    except (TimeoutError, ConnectionError):
        return ingest_spot_evidence(store, config, kind=kind, data={}, received_at=clock(),
                                    receipt_id=receipt_id, configured_venues=configured_venues,
                                    failure="transport_unavailable")
    return ingest_spot_evidence(store, config, kind=kind, data=data, received_at=clock(),
                                receipt_id=receipt_id, configured_venues=configured_venues)


def selected_spot_evidence(view: InformationView):
    """Latest locally received sample per source/kind; never latest exchange clock.

    Invalid/stale evidence is disclosed, never used to reconstruct a good book.
    Cap four whole records. No directional/causal signal or trade imbalance.
    """
    candidates = [r for r in view.observations if r.schema_version == SCHEMA and r.metric in {DEPTH, TRADES}
                  and r.is_available_at(view.decision_time)]
    allowed = set()
    latest_sources = {}
    for source, at in view.source_definitions:
        latest_sources.setdefault(source.source_id, []).append((source, at))
    for source_id, definitions in latest_sources.items():
        at = max(at for _, at in definitions)
        # Conflicting same-time definitions fail closed regardless of row order.
        if all(all(dict(source.metadata).get(f"c2_{right}") == "permitted" for right in RIGHTS)
               for source, observed_at in definitions if observed_at == at):
            allowed.add(source_id)
    latest = {}
    for row in sorted(candidates, key=lambda r: (r.retrieved_at, r.observation_id)):
        if row.source_id in allowed:
            latest[(row.source_id, row.metric)] = row
    return tuple(latest[key] for key in sorted(latest)[:4])


def render_spot_evidence(view):
    rows = selected_spot_evidence(view)
    if not rows:
        return []  # Preserve historical context bytes when C2 did not exist.
    result = ["- BTC spot microstructure: sampled venue-local evidence; completeness UNKNOWN; quotes are not executions."]
    for row in rows:
        p = row.payload
        age = (view.decision_time-row.retrieved_at).total_seconds()
        stale = age > p["stale_seconds"]
        reported_stale = p["exchange_age_seconds"] is not None and p["exchange_age_seconds"] > p["stale_seconds"]
        detail = (f"levels={len(p['bids'])}/{len(p['asks'])}; spread={p['spread_quote']}; integrity={p['integrity']}"
                  if row.metric == DEPTH else f"trade={p['trade_id']}; price={p['price']}; quantity={p['quantity']}; "
                  f"aggressor={p['aggressor_side']}; granularity={p['granularity']}")
        receipts = [r for r in view.evidence_history if r.metric == RECEIPT and r.source_id == row.source_id
                    and r.payload.get("kind") == row.metric and r.payload.get("config") == p["config"]]
        last = max(receipts, key=lambda r: (r.retrieved_at, r.observation_id), default=None)
        gaps = sum(g.metric == row.metric and g.subject == p["symbol"] and g.reason.startswith(p["venue"] + ":")
                   for g in view.gaps)
        result.append(f"- {row.observation_id}: {p['venue']} {p['symbol']} {row.metric}; {detail}; "
                      f"age_seconds={age}; stale={stale}; reported_stale_untrusted={reported_stale}; received_at={row.retrieved_at.isoformat()}; "
                      f"available_at={row.available_at.isoformat()}; exchange_event_at={p['exchange_event_at']}; "
                      f"clock_untrusted; identity_conflict={p['identity_conflict']}; sequence_reversed={p['out_of_order_sequence']}; "
                      f"last_transport_failure={last.payload['failure'] if last else 'unknown'}; recorded_gaps={gaps}")
    return result
