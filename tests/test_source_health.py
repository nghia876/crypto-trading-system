"""Operational journal tests are deterministic mocks, not live latency evidence."""

import json
from datetime import timedelta

import pytest
import requests

from tests.test_broad_news import T, rss, session_for
from tradingagents.information.news import poll_once
from tradingagents.information.polling import coordinate
from tradingagents.information.source_health import health_report, main
from tradingagents.information.sources import OPERATIONAL_REPAIR_CONFIG, SPECIALIST_WORLD_CONFIG
from tradingagents.information.store import SQLiteInformationStore

C = SPECIALIST_WORLD_CONFIG[0]


def report(store, at=T):
    return health_report(store, (C,), cutoff=at)["sources"][0]


def test_multi_poll_restart_duplicate_and_first_seen(tmp_path):
    path = tmp_path / "canonical.sqlite3"
    store = SQLiteInformationStore(path)
    text = rss(url="https://water.usgs.gov/test")
    poll_once(store, (C,), poll_id="one", session=session_for(text), clock=lambda: T)
    later = T + timedelta(hours=3)
    reopened = SQLiteInformationStore(path)
    poll_once(reopened, (C,), poll_id="two", session=session_for(text), clock=lambda: later)
    session = session_for(error=AssertionError("must not fetch"))
    poll_once(reopened, (C,), poll_id="two", session=session, clock=lambda: later)
    session.get.assert_not_called()
    row = report(reopened, later)
    assert row["attempts"] == 2 and row["unique_articles"] == 1
    assert row["outcomes"] == {"success": 2}
    assert row["first_seen_minus_publication"]["max_seconds"] == 7200
    assert row["latest_retrieval_minus_first_seen"]["max_seconds"] == 10800
    assert row["closed_unknown_intervals"][0]["seconds"] == 9900
    assert report(reopened)["attempts"] == 1
    assert report(reopened, later + timedelta(days=2))["collection_unobserved"]
    assert report(reopened, later + timedelta(days=2))["content"] == "stale_publication"


@pytest.mark.parametrize("mode,transport", [("stale", "responding"), ("empty", "empty"),
                                          ("timeout", "failed"), ("rate_limit", "failed")])
def test_stale_empty_failed_and_rate_limit(tmp_path, mode, transport):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    if mode == "timeout":
        session = session_for(error=requests.Timeout())
    elif mode == "rate_limit":
        response = requests.Response()
        response.status_code = 429
        response.headers["Retry-After"] = "3600"
        session = session_for(error=requests.HTTPError(response=response))
    else:
        text = "<rss><channel/></rss>" if mode == "empty" else rss(
            url="https://water.usgs.gov/test", pub="Thu, 01 Jan 2026 10:00:00 GMT")
        session = session_for(text)
    coordinate(store, (C,), now=T, clock=lambda: T, session=session)
    result = report(store)
    assert result["transport"] == transport
    assert result["timeout_count"] == (mode == "timeout")
    assert result["rate_limit_count"] == (mode == "rate_limit")
    if mode == "stale":
        assert result["content"] == "stale_publication"
        assert result["last_success"] == T.isoformat()
    before = result["attempts"]
    session = session_for(error=AssertionError("cadence/backoff must survive restart"))
    coordinate(SQLiteInformationStore(store.path), (C,), now=T+timedelta(seconds=10),
               clock=lambda: T+timedelta(seconds=10), session=session)
    session.get.assert_not_called()
    assert report(store, T+timedelta(seconds=10))["attempts"] == before


def test_recovery_does_not_erase_failure_or_unknown_gap(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    poll_once(store, (C,), poll_id="failed", session=session_for(error=requests.Timeout()), clock=lambda: T)
    later = T+timedelta(days=2)
    poll_once(store, (C,), poll_id="recovered", session=session_for("<rss><channel/></rss>"), clock=lambda: later)
    result = report(store, later)
    assert result["transport"] == "empty" and result["timeout_count"] == 1
    assert len(result["closed_unknown_intervals"]) == 1
    assert not result["collection_unobserved"]
    assert report(store)["transport"] == "failed"


def test_totals_survive_more_than_twelve_poll_checkpoint_window(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    for index in range(15):
        at = T+timedelta(minutes=15*index)
        poll_once(store, (C,), poll_id=f"poll-{index}",
                  session=session_for("<rss><channel/></rss>"), clock=lambda at=at: at)
    assert report(SQLiteInformationStore(store.path), at)["attempts"] == 15
    assert report(store)["attempts"] == 1


def test_never_polled_cutoff_clocks_and_rights(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    result = report(store)
    assert result["baseline_unknown"] and result["collection_unobserved"]
    assert result["publication_age_seconds"] is None
    with pytest.raises(ValueError):
        report(store, T.replace(tzinfo=None))
    with pytest.raises(ValueError):
        health_report(store, (C,), cutoff=T, interval=0)
    assert result["rights_reference"].startswith("https://")
    assert "UNKNOWN" in result["origin_independence"]


def test_future_publication_is_not_negative_latency_or_freshness(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    poll_once(store, (C,), poll_id="future", session=session_for(rss(
        url="https://water.usgs.gov/test", pub="Fri, 09 Jan 2027 10:00:00 GMT")), clock=lambda: T)
    assert report(store)["first_seen_minus_publication"]["count"] == 0
    assert report(store)["publication_age_seconds"] is None


def test_clock_rollback_stops_commit_and_naive_clock_stops_request(tmp_path):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    times = iter([T, T-timedelta(seconds=1)])
    with pytest.raises(ValueError, match="backwards"):
        poll_once(store, (C,), poll_id="rollback", session=session_for("<rss><channel/></rss>"),
                  clock=lambda: next(times))
    assert report(store)["attempts"] == 0
    session = session_for(error=AssertionError("must validate clock before request"))
    with pytest.raises(ValueError, match="aware"):
        poll_once(store, (C,), poll_id="naive", session=session, clock=lambda: T.replace(tzinfo=None))
    session.get.assert_not_called()


def test_uk_departments_not_independent_and_cli_is_readonly(tmp_path, capsys):
    store = SQLiteInformationStore(tmp_path / "canonical.sqlite3")
    health = health_report(store, OPERATIONAL_REPAIR_CONFIG, cutoff=T)
    assert {r["publisher_group"] for r in health["sources"]} == {"UK Government"}
    assert all(not c.source.asset_scope and not c.query for c in OPERATIONAL_REPAIR_CONFIG)
    before = (tmp_path / "canonical.sqlite3").read_bytes()
    assert main(["--store", str(store.path), "--as-of", T.isoformat()]) == 0
    assert json.loads(capsys.readouterr().out)["cutoff"] == T.isoformat()
    assert (tmp_path / "canonical.sqlite3").read_bytes() == before
