"""Bounded review packets and connected-cluster holdouts; never matching features.

Pair labels stay in external JSON. Per-article context enters SQLite only through
record_event_context after explicit adjudication. Reviewer identities are claims,
not authenticated human participation. Freeze before scoring; retire after use.
"""

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime

from tradingagents.information.event_context import record_event_context
from tradingagents.information.event_evaluation import evaluate
from tradingagents.information.observations import _require_aware


def _plain(value):
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def digest(value):
    return hashlib.sha256(
        json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def article_fingerprint(row):
    return digest({
        "id": row.observation_id, "source": row.source_id, "payload": row.payload,
        "url": row.raw_reference, "event": row.event_time, "published": row.publication_time,
        "seen": row.first_seen_time, "retrieved": row.retrieved_at,
        "updated": row.effective_time, "supersedes": row.supersedes_observation_id,
    })


def review_packet(view):
    """Metadata-only queue, deliberately containing no pair labels or predictions."""
    return [{
        "evidence_id": row.observation_id,
        "article_sha256": article_fingerprint(row),
        "original_url": row.raw_reference,
        "claim": row.payload.get("claim"),
        "publisher": row.payload.get("publisher_group", "unknown"),
        "published_at": _plain(row.publication_time),
        "first_seen_at": _plain(row.first_seen_time),
        "retrieved_at": _plain(row.retrieved_at),
        "source_updated_at": _plain(row.effective_time),
        "review_kind": "pending", "status": "pending", "reviewer": None,
        "recorded_at": None, "rationale": None, "provenance": None,
        "episode_key": None, "location_key": None,
        "occurrence_start": None, "occurrence_end": None,
        "origin_cluster": None, "incident_cluster": None,
        "duplicate_cluster": row.subject, "supersedes": None,
        "context_fingerprints": {
            r.observation_id: article_fingerprint(r)
            for r in (*view.observations, *view.evidence_history)
            if r.metric == "narrative.event_context"
            and r.payload.get("evidence_id") == row.observation_id
        },
    } for row in view.observations if row.metric == "narrative.event"]


def apply_article_review(store, review):
    """Adjudicated article metadata only. Disagreements remain external, unpromoted."""
    if review["status"] != "adjudicated" or review["review_kind"] not in {
        "human_declared", "agent_reviewed", "synthetic_authored"
    }:
        raise ValueError("explicit adjudication and review kind required")
    recorded = datetime.fromisoformat(review["recorded_at"])
    rows = store.view_at(recorded)
    evidence = next((r for r in (*rows.observations, *rows.evidence_history)
                     if r.observation_id == review["evidence_id"]), None)
    if evidence is None or article_fingerprint(evidence) != review["article_sha256"]:
        raise ValueError("review must bind the available immutable article version")
    context = {k: review.get(k) for k in (
        "episode_key", "location_key", "occurrence_start", "occurrence_end", "supersedes"
    )}
    for key in ("occurrence_start", "occurrence_end"):
        context[key] = datetime.fromisoformat(context[key]) if context[key] else None
    return record_event_context(
        store, evidence_id=review["evidence_id"], recorded_at=recorded,
        reviewer=review["reviewer"], rationale=review["rationale"],
        provenance=review["review_kind"] + ": " + review["provenance"], **context,
    )


def freeze_manifest(articles, labels, *, seed, frozen_at):
    """Union incident/origin/duplicate clusters BEFORE deterministic assignment.

    Unknown cluster identities block freezing; do not substitute article IDs for
    unknown origins. The whole publisher may conservatively share one origin.
    Corrections and syndication must share duplicate/origin keys with originals.
    """
    _require_aware("frozen_at", frozen_at)
    if not seed or not 1 <= len(articles) <= 4096:
        raise ValueError("seed and bounded articles required")
    ids = [a["evidence_id"] for a in articles]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate evidence ID")
    parents = {key: key for key in ids}

    def root(key):
        while parents[key] != key:
            key = parents[key]
        return key

    owners = {}
    for article in sorted(articles, key=lambda a: a["evidence_id"]):
        for field in ("incident_cluster", "origin_cluster", "duplicate_cluster"):
            value = article.get(field)
            if not value or value == "unknown":
                raise ValueError("unresolved cluster identity blocks freeze")
            token = (field, value)
            if token in owners:
                a, b = root(article["evidence_id"]), root(owners[token])
                parents[max(a, b)] = min(a, b)
            owners[token] = article["evidence_id"]
    components = sorted({root(key) for key in ids}, key=lambda key: digest([seed, key]))
    heldout_components = set(components[:max(1, (len(components) + 4) // 5)])
    assignment = {key: ("holdout" if root(key) in heldout_components else "development")
                  for key in sorted(ids)}
    for label in labels:
        pair = label["evidence_ids"]
        if len(pair) != 2 or any(key not in assignment for key in pair):
            raise ValueError("label references outside frozen corpus")
        if assignment[pair[0]] != assignment[pair[1]]:
            raise ValueError("pair spans splits; revise clusters BEFORE freezing")
        reviewed = datetime.fromisoformat(label["reviewed_at"])
        _require_aware("reviewed_at", reviewed)
        if reviewed > frozen_at:
            raise ValueError("labels must precede freeze")
        if not label.get("reviewer"):
            raise ValueError("pair reviewer required")
    from pathlib import Path

    matcher_hashes = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()
                                         .replace(b"\r\n", b"\n")).hexdigest()
                      for name in ("event_intelligence.py", "event_context.py")}
    body = {
        "version": "cluster-holdout-v1", "seed": seed,
        "frozen_at": frozen_at.isoformat(), "articles": sorted(articles, key=lambda a: a["evidence_id"]),
        "assignment": assignment, "label_sha256": digest(labels),
        "policy": "event-link-reviewed-context-v2", "tuning": "prohibited; retire after scoring",
        "matcher_sha256": matcher_hashes,
    }
    return body | {"sha256": digest(body)}


def score_frozen(store, manifest, labels, cutoffs):
    """Read-only scoring; no label, rationale or cluster assignment enters matching."""
    body = {k: v for k, v in manifest.items() if k != "sha256"}
    if digest(body) != manifest["sha256"] or digest(labels) != manifest["label_sha256"]:
        raise ValueError("frozen manifest/labels changed")
    rebuilt = freeze_manifest(manifest["articles"], labels, seed=manifest["seed"],
                              frozen_at=datetime.fromisoformat(manifest["frozen_at"]))
    if rebuilt != manifest:
        raise ValueError("invalid split manifest")
    reports = []
    for cutoff in cutoffs:
        view = store.view_at(cutoff)
        history = {r.observation_id: r for r in (*view.observations, *view.evidence_history)}
        for article in manifest["articles"]:
            row = history.get(article["evidence_id"])
            if row and article_fingerprint(row) != article["article_sha256"]:
                raise ValueError("article changed since freeze")
            for context in history.values():
                if (context.metric == "narrative.event_context"
                    and context.payload.get("evidence_id") == article["evidence_id"]
                    and article.get("context_fingerprints", {}).get(context.observation_id)
                    != article_fingerprint(context)):
                    raise ValueError("unfrozen context review; holdout cannot be tuned")
        heldout = [label for label in labels
                   if all(manifest["assignment"][key] == "holdout"
                          for key in label["evidence_ids"])]
        reports.append(evaluate(view, heldout))
    return {"manifest_sha256": manifest["sha256"], "reports": reports,
            "holdout_retired": True, "human_validation": "not established by this tool"}


def main(argv=None):
    """Offline packet/apply/freeze/score commands; labels never written to SQLite."""
    import argparse
    from pathlib import Path

    from tradingagents.information.store import SQLiteInformationStore

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("packet", "apply", "freeze", "score"))
    parser.add_argument("--store", type=Path)
    parser.add_argument("--articles", type=Path)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cutoff", action="append", default=[])
    parser.add_argument("--seed", default="phase36-v1")
    parser.add_argument("--frozen-at")
    args = parser.parse_args(argv)

    def read(path):
        if path is None or path.stat().st_size > 2_000_000:
            parser.error("required JSON file missing or larger than 2 MB")
        return json.loads(path.read_text(encoding="utf-8"))

    if args.action == "freeze":
        if not args.frozen_at:
            parser.error("freeze requires actual frozen-at acquisition timestamp")
        result = freeze_manifest(read(args.articles), read(args.labels), seed=args.seed,
                                 frozen_at=datetime.fromisoformat(args.frozen_at))
    else:
        if args.store is None or not args.store.is_file():
            parser.error("existing canonical store required")
        store = SQLiteInformationStore(args.store, read_only=args.action != "apply")
        if args.action == "apply":
            result = {"review_id": apply_article_review(store, read(args.articles)).observation_id}
        else:
            cutoffs = [datetime.fromisoformat(value) for value in args.cutoff]
            if not cutoffs:
                parser.error("at least one cutoff required")
            result = (review_packet(store.view_at(cutoffs[0])) if args.action == "packet"
                      else score_frozen(store, read(args.manifest), read(args.labels), cutoffs))
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
