"""Operational policy, bounded current retention and real-source PIT replay."""

import json
import sqlite3
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from tests.test_broad_news import T, rss, session_for
from tradingagents.information.news import poll_once
from tradingagents.information.store import SQLiteInformationStore
from tradingagents.information.world_radar import (
    ELIGIBLE_CONFIGS,
    PolicySession,
    coverage_metrics,
    replay_specimens,
    run,
)

FOLDER = Path(__file__).parent / "fixtures/phase37"


@pytest.mark.parametrize("robots,status,allowed", [
    ("User-agent: *\nDisallow: /rss", 200, False),
    ("User-agent: *\nAllow: /", 200, True),
    ("", 403, False), ("", 302, False), ("", 404, True),
    ("User-agent: *\nCrawl-delay: 2", 200, False),
])
def test_policy_exact_scope_robots_and_no_bypass(robots, status, allowed):
    config = ELIGIBLE_CONFIGS[2]
    session = session_for(robots)
    response = session.get.return_value.__enter__.return_value
    response.status_code = status
    policy = PolicySession(session, (config,))
    if allowed:
        policy.get(config.source.endpoint)
        assert session.get.call_count == 2
    else:
        with pytest.raises(requests.RequestException):
            policy.get(config.source.endpoint)
        assert session.get.call_count == 1  # never asks for disallowed feed
    with pytest.raises(requests.RequestException):
        policy.get("https://example.com/unreviewed")
    altered = replace(config, source=replace(config.source, endpoint="https://example.com/rss"))
    with pytest.raises(ValueError, match="unreviewed"):
        PolicySession(session, (altered,))


def test_robots_unavailable_is_recorded_failure_and_job_resume_is_quiet(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    session = MagicMock()
    session.get.side_effect = requests.Timeout()
    first = run(store, session=session, now=T, clock=lambda: T)
    assert first["polls"] and all(p["outcome"] == "failure" for p in first["polls"])
    assert not store.view_at(T).observations
    assert all(not p["allowed"] for p in first["robots"].values())
    second_session = MagicMock()
    # Other sources on already-attempted hosts are also cooled down.
    second = run(store, session=second_session, now=T, clock=lambda: T)
    assert not second["polls"]
    second_session.get.assert_not_called()


def test_current_eligible_retention_precedes_old_hash_order_and_future(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    config = ELIGIBLE_CONFIGS[0]
    def item(title, pub):
        return rss(title, url=config.source.endpoint + "?" + title, pub=pub).split("<channel>")[1].split("</channel>")[0]
    text = "<rss><channel>" + "".join([
        item("old", "Mon, 01 Jan 2024 00:00:00 GMT"),
        item("current", "Thu, 08 Jan 2026 12:00:00 GMT"),
        item("future", "Thu, 08 Jan 2027 12:00:00 GMT"),
    ]) + "</channel></rss>"
    outcomes = poll_once(store, (config,), poll_id="bounded-current", observation_limit=1,
                         session=session_for(text), clock=lambda: T)
    assert store.view_at(T).observations[0].payload["claim"] == "current"
    assert json.loads(outcomes[0].detail)["omitted_by_slice_limit"] == 2


def test_real_sources_replay_freshness_no_future_and_conservative_origins(tmp_path):
    data = json.loads((FOLDER / "real_specimens.json").read_text(encoding="utf-8"))
    cutoff = datetime.fromisoformat(data["cutoff"])
    earliest = min(datetime.fromisoformat(s["retrieved_at"]) for s in data["specimens"])
    store = SQLiteInformationStore(tmp_path / "canonical.db")
    replay_specimens(store, data["specimens"])
    assert not store.view_at(earliest - timedelta(microseconds=1)).observations
    late = store.view_at(cutoff)
    metrics = coverage_metrics(late)
    assert len(metrics["fresh_families"]) >= 3
    assert set(metrics["fresh_publisher_groups"]) == {"NASA", "U.S. Geological Survey", "UK Government"}
    assert metrics["human_reviews"] == 0
    assert all(r.payload["independent_confirmation"] == "unknown" for r in late.observations)
    assert all(r.payload["event_occurrence_time"] is None for r in late.observations)
    assert any(r.publication_time is None and r.effective_time for r in late.observations)
    assert metrics == coverage_metrics(SQLiteInformationStore(store.path, read_only=True).view_at(cutoff))
    # Repeated copies retain immutable history without inflating unique-article counts.
    replay_specimens(store, data["specimens"])
    assert metrics == coverage_metrics(store.view_at(cutoff))
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("pragma integrity_check").fetchone()[0] == "ok"
    pairs = json.loads((FOLDER / "pairs_unreviewed.json").read_text(encoding="utf-8"))
    assert all(p["label"] == "unknown" and p["review_status"] == "pending" for p in pairs)
    assert all(len(set(p["evidence_ids"])) == 2 for p in pairs)
    assert {p["suggested_pair_identity"] for p in pairs} >= {
        "plausible_same_incident", "plausible_distinct_incidents"}
