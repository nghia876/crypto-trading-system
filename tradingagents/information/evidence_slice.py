"""One-shot eligible USGS headline slice in the canonical store; no body crawler.

Rights gate is specific to the reviewed agency feed configurations. It does not
clear arbitrary government-hosted content or additional feeds. Unknown rights
block before network access. No model/price/BTC condition is involved.
"""

import argparse
import json
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from xml.sax.saxutils import escape

from tradingagents.information.evidence_review import review_packet
from tradingagents.information.news import parse_news_snapshot, poll_once
from tradingagents.information.polling import source_gap_report
from tradingagents.information.sources import SPECIALIST_WORLD_CONFIG
from tradingagents.information.store import SQLiteInformationStore

RIGHTS = {
    "reviewed_at": "2026-11-01",
    "reviewer": "Codex agent; not legal counsel or human article review",
    "reference": "https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits",
    "scope": "USGS-produced feed headline, URL and supplied dates only",
    "basis": "USGS-produced information is US public domain; third-party exceptions excluded",
    "archiving": True, "ai_processing": True,
    "excluded": "bodies, third-party content, photographs, logos, personnel likeness/voice",
    "limitations": "US public-domain basis; other-jurisdiction rights not independently adjudicated",
}


def require_rights(config):
    if config not in SPECIALIST_WORLD_CONFIG[:2]:
        raise ValueError("rights not established for this acquisition slice")
    return RIGHTS


def acquire(store, *, poll_id, session=None, clock=None, limit=4):
    """At most two requests, eight retained items by default, no retries/redirects."""
    if not 1 <= limit <= 8:
        raise ValueError("slice limit must be 1..8 per feed")
    configs = SPECIALIST_WORLD_CONFIG[:2]
    for config in configs:
        require_rights(config)
    outcomes = poll_once(store, configs, poll_id=poll_id, session=session, clock=clock,
                         observation_limit=limit)
    cutoff = max(row.observed_at for row in outcomes)
    view = store.view_at(cutoff)
    selected = {key for outcome in outcomes for key in outcome.evidence_ids}
    rows = [row for row in view.observations if row.observation_id in selected]
    return {
        "rights": RIGHTS, "poll_id": poll_id, "cutoff": cutoff.isoformat(),
        "data_kind": "real_source_unreviewed", "human_reviews": 0,
        "outcomes": [{"source": o.source_id, "status": o.status.value,
                      "detail": json.loads(o.detail)} for o in outcomes],
        "specimens": [{"source_id": row.source_id, "title": row.payload["claim"],
                       "url": row.raw_reference, "published_raw": row.payload["published_raw"],
                       "retrieved_at": row.retrieved_at.isoformat(),
                       "snapshot_sha256": row.payload["snapshot_hash"]} for row in rows],
        "review_queue": [r for r in review_packet(view) if r["evidence_id"] in selected],
        "gaps": source_gap_report(view),
    }


def replay_specimens(store, report):
    """Offline normalized field replay in a temporary canonical-schema test store.

    This is NOT the full original XML: only eligible retained fields were archived.
    Preserve the full-response hash as provenance, never claim it hashes this XML.
    Do not use this to backdate a newly acquired live database.
    """
    outcomes = {o["source"]: o["detail"] for o in report["outcomes"]}
    for specimen in report["specimens"]:
        config = next(c for c in SPECIALIST_WORLD_CONFIG[:2]
                      if c.source.source_id == specimen["source_id"])
        require_rights(config)
        text = ("<rss><channel><item><title>" + escape(specimen["title"]) + "</title><link>"
                + escape(specimen["url"]) + "</link><pubDate>"
                + escape(specimen["published_raw"] or "") + "</pubDate></item></channel></rss>")
        batch = parse_news_snapshot(text, config,
                                    retrieved_at=datetime.fromisoformat(specimen["retrieved_at"]))
        detail = outcomes[specimen["source_id"]]
        rows = tuple(replace(row, payload=dict(row.payload) | {
            "snapshot_hash": specimen["snapshot_sha256"],
            "snapshot_item_count": detail["items"] + detail["omitted_by_slice_limit"],
            "excluded_article_count": detail["excluded_article_count"],
        }) for row in batch.observations)
        store.append(replace(batch, observations=rows))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True,
                        help="Canonical information SQLite path; never a parallel event store")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--poll-id", required=True)
    args = parser.parse_args(argv)
    store = SQLiteInformationStore(args.store)
    report = acquire(store, poll_id=args.poll_id, clock=lambda: datetime.now(UTC))
    with sqlite3.connect(store.path) as connection:
        report["sqlite_integrity"] = connection.execute("PRAGMA integrity_check").fetchone()[0]
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps({"retained": len(report["specimens"]), "outcomes": report["outcomes"],
                      "sqlite_integrity": report["sqlite_integrity"]}, indent=2))


if __name__ == "__main__":
    main()
