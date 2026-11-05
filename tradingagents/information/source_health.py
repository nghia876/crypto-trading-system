"""Reproducible as-of operational measurements from the canonical polling journal.

No network, extra database, inferred uptime, incident labels or source corroboration.
"""

import argparse
import json
from collections import Counter
from datetime import UTC, datetime, timedelta

from tradingagents.information.observations import _require_aware
from tradingagents.information.store import SQLiteInformationStore


def health_report(store, configs, *, cutoff, interval=900):
    """Read only records available by cutoff; recompute age even with no new job.

    Gaps mean collection unobserved, not PC downtime or publisher silence.
    Lag is metadata availability lag, never incident detection latency.
    """
    _require_aware("cutoff", cutoff)
    cutoff = cutoff.astimezone(UTC)
    if not 60 <= interval <= 86400:
        raise ValueError("interval must be 60..86400 seconds")
    view = store.view_at(cutoff)
    result = []
    for config in configs:
        # Coordinator's checkpoint query intentionally retains only 12 recent
        # attempts. Operational totals must inspect the full as-of journal.
        history = sorted([
            (r, json.loads(r.detail)) for r in view.coverage
            if r.coverage_id.startswith("news-poll:") and r.metric == "narrative.event"
            and json.loads(r.detail).get("config") == config.fingerprint
        ], key=lambda item: (item[0].observed_at, item[0].coverage_id))
        counts = Counter(d["outcome"] for _, d in history)
        errors = Counter(d.get("error") or "unknown" for _, d in history
                         if d["outcome"] == "failure")
        last, detail = history[-1] if history else (None, {})
        selections = [r for r in view.coverage if r.metric == "narrative.collection_health"
                      and json.loads(r.detail).get("config") == config.fingerprint]
        selection = max(selections, key=lambda r: (r.observed_at, r.coverage_id), default=None)
        successes = [r for r, d in history if d["outcome"] != "failure"]
        rows = [r for r in view.observations
                if r.metric == "narrative.event" and r.is_available_at(cutoff)
                and r.payload.get("config_fingerprint") == config.fingerprint]
        latest = {}
        for row in sorted(rows, key=lambda r: (r.available_at, r.observation_id)):
            latest[row.subject] = row
        rows = list(latest.values())
        publication = max((r.publication_time for r in rows
                           if r.publication_time and r.publication_time <= cutoff), default=None)
        update = max((r.effective_time for r in rows
                      if r.effective_time and r.effective_time <= cutoff), default=None)
        def age(value):
            return (cutoff - value).total_seconds() if value else None

        def lag_summary(values):
            ordered = sorted(values)
            return {"count": len(ordered), "min_seconds": min(ordered, default=None),
                    "max_seconds": max(ordered, default=None),
                    "median_seconds": (ordered[(len(ordered)-1)//2] + ordered[len(ordered)//2])/2
                    if ordered else None}

        # First seen is locally measured; publication and update remain distinct.
        publication_lags = [(r.first_seen_time-r.publication_time).total_seconds()
                            for r in rows if r.publication_time
                            and r.publication_time <= r.first_seen_time]
        retrieval_lags = [(r.retrieved_at-r.first_seen_time).total_seconds() for r in rows]
        update_lags = [(r.first_seen_time-r.effective_time).total_seconds() for r in rows
                       if r.effective_time and r.effective_time <= r.first_seen_time]
        publication_retrieval = [(r.retrieved_at-r.publication_time).total_seconds() for r in rows
                                 if r.publication_time and r.publication_time <= r.retrieved_at]
        gaps = []
        for previous, following in zip(history, history[1:], strict=False):
            start, end = previous[0].observed_at, following[0].observed_at
            if end-start > timedelta(seconds=2*interval):
                gaps.append({"from": (start+timedelta(seconds=interval)).isoformat(),
                             "until": end.isoformat(), "seconds": (end-start).total_seconds()-interval,
                             "cause": "UNKNOWN; offline PC, budget, backoff or missed invocation"})
        open_gap = last is None or age(last.observed_at) > 2*interval
        transport = ("never_polled" if last is None else "failed"
                     if detail.get("outcome") == "failure" else "empty"
                     if detail.get("outcome") == "empty" else "responding")
        content = ("empty_or_unavailable" if not rows else "publication_unknown"
                   if publication is None else "fresh_24h"
                   if age(publication) <= 86400 else "stale_publication")
        result.append({
            "source_id": config.source.source_id, "config": config.fingerprint,
            "domain": config.domain, "publisher_group": config.source.provider,
            "origin_independence": "UNKNOWN; publisher groups are not incident origins",
            "rights_reference": dict(config.source.metadata).get("rights_reference"),
            "rights_gate": "caller-selected configuration; acquisition still requires exact policy and robots gate",
            "attempts": len(history), "outcomes": dict(counts), "errors": dict(errors),
            "timeout_count": sum(n for key, n in errors.items() if "Timeout" in key),
            "rate_limit_count": sum(d.get("http_status") == 429 for _, d in history),
            "last_attempt": last.observed_at.isoformat() if last else None,
            "last_success": successes[-1].observed_at.isoformat() if successes else None,
            "last_error": detail.get("error"), "transport": transport,
            "latest_intake": {key: detail.get(key) for key in (
                "snapshot_item_count", "parsed_unique_items", "items", "retention_limit",
                "omitted_by_slice_limit", "outside_window_count", "excluded_article_count",
                "parser_overflow_count", "atomic_rejected_item_count", "window_start",
                "window_end", "source_order", "provider_window")},
            "intake_contract": "reported when recorded; null on legacy attempts means UNKNOWN",
            "latest_selection": json.loads(selection.detail).get("selection_status", "unknown_legacy")
            if selection else "unknown_not_recorded",
            "collection_unobserved": open_gap, "closed_unknown_intervals": gaps,
            "open_unknown_from": (last.observed_at+timedelta(seconds=interval)).isoformat()
            if last and open_gap else None,
            "baseline_unknown": last is None,
            "content": content, "unique_articles": len(rows),
            "newest_publication": publication.isoformat() if publication else None,
            "publication_age_seconds": age(publication),
            "newest_source_update": update.isoformat() if update else None,
            "source_update_age_seconds": age(update),
            "publication_unknown_articles": sum(r.publication_time is None for r in rows),
            "first_seen_minus_publication": lag_summary(publication_lags),
            "first_seen_minus_source_update": lag_summary(update_lags),
            "latest_retrieval_minus_publication": lag_summary(publication_retrieval),
            "latest_retrieval_minus_first_seen": lag_summary(retrieval_lags),
            "clock_anomalies": sum(r.publication_time is not None and r.publication_time > r.first_seen_time
                                   for r in rows),
            "activity_interpretation": "failure does not establish broken publisher; successful stale/empty feed may be inactive; absence of incidents UNKNOWN",
        })
    return {"cutoff": cutoff.isoformat(), "interval_seconds": interval,
            "measurement": "canonical journal; no inferred polls or uptime; update is not occurrence",
            "sources": result}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--as-of", help="aware ISO timestamp; default current UTC")
    parser.add_argument("--interval", type=int, default=900)
    args = parser.parse_args(argv)
    from tradingagents.information.runtime_store import runtime_store_path
    from tradingagents.information.world_radar import ELIGIBLE_CONFIGS, RIGHTS_SCOPE
    store = SQLiteInformationStore(runtime_store_path(args.store), read_only=True)
    report = health_report(store, ELIGIBLE_CONFIGS,
                           cutoff=datetime.fromisoformat(args.as_of) if args.as_of else datetime.now(UTC),
                           interval=args.interval)
    report["rights_scope"] = RIGHTS_SCOPE
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
