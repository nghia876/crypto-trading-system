"""Bounded recurring news jobs; checkpoints and health live in the canonical store.

No daemon: invoke once from Task Scheduler. Failed attempts retry on later jobs,
never in a tight loop. Coverage records are the append-only checkpoint journal.
"""

from __future__ import annotations

import argparse
import json
import os
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import requests

from tradingagents.information.binance_spot import CoverageRecord, CoverageStatus, MarketDataBatch
from tradingagents.information.news import _digest, poll_once
from tradingagents.information.observations import _require_aware
from tradingagents.information.sources import BROAD_NEWS_CONFIG
from tradingagents.information.store import SQLiteInformationStore


@contextmanager
def job_lock(store):
    """OS advisory lock released on crash; same store resolves to the same lock file."""
    path = Path(store.path).resolve().with_suffix(Path(store.path).suffix + ".news.lock")
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _history(store, config, now):
    rows = []
    for record in store.polling_history(config.fingerprint, now):
        if record.coverage_id.startswith("news-poll:"):
            detail = json.loads(record.detail)
            if detail.get("config") == config.fingerprint:
                rows.append((record, detail))
    return sorted(rows, key=lambda x: (x[0].observed_at, x[0].coverage_id))


def _state(store, config, now, interval):
    history = _history(store, config, now)
    failures = 0
    for _, detail in reversed(history):
        if detail["outcome"] != "failure":
            break
        failures += 1
    last = history[-1][0] if history else None
    delay = min(86400, interval * 2 ** min(failures, 10))
    if history:
        # A server's valid Retry-After is a lower bound, including >24h.
        delay = max(delay, history[-1][1].get("retry_after_seconds") or 0)
    due = (
        (
            last.observed_at
            + timedelta(
                seconds=min(
                    delay, (datetime.max.replace(tzinfo=UTC) - last.observed_at).total_seconds() - 1
                )
            )
        )
        if last
        else datetime.min.replace(tzinfo=UTC)
    )
    success = next(
        (r for r, d in reversed(history) if d["outcome"] == "success" and r.evidence_ids), None
    )
    return history, failures, last, due, success


