"""Read-only Phase 3 exit diagnostic. No polling, scoring, labels or uptime inference.

This is an evidence inventory, not an automatic operational certification. The
review packet is external audit evidence and never enters historical knowledge.
"""

import argparse
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tradingagents.information.evidence_review import article_fingerprint, digest
from tradingagents.information.source_health import health_report
from tradingagents.information.sources import WORLD_DISCOVERY_DOMAINS
from tradingagents.information.store import SQLiteInformationStore
from tradingagents.information.world_radar import (
    ELIGIBLE_CONFIGS,
    RIGHTS_SCOPE,
    coverage_metrics,
)


def classify_source(row):
    """Independent axes: unknown collection cannot diagnose a broken publisher."""
    return {
        "collection": "UNKNOWN" if row["collection_unobserved"] else "OBSERVED_RECENTLY",
        "transport": "FAILURE_OBSERVED" if row["transport"] == "failed" else row["transport"],
        "content": "POSSIBLY_INACTIVE" if row["transport"] in {"responding", "empty"}
        and row["content"] in {"stale_publication", "empty_or_unavailable"} else row["content"],
        "broken_publisher": "NOT PROVEN",
    }


def audit_packet(store, packet, cutoff):
    """Verify original immutable versions; declared identities are not authentication."""
    articles, pairs = packet["articles"], packet["pairs"]
    if not 1 <= len(articles) <= 200 or not 1 <= len(pairs) <= 100:
        raise ValueError("bounded review packet required")
    ids = tuple(a["evidence_id"] for a in articles)
    rows = {r.observation_id: r for r in store.evidence_by_ids(ids, cutoff)}
    hashes = {a["evidence_id"]: a["article_sha256"] for a in articles}
    valid = len(set(ids)) == len(ids) and all(
        key in rows and article_fingerprint(rows[key]) == hashes[key] for key in ids)
    valid = valid and all(len(p["evidence_ids"]) == 2
                          and len(set(p["evidence_ids"])) == 2
                          and p["article_sha256"] == [hashes.get(k) for k in p["evidence_ids"]]
                          for p in pairs)
    body = {k: v for k, v in packet.items() if k != "packet_sha256"}
    declared = sum(p.get("review_kind") == "human_declared" for p in pairs)
    return {
        "packet_hash_valid": digest(body) == packet.get("packet_sha256"),
        "original_versions_valid_at_cutoff": valid,
        "article_count": len(articles), "pair_count": len(pairs),
        "pending_pairs": sum(p.get("review_status") == "pending" for p in pairs),
        "human_declared_pairs": declared,
        "human_participation_authenticated": False,
        "pair_ids": [p["pair_id"] for p in pairs],
        "label_provenance": "External supplied packet only; agent URL checks are not human labels; no import or adjudication",
    }


