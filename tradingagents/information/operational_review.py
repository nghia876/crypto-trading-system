"""Prepare neutral human forms for existing proposals; never adjudicate or import.

Original proposal files stay untouched. Metadata checks are agent research, not
human labels. Article occurrence/location review precedes separate pair review.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from tradingagents.information.evidence_review import article_fingerprint, digest
from tradingagents.information.observations import _require_aware
from tradingagents.information.store import SQLiteInformationStore


def prepare_packet(store, proposals, *, cutoff, checks):
    _require_aware("cutoff", cutoff)
    if not 1 <= len(proposals) <= 100:
        raise ValueError("bounded proposal list required")
    ids = {key for pair in proposals for key in pair["evidence_ids"]}
    rows = {r.observation_id: r for r in store.evidence_by_ids(tuple(sorted(ids)), cutoff)}
    if ids != rows.keys():
        raise ValueError("original evidence versions unavailable at cutoff")
    articles = []
    for key in sorted(ids):
        row = rows[key]
        articles.append({
            "evidence_id": key, "article_sha256": article_fingerprint(row),
            "original_url": row.raw_reference, "title": row.payload.get("claim"),
            "published_at": row.publication_time.isoformat() if row.publication_time else None,
            "source_updated_at": row.effective_time.isoformat() if row.effective_time else None,
            "first_seen_at": row.first_seen_time.isoformat(),
            "retrieved_at": row.retrieved_at.isoformat(),
            "snapshot_sha256": row.payload.get("snapshot_hash"),
            "publisher_group": row.payload.get("publisher_group"),
            "agent_url_check": checks.get(row.raw_reference),
            "status": "UNREVIEWED", "review_kind": "pending", "reviewer": None,
            "recorded_at": None, "occurrence_start": None, "occurrence_end": None,
            "location_key": None, "episode_key": None, "rationale": None, "provenance": None,
            "context_fingerprints": {}, "supersedes": None,
        })
    forms = [{
        "pair_id": f"phase38-{index+1}", "evidence_ids": pair["evidence_ids"],
        "article_sha256": [article_fingerprint(rows[key]) for key in pair["evidence_ids"]],
        "choices": {"same_event": "Same incident", "different_event": "Different incident",
                    "unknown": "Insufficient evidence"},
        "status": "UNREVIEWED", "label": "unknown", "review_status": "pending",
        "reviewer": None, "reviewed_at": None, "review_kind": "pending",
        "rationale": None, "provenance": None, "confidence": "unknown",
        "occurrence_evidence": None, "location_evidence": None,
        "origin_independence": "UNKNOWN", "reporting_relationship": "unknown",
        "family": rows[pair["evidence_ids"][0]].payload.get("domain"),
        "stratum": "real_unreviewed", "label_version": 1, "supersedes_label_sha256": None,
    } for index, pair in enumerate(proposals)]
    body = {"cutoff": cutoff.isoformat(), "proposal_sha256": digest(proposals),
            "human_reviews": 0, "articles": articles, "pairs": forms,
            "procedure": "Review original article occurrence/location first without pair predictions; separate pair adjudicator records actual identity/time and cited evidence. Unknown or disputed evidence must not be promoted. No matcher tuning or holdout reuse."}
    return body | {"packet_sha256": digest(body)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--proposals", type=Path, required=True)
    parser.add_argument("--checks", type=Path, required=True)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("preserve existing packet; use a new filename")
    for path in (args.proposals, args.checks):
        if path.stat().st_size > 2_000_000:
            parser.error("input exceeds 2 MB")
    from tradingagents.information.runtime_store import runtime_store_path
    result = prepare_packet(SQLiteInformationStore(runtime_store_path(args.store), read_only=True),
                            json.loads(args.proposals.read_text(encoding="utf-8")),
                            cutoff=datetime.fromisoformat(args.cutoff),
                            checks=json.loads(args.checks.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
