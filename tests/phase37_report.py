"""Archive retained real metadata and UNREVIEWED proposals, without scoring or labels."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from tradingagents.information.evidence_review import review_packet
from tradingagents.information.polling import source_gap_report
from tradingagents.information.store import SQLiteInformationStore
from tradingagents.information.world_radar import ELIGIBLE_CONFIGS, RIGHTS_SCOPE, coverage_metrics


def main():
    root = Path(__file__).resolve().parents[2]
    folder = Path(__file__).parent / "fixtures/phase37"
    folder.mkdir(exist_ok=False)
    store = SQLiteInformationStore(root / "canonical-information.sqlite3", read_only=True)
    cutoff = datetime.now(UTC)
    view = store.view_at(cutoff)
    source_ids = {c.source.source_id for c in ELIGIBLE_CONFIGS}
    latest = {}
    for row in sorted(view.observations, key=lambda r: (r.available_at, r.observation_id)):
        if (row.source_id in source_ids and row.metric == "narrative.event"
                and row.retrieved_at >= datetime(2026, 11, 1, 8, 14, tzinfo=UTC)):
            latest[row.source_id, row.subject] = row
    rows = list(latest.values())
    specimens = [{
        "evidence_id": r.observation_id, "source_id": r.source_id,
        "title": r.payload["claim"], "url": r.raw_reference,
        "published_raw": r.payload["published_raw"], "updated_raw": r.payload["updated_raw"],
        "retrieved_at": r.retrieved_at.isoformat(), "available_at": r.available_at.isoformat(),
        "first_seen_time": r.first_seen_time.isoformat(),
        "snapshot_sha256": r.payload["snapshot_hash"],
        "publisher_group": r.payload["publisher_group"],
        "origin_cluster": "publisher:" + r.payload["publisher_group"],
        "duplicate_cluster": r.subject, "syndication": "UNKNOWN", "status": "UNREVIEWED",
    } for r in rows]
    ids = {r.observation_id for r in rows}
    articles = [dict(r, status="UNREVIEWED") for r in review_packet(view) if r["evidence_id"] in ids]

    def find(fragment, exclude="\0"):
        return next(r for r in specimens if fragment in r["title"] and exclude not in r["title"])

    def pair(a, b, suggestion, rationale, location, occurrence):
        return {"evidence_ids": [a["evidence_id"], b["evidence_id"]],
                "articles": [a, b], "status": "UNREVIEWED", "review_status": "pending",
                "label": "unknown", "suggested_pair_identity": suggestion,
                "rationale": rationale, "occurrence_date": occurrence,
                "location": location, "uncertainty": "Headlines only; occurrence and identity require article adjudication",
                "independent_publishers": a["publisher_group"] != b["publisher_group"],
                "independent_original_origins": "UNVERIFIED", "human_reviews": 0}

    pairs = [
        pair(find("Following Hurricane Isaias, Day 2"),
             find("Following Hurricane Isaias", "Day 2"), "plausible_same_incident",
             "Same named hurricane, Florida Panhandle flood response and explicit Day 2 follow-up. Same USGS publisher; not independent corroboration.",
             "Florida Panhandle, USA (title only)", None),
    ]
    # Deliberately distinct named phenomena/locations, still pending human review.
    pairs.append(pair(find("Following Hurricane Isaias", "Day 2"), find("southeast of Easter Island"),
                    "plausible_distinct_incidents", "Florida flood response versus Easter Island earthquake. Same USGS publishing group.",
                    "Florida Panhandle / southeast of Easter Island (titles only)", None))
    pairs.append(pair(find("New report shows toll of Chickenpox"), find("Varicella epidemiological"),
                      "possible_same_report_release", "Possible news release and underlying varicella report; not established same outbreak/incident.",
                      "UK; exact reporting geography unreviewed", None))
    reports = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(root.glob("phase37-live-*.json"))]
    with sqlite3.connect(store.path) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    outputs = {
        "real_specimens.json": {"cutoff": cutoff.isoformat(), "specimens": specimens,
                                "data_kind": "real_source_unreviewed", "rights": RIGHTS_SCOPE},
        "articles_unreviewed.json": articles,
        "pairs_unreviewed.json": pairs,
        "operational_results.json": {
            "cutoff": cutoff.isoformat(), "metrics": coverage_metrics(view),
            "gaps": source_gap_report(view, ELIGIBLE_CONFIGS), "sqlite_integrity": integrity,
            "live_runs": [{"cutoff": r["cutoff"], "polls": r["polls"], "robots": r["robots"]} for r in reports],
            "human_reviews": 0, "accuracy_evaluation": "NOT RUN; all proposals UNREVIEWED",
        },
    }
    for name, value in outputs.items():
        (folder / name).write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"specimens": len(specimens), "pairs": len(pairs), "sqlite_integrity": integrity}))


if __name__ == "__main__":
    main()