def readiness_report(store, packet, *, cutoff, interval=900):
    health = health_report(store, ELIGIBLE_CONFIGS, cutoff=cutoff, interval=interval)
    view = store.view_at(cutoff)
    # Include historical config fingerprints rather than silently losing older
    # attempts when a rights-review date changes the active fingerprint.
    journal = [(r, json.loads(r.detail)) for r in view.coverage
               if r.coverage_id.startswith("news-poll:") and r.metric == "narrative.event"]
    times = sorted(r.observed_at for r, _ in journal)
    active = {c.fingerprint for c in ELIGIBLE_CONFIGS}
    review = audit_packet(store, packet, cutoff)
    with sqlite3.connect(Path(store.path).resolve().as_uri() + "?mode=ro", uri=True) as conn:
        integrity = [r[0] for r in conn.execute("PRAGMA integrity_check")]
    metrics = coverage_metrics(view)
    # Legacy metrics supplies a fixed zero, which is not an audit of external
    # labels. This report instead uses the explicitly supplied, hash-bound packet.
    metrics.pop("human_reviews", None)
    narrative = [r for r in (*view.observations, *view.evidence_history)
                 if r.metric == "narrative.event"]
    first_available = min((r.available_at for r in narrative), default=None)
    early_cutoff = first_available-timedelta(microseconds=1) if first_available else None
    early_count = sum(r.metric == "narrative.event" for r in store.view_at(early_cutoff).observations) if early_cutoff else None
    reopened = SQLiteInformationStore(store.path, read_only=True)
    reopen_equal = health == health_report(reopened, ELIGIBLE_CONFIGS, cutoff=cutoff, interval=interval)
    replay = {"early_cutoff": early_cutoff.isoformat() if early_cutoff else None,
              "early_narrative_records": early_count,
              "late_narrative_records": sum(r.metric == "narrative.event" for r in view.observations),
              "reopened_health_identical": reopen_equal,
              "scope": "Store boundary and reopen probe; not end-to-end historical reasoning or clock authentication"}
    sources = [dict(row, classification=classify_source(row)) for row in health["sources"]]
    def gate(name, status, evidence):
        return {"requirement": name, "status": status, "evidence": evidence}

    gates = [
        gate("SQLite integrity", "PASS" if integrity == ["ok"] else "BLOCKED", integrity),
        gate("Original review packet integrity and PIT version binding",
             "PASS" if review["packet_hash_valid"] and review["original_versions_valid_at_cutoff"] else "BLOCKED", review),
        gate("Sustained polling/restarts and bounded discovery latency", "NOT PROVEN",
             "Journal span is not uptime. Finite jobs, gaps, rolling-feed omissions and host clock uncertainty remain."),
        gate("Timely global WORLD incident coverage", "NOT PROVEN",
             "Publication/update recency is metadata, not incident occurrence, recall or measured reaction alignment."),
        gate("Independent incident origins and syndication resolution", "NOT PROVEN",
             "Publisher groups and canonical URL collapse do not establish reporting independence."),
        gate("Independent human article/pair adjudication and untouched cluster holdout", "NOT PROVEN", review),
        gate("Rights/access for withheld feeds", "BLOCKED", RIGHTS_SCOPE["blocked"]),
        gate("Macro completion", "BLOCKED",
             "Daily Treasury TGA/yields rights-gated; BEA GDP/PCE incomplete; BLS live calendar unavailable; FRED disabled."),
        gate("Canonical early/late store boundary and reopened health",
             "PASS" if early_count == 0 and narrative and reopen_equal else "NOT PROVEN", replay),
        gate("Actual mixed analyst graph regression", "NOT PROVEN",
             "Separate offline test run required; this read-only inventory does not execute the analyst graph."),
    ]
    return {
        "schema_version": 1, "cutoff": health["cutoff"], "decision": "NO-GO",
        "phase_3": "IN_PROGRESS", "scope": "Read-only canonical evidence; no network or production certification",
        "journal": {
            "attempts_all_fingerprints": len(journal),
            "attempts_inactive_fingerprints": sum(d.get("config") not in active for _, d in journal),
            "first_attempt": times[0].isoformat() if times else None,
            "last_attempt": times[-1].isoformat() if times else None,
            "span_seconds": (times[-1]-times[0]).total_seconds() if times else 0,
            "interpretation": "Elapsed span is not observed uptime or a restart count; absent intervals have unknown cause",
        },
        "health": dict(health, sources=sources), "coverage": metrics,
        "world_families": [{
            "family": family,
            "configured_feeds": sum(c.domain == family for c in ELIGIBLE_CONFIGS),
            "fresh_24h_metadata": sum(s["fresh_24h"] for s in metrics["sources"]
                                       if s["family"] == family),
            "incident_coverage": "NOT PROVEN",
        } for family in WORLD_DISCOVERY_DOMAINS],
        "metadata_totals": {
            "source_url_records": sum(s["items"] for s in metrics["sources"]),
            "fresh_24h_publication_or_update": sum(s["fresh_24h"] for s in metrics["sources"]),
            "fresh_7d_publication_or_update": sum(s["fresh_7d"] for s in metrics["sources"]),
            "fresh_update_only_7d": sum(s["fresh_update_only"] for s in metrics["sources"]),
        },
        "rights_scope": RIGHTS_SCOPE, "review": review, "checklist": gates,
        "replay_probe": replay,
        "sqlite_integrity": integrity,
        "limitations": [
            "All WORLD families remain required without BTC keyword or price prerequisites.",
            "Water/food announcements are not global scarcity monitoring; energy policy is not physical grid telemetry.",
            "Cyber, specialist AI, public-health outbreak timeliness and geographic/language diversity remain unproven.",
            "No human labels, independent confirmation, scheduler or historical polls are manufactured.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--as-of", help="aware ISO cutoff; omit for current UTC")
    parser.add_argument("--interval", type=int, default=900)
    args = parser.parse_args(argv)
    if args.packet.stat().st_size > 2_000_000:
        parser.error("packet exceeds 2 MB")
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    result = readiness_report(SQLiteInformationStore(args.store, read_only=True), packet,
                              cutoff=datetime.fromisoformat(args.as_of) if args.as_of else datetime.now(UTC),
                              interval=args.interval)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