def coordinate(
    store,
    configs=BROAD_NEWS_CONFIG,
    *,
    now=None,
    interval=900,
    max_sources=4,
    session=None,
    clock=None,
):
    """Run due configurations fairly, at most one request each, then persist health.

    Callers must serialize via job_lock (CLI does so). A crash before append can
    refetch that source, but deterministic slot IDs prevent duplicate committed
    attempts. A completed source is skipped on restart. Missed intervals are
    disclosed, never synthesized as successful historical collection.
    """
    now = now or datetime.now(UTC)
    _require_aware("now", now)
    now = now.astimezone(UTC)
    if not 60 <= interval <= 86400 or not 2 <= max_sources <= 16:
        raise ValueError("interval must be 60..86400 seconds; source budget 2..16")
    if not 1 <= len(configs) <= 16 or len({c.fingerprint for c in configs}) != len(configs):
        raise ValueError("one to sixteen distinct configurations required")
    states = {c.fingerprint: _state(store, c, now, interval) for c in configs}
    # Round robin domains; oldest due within each domain rotates providers naturally.
    domains = sorted({c.domain for c in configs})
    queues = {
        d: sorted(
            (c for c in configs if c.domain == d and states[c.fingerprint][3] <= now),
            key=lambda c: (states[c.fingerprint][3], c.fingerprint),
        )
        for d in domains
    }
    chosen = []
    used_hosts = set()
    recent_hosts = {
        urlsplit(c.source.endpoint).hostname
        for c in configs
        if states[c.fingerprint][2] is not None
        and (
            (now - states[c.fingerprint][2].observed_at).total_seconds() < 30
            or (
                states[c.fingerprint][0][-1][1].get("http_status") in {429, 503}
                and states[c.fingerprint][3] > now
            )
        )
    }
    while len(chosen) < max_sources and any(queues.values()):
        for domain in domains:
            if queues[domain] and len(chosen) < max_sources:
                candidate = queues[domain].pop(0)
                host = urlsplit(candidate.source.endpoint).hostname
                if host not in used_hosts | recent_hosts:
                    chosen.append(candidate)
                    used_hosts.add(host)
    slot = int(now.timestamp()) // interval
    outcomes = []
    for config in chosen:
        # Policy interval included: changing cadence never reuses a logical attempt ID.
        outcomes.extend(
            poll_once(
                store,
                (config,),
                poll_id=f"recurring-v1:{interval}:{slot}",
                session=session,
                clock=clock,
            )
        )
    completed = max([now] + [r.observed_at for r in outcomes])
    health = []
    for config in configs:
        _, failures, last, due, success = _state(store, config, completed, interval)
        previous = states[config.fingerprint][2]
        gap_seconds = (now - previous.observed_at).total_seconds() if previous else None
        evidence = store.evidence_by_ids(success.evidence_ids, completed) if success else ()
        publications = [r.publication_time for r in evidence if r.publication_time]
        newest_publication = max(publications) if publications else None
        detail = {
            "policy_version": "recurring-v1",
            "interval_seconds": interval,
            "max_sources": max_sources,
            "host_cooldown_seconds": 30,
            "slot": slot,
            "newest_publication": newest_publication.isoformat() if newest_publication else None,
            "content_stale": (completed - newest_publication > timedelta(days=1))
            if newest_publication
            else None,
            "publication_unknown_items": sum(r.publication_time is None for r in evidence),
            "config": config.fingerprint,
            "domain": config.domain,
            "last_attempt": last.observed_at.isoformat() if last else None,
            "last_nonempty": success.observed_at.isoformat() if success else None,
            "next_due": due.isoformat(),
            "consecutive_failures": failures,
            "late": previous is not None
            and states[config.fingerprint][3] < now - timedelta(seconds=interval),
            "missed_interval_seconds": gap_seconds
            if gap_seconds and gap_seconds > 2 * interval
            else None,
            "rolling_window_gap": bool(gap_seconds and gap_seconds > 86400),
            "stale": success is None
            or completed - success.observed_at > timedelta(seconds=2 * interval),
            "budget_deferred": config not in chosen and states[config.fingerprint][3] <= now,
            "completeness": "unknown; rolling feeds cannot prove absence or recover missed history",
            "independence": "unknown; providers/domains are not independent confirmations",
        }
        status = (
            CoverageStatus.UNAVAILABLE
            if failures
            else CoverageStatus.STALE
            if detail["stale"]
            else CoverageStatus.UNKNOWN
        )
        record = CoverageRecord(
            "news-health:" + _digest(config.fingerprint + completed.isoformat()),
            config.source.source_id,
            config.domain,
            "narrative.collection_health",
            completed,
            status,
            json.dumps(detail, sort_keys=True),
            (),
        )
        health.append(record)
    store.append(
        MarketDataBatch(
            (), (), completed, tuple(health), tuple(c.source_definition for c in configs)
        )
    )
    return tuple(outcomes), tuple(health)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("poll-once", "health"))
    parser.add_argument("--store", required=True, help="EXACT graph information_store_path")
    parser.add_argument("--interval", type=int, default=900)
    parser.add_argument("--max-sources", type=int, default=4)
    args = parser.parse_args(argv)
    store = SQLiteInformationStore(args.store)
    if args.command == "health":
        view = store.view_at(datetime.now(UTC))
        records = [r for r in view.coverage if r.metric == "narrative.collection_health"]
        latest = {r.source_id: r for r in sorted(records, key=lambda r: r.observed_at)}
        print(
            json.dumps(
                {
                    k: {"observed_at": v.observed_at.isoformat(), **json.loads(v.detail)}
                    for k, v in latest.items()
                },
                indent=2,
            )
        )
        return 0
    with job_lock(store), requests.Session() as session:
        outcomes, health = coordinate(
            store, interval=args.interval, max_sources=args.max_sources, session=session
        )
    print(
        json.dumps(
            {
                "polls": [json.loads(r.detail) for r in outcomes],
                "health": [json.loads(r.detail) for r in health],
            },
            indent=2,
        )
    )
    return int(any(r.status == CoverageStatus.UNAVAILABLE for r in outcomes))


if __name__ == "__main__":
    raise SystemExit(main())
