"""Reproduce the local real-source diagnostic without any network or tuning.

Input: saved acquisition report and the SAME canonical information store.
Writes frozen data/labels/manifest BEFORE first scoring; refuses overwrites.
These are title-only AGENT annotations, never independent human judgments.
"""

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tradingagents.information.evidence_review import freeze_manifest, score_frozen
from tradingagents.information.store import SQLiteInformationStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquisition", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = [args.output / name for name in (
        "phase36_usgs_specimens.json", "phase36_pair_labels.json",
        "phase36_frozen_manifest.json", "phase36_metrics.json"
    )]
    if any(path.exists() for path in files):
        parser.error("frozen outputs already exist; never overwrite an inspected holdout")
    data = json.loads(args.acquisition.read_text(encoding="utf-8"))
    articles = data["review_queue"]
    if len(articles) != 8:
        parser.error("this bounded diagnostic requires the recorded eight-item slice")
    now = datetime.now(UTC)
    for article in articles:
        article.update(
            # Conservative partition unit, NOT a claim that all reports are one incident.
            incident_cluster="conservative:usgs-entire-eight-item-slice",
            origin_cluster="publisher:USGS", review_kind="agent_reviewed",
            status="pending", reviewer="Codex agent", recorded_at=now.isoformat(),
            provenance="Title-only inspection of live acquired USGS headline fields",
            rationale="Occurrence/location adjudication still requires human review; null context",
        )
    # Predeclared title-only strata. No match outputs inspected to choose these.
    definitions = [
        (0, 4, "different_event", "nearby_unrelated", "NY streamflow versus CA flood: different reported places"),
        (1, 5, "different_event", "hard_negative", "Oregon fires/gages versus Oregon atmospheric river; title-only different hazards"),
        (2, 7, "different_event", "hard_negative", "NJ low flow versus Ohio flooding: different reported places"),
        (3, 6, "unknown", "correction", "CA runoff reports: occurrence identity/correction relationship unresolved"),
        (4, 6, "unknown", "syndication", "CA flooding/runoff: one publisher; shared reporting origin unresolved"),
    ]
    labels = [{
        "evidence_ids": [articles[a]["evidence_id"], articles[b]["evidence_id"]],
        "label": value, "family": "real_usgs_water", "stratum": stratum,
        "review_status": "agent_reviewed", "reviewer": "Codex agent (not human)",
        "reviewed_at": now.isoformat(), "confidence": "low",
        "reporting_relationship": "same_publisher_syndication",
        "provenance": "Real acquired headline fields; agent title-only labels; no body/human review",
        "rationale": rationale,
    } for a, b, value, stratum, rationale in definitions]
    manifest = freeze_manifest(articles, labels, seed="phase36-usgs-v1", frozen_at=now)
    specimen = {key: value for key, value in data.items() if key != "review_queue"}
    args.output.mkdir(parents=True, exist_ok=True)
    for path, value in zip(files[:3], (specimen, labels, manifest), strict=True):
        path.write_text(json.dumps(value, sort_keys=True, indent=2), encoding="utf-8")
    cutoff = datetime.fromisoformat(data["cutoff"])
    early = min(datetime.fromisoformat(s["retrieved_at"]) for s in data["specimens"]) - timedelta(microseconds=1)
    store = SQLiteInformationStore(args.store, read_only=True)
    result = score_frozen(store, manifest, labels, [early, cutoff])
    reopened = score_frozen(SQLiteInformationStore(args.store, read_only=True),
                            manifest, labels, [early, cutoff])
    if result != reopened:
        raise AssertionError("reopen changed frozen evaluation")
    result.update(data_kind="real_source_agent_title_labels", human_reviews=0,
                  independent_origins=1, development_items=0, holdout_items=8,
                  limitations="No positives, independent labels, body review or accuracy validation; holdout retired",
                  sqlite_integrity=data["sqlite_integrity"], reopen_identical=True)
    files[3].write_text(json.dumps(result, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
