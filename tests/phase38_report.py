"""Archive finite operational runs and normalized fields; no human labels/scoring."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from tradingagents.information.source_health import health_report
from tradingagents.information.store import SQLiteInformationStore
from tradingagents.information.world_radar import ELIGIBLE_CONFIGS, coverage_metrics


def main():
    root = Path(__file__).resolve().parents[2]
    runs = [json.loads((root / f"phase38-live-{i}.json").read_text(encoding="utf-8"))
            for i in range(1, 5)]
    cutoff = max(datetime.fromisoformat(r["cutoff"]) for r in runs)
    store = SQLiteInformationStore(root / "canonical-information.sqlite3", read_only=True)
    folder = Path(__file__).parent / "fixtures/phase38"
    folder.mkdir(exist_ok=False)
    latest = {}
    for run in runs:
        for row in run["specimens"]:
            latest[(row["source_id"], row["url"])] = row
    specimens = list(latest.values())
    with sqlite3.connect(f"file:{store.path}?mode=ro", uri=True) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    report = {
        "cutoff": cutoff.isoformat(), "sqlite_integrity": integrity,
        "runs": [{k: run[k] for k in ("cutoff", "polls", "robots", "rights_scope")} for run in runs],
        "metrics": coverage_metrics(store.view_at(cutoff)),
        "health": health_report(store, ELIGIBLE_CONFIGS, cutoff=cutoff),
        "policy_checks": json.loads((root / "phase38-policy-checks.json").read_text(encoding="utf-8")),
        "human_reviews": 0,
    }
    for name, data in (("real_specimens.json", {"cutoff": cutoff.isoformat(), "specimens": specimens}),
                       ("operational_results.json", report)):
        (folder / name).write_text(json.dumps(data, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps({"cutoff": cutoff.isoformat(), "unique_acquired_source_urls": len(specimens),
                      "attempts": sum(len(r["polls"]) for r in runs), "integrity": integrity}))


if __name__ == "__main__":
    main()
