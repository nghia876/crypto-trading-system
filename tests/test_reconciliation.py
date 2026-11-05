"""Reconciliation failures must preserve every baseline row and both inputs."""
import hashlib
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.observations import Observation
from tradingagents.information.reconciliation import (
    ReconciliationConflict,
    build_candidate,
    merge_transaction,
    read_rows,
)
from tradingagents.information.sources import Source
from tradingagents.information.store import SQLiteInformationStore

NOW = datetime(2026, 10, 29, tzinfo=UTC)
SOURCE = Source("test", "fixture", "Fixture", "https://example.test", "offline")


def seed(path, identity="a"):
    store = SQLiteInformationStore(path)
    obs = Observation(identity, "test", "subject", "metric", {"value": 1}, NOW, NOW, NOW)
    store.append(MarketDataBatch((obs,), (), NOW, source_definitions=(SOURCE,)))
    return path


@pytest.mark.parametrize("failure", ["observation", "coverage", "source", "source_version",
                                     "dangling", "wrong_subject", "cycle", "fork"])
def test_collision_or_lineage_rejects_and_rolls_back(tmp_path, failure):
    path = seed(tmp_path / "baseline.db")
    with sqlite3.connect(path) as db:
        baseline = read_rows(db)
        incoming = {t: [] for t in baseline}
        # Sort before the conflict to ensure real insertion precedes failure.
        row = list(baseline["observations"][0])
        row[0] = "0-new"
        incoming["observations"].append(tuple(row))
        if failure == "observation":
            row = list(baseline["observations"][0])
            row[10] = '{"value":2}'
            incoming["observations"].append(tuple(row))
        elif failure.startswith("source"):
            row = list(baseline["source_definitions"][0])
            row[3] = row[3].replace('"Fixture"', '"Changed"')
            if failure == "source_version":
                row[2] = (NOW + timedelta(days=1)).isoformat()
            incoming["source_definitions"].append(tuple(row))
        elif failure == "coverage":
            coverage = ("same", "test", "subject", "metric", NOW.isoformat(), "present", "", "[]")
            db.execute("INSERT INTO coverage VALUES (?,?,?,?,?,?,?,?)", coverage)
            db.commit()
            baseline = read_rows(db)
            incoming["coverage"] = [(*coverage[:6], "changed", "[]")]
        else:
            incoming["observations"] = []
            row[15] = "missing" if failure == "dangling" else "a"
            if failure == "wrong_subject":
                row[2] = "wrong"
            if failure == "cycle":
                row[15] = row[0]
            incoming["observations"].append(tuple(row))
            if failure == "fork":
                row[0] = "another-child"
                incoming["observations"].append(tuple(row))
        with pytest.raises(ReconciliationConflict):
            merge_transaction(db, incoming)
        assert read_rows(db) == baseline


def test_exact_union_reopen_and_no_overwrite(tmp_path):
    first, second = seed(tmp_path / "first.db"), seed(tmp_path / "second.db", "b")
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (first, second)]
    candidate = tmp_path / "DISPOSABLE.db"
    result = build_candidate(first, second, candidate)
    assert result["validation"]["counts"]["observations"] == 2
    assert result["tables"]["source_definitions"]["identical_shared_keys"] == 1
    with pytest.raises(FileExistsError):
        build_candidate(first, second, candidate)
    with sqlite3.connect(candidate) as db:
        rows = read_rows(db)
        assert merge_transaction(db, rows)["tables"]["observations"]["identical_shared_keys"] == 2
    assert len(SQLiteInformationStore(candidate, read_only=True).view_at(NOW).evidence_history) == 2
    assert before == [hashlib.sha256(p.read_bytes()).hexdigest() for p in (first, second)]


def test_conflicting_content_version_rejected(tmp_path):
    from tests.test_broad_news import rss
    from tradingagents.information.news import parse_news_snapshot
    from tradingagents.information.sources import SPECIALIST_WORLD_CONFIG

    path = tmp_path / "news.db"
    store = SQLiteInformationStore(path)
    config = SPECIALIST_WORLD_CONFIG[0]
    store.append(parse_news_snapshot(rss(url=config.source.endpoint), config, retrieved_at=NOW))
    with sqlite3.connect(path) as db:
        baseline = read_rows(db)
        assert baseline["observations"]
        row = list(baseline["observations"][0])
        import json
        payload = json.loads(row[10])
        payload["claim"] = "Different content retaining the same version ID"
        row[10] = json.dumps(payload)
        row[0] = "conflicting-version"
        incoming = {t: [] for t in baseline}
        incoming["observations"] = [tuple(row)]
        with pytest.raises(ReconciliationConflict, match="content version"):
            merge_transaction(db, incoming)
        assert read_rows(db) == baseline
