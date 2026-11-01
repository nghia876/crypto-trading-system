"""Offline event-link evaluation; labels never enter candidates or SQLite."""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from tradingagents.information.event_intelligence import suggest_event_links


def evaluate(view, labels):
    """Score available labeled pairs only, with explicit unknowns and omissions."""
    if len(labels) > 4096:
        raise ValueError("maximum 4096 labels")
    seen = set()
    for item in labels:
        pair = tuple(sorted(item["evidence_ids"]))
        if len(pair) != 2 or pair[0] == pair[1] or pair in seen:
            raise ValueError("unique distinct pairs required")
        seen.add(pair)
        if item["label"] not in {"same_event", "different_event", "unknown"}:
            raise ValueError("invalid identity label")
        if item["review_status"] not in {
            "synthetic_authored", "agent_reviewed", "human_reviewed", "pending", "disputed"
        }:
            raise ValueError("invalid review status")
        if item["confidence"] not in {"high", "medium", "low", "unknown"}:
            raise ValueError("invalid confidence")
        if item["reporting_relationship"] not in {
            "cross_source",
            "same_publisher_syndication",
            "unknown",
        }:
            raise ValueError("invalid reporting relationship")
        if not all(item.get(k) for k in ("provenance", "rationale", "family", "stratum")):
            raise ValueError("provenance, rationale, family and stratum required")
    result = suggest_event_links(view)
    predicted = {tuple(sorted(c["evidence_ids"])) for c in result["candidates"]}
    available = {r.observation_id for r in view.observations}
    groups = defaultdict(lambda: {"tp": 0, "fp": 0, "tn": 0, "fn": 0})
    details = []
    for item in labels:
        pair = tuple(sorted(item["evidence_ids"]))
        if not set(pair) <= available:
            outcome = "unavailable"
        elif item["label"] == "unknown" or item["review_status"] in {"pending", "disputed"}:
            outcome = "unknown"
        else:
            positive = item["label"] == "same_event"
            outcome = (
                ("tp" if positive else "fp") if pair in predicted else ("fn" if positive else "tn")
            )
            for group in (
                "overall",
                "family:" + item["family"],
                "stratum:" + item["stratum"],
                "reporting:" + item["reporting_relationship"],
                "review:" + item["review_status"],
            ):
                groups[group][outcome] += 1
        details.append({"evidence_ids": list(pair), "outcome": outcome})
    return {
        "policy": result["policy"],
        "cutoff": result["cutoff"],
        "metrics": summarize(groups),
        "pairs": details,
        "omitted_records": result["omitted_records"],
        "omitted_candidates": result["omitted_candidates"],
        "unlabeled_predictions": len(predicted - seen),
    }


def summarize(groups):
    output = {}
    for key, counts in sorted(groups.items()):
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        output[key] = dict(counts) | {
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
        }
    return output


def run_fixture(path):
    """Isolated retrieval trials in temporary canonical SQLite stores; no live DB."""
    from datetime import datetime
    from tempfile import TemporaryDirectory

    from tradingagents.information.binance_spot import MarketDataBatch
    from tradingagents.information.observations import Observation
    from tradingagents.information.store import SQLiteInformationStore

    if Path(path).stat().st_size > 2_000_000:
        raise ValueError("fixture exceeds 2 MB")
    raw = Path(path).read_bytes()
    fixture = json.loads(raw)
    if not 1 <= len(fixture["cases"]) <= 256:
        raise ValueError("one to 256 trials required")
    totals = defaultdict(lambda: {"tp": 0, "fp": 0, "tn": 0, "fn": 0})
    details = []
    with TemporaryDirectory(prefix="event-evaluation-") as temp:
        for index, case in enumerate(fixture["cases"]):
            if len(case["records"]) != 2:
                raise ValueError("exactly two records per isolated trial")
            store = SQLiteInformationStore(Path(temp) / f"{index}.sqlite3")
            rows = []
            for item in case["records"]:
                known = datetime.fromisoformat(item["available_at"])
                rows.append(
                    Observation(
                        item["id"],
                        item["source"],
                        item["id"],
                        "narrative.event",
                        {
                            "claim": item["title"],
                            "domain": case["family"],
                            "publisher_group": item["publisher"],
                        },
                        known,
                        known,
                        known,
                        publication_time=datetime.fromisoformat(item["published_at"]),
                        raw_reference="https://example.invalid/" + item["id"],
                        schema_version="narrative-news-v1",
                        unit="event_record",
                    )
                )
            store.append(MarketDataBatch(tuple(rows), (), max(r.retrieved_at for r in rows)))
            cutoff = datetime.fromisoformat(case["cutoff"])
            label = {k: v for k, v in case.items() if k not in {"records", "id", "cutoff"}}
            label["evidence_ids"] = [r.observation_id for r in rows]
            result = evaluate(store.view_at(cutoff), [label])
            if result != evaluate(SQLiteInformationStore(store.path).view_at(cutoff), [label]):
                raise AssertionError("reopen replay mismatch")
            for group, counts in result["metrics"].items():
                for key in ("tp", "fp", "tn", "fn"):
                    totals[group][key] += counts[key]
            details.append({"id": case["id"], "outcome": result["pairs"][0]["outcome"]})
    return {
        "dataset": fixture["provenance"],
        "sha256": hashlib.sha256(raw).hexdigest(),
        "protocol": "isolated_pair_trials; not corpus-wide recall",
        "policy": result["policy"],
        "metrics": summarize(totals),
        "cases": details,
    }


def main(argv=None):
    """Evaluate labels against an existing store without appending evidence."""
    from datetime import datetime

    from tradingagents.information.store import SQLiteInformationStore

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--store", type=Path)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--cutoff")
    args = parser.parse_args(argv)
    if args.fixture:
        if args.store or args.labels or args.cutoff:
            parser.error("fixture mode cannot access a live store")
        print(json.dumps(run_fixture(args.fixture), sort_keys=True, indent=2))
        return
    if not all((args.store, args.labels, args.cutoff)):
        parser.error("store, labels and cutoff required")
    if not args.store.is_file():
        parser.error("existing canonical store required")
    if args.labels.stat().st_size > 2_000_000:
        parser.error("labels exceed 2 MB")
    raw = args.labels.read_bytes()
    labels = json.loads(raw)
    result = evaluate(
        SQLiteInformationStore(args.store, read_only=True).view_at(
            datetime.fromisoformat(args.cutoff)
        ),
        labels,
    )
    result["label_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
