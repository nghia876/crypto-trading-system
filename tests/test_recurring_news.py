"""Recurring jobs retain the existing acquisition, store, replay and graph contracts."""

import json
from datetime import timedelta

import pytest
import requests

from tests.test_broad_news import G_TECH, TECH, WAR, T, atom, rss, session_for
from tradingagents.information.polling import coordinate, job_lock
from tradingagents.information.sources import BROAD_NEWS_CONFIG
from tradingagents.information.store import SQLiteInformationStore


def run(store, configs=(WAR,), at=T, session=None, **kwargs):
    return coordinate(
        store, configs, now=at, clock=lambda: at, session=session or session_for(rss()), **kwargs
    )


def test_restart_repeat_no_duplicate_and_due(tmp_path):
    path = tmp_path / "e.db"
    store = SQLiteInformationStore(path)
    session = session_for(rss())
    first, _ = run(store, session=session)
    before = store.view_at(T)
    repeated, _ = run(SQLiteInformationStore(path), at=T + timedelta(seconds=30), session=session)
    assert first and not repeated and session.get.call_count == 1
    assert store.view_at(T).evidence_history == before.evidence_history
    later = T + timedelta(minutes=15)
    run(store, at=later, session=session)
    assert session.get.call_count == 2
    rows = store.view_at(later).evidence_history
    assert len(rows) == 2 and len({r.payload["version_id"] for r in rows}) == 1
    assert all(r.first_seen_time == T for r in rows)
    assert len(store.view_at(T - timedelta(microseconds=1)).observations) == 0


def test_partial_crash_recovery(tmp_path, monkeypatch):
    import tradingagents.information.polling as module

    store = SQLiteInformationStore(tmp_path / "e.db")
    original = module.poll_once
    calls = []

    def crash(store, configs, **kwargs):
        calls.append(configs[0])
        if len(calls) == 2:
            raise RuntimeError("process stopped")
        kwargs["session"] = session_for(
            '{"articles":[{"title":"Science breakthrough","url":"https://example.org/science"}]}'
        )
        return original(store, configs, **kwargs)

    monkeypatch.setattr(module, "poll_once", crash)
    with pytest.raises(RuntimeError):
        run(store, (WAR, G_TECH), session=session_for(rss()))
    monkeypatch.setattr(module, "poll_once", original)
    session = session_for(rss())
    outcomes, _ = run(SQLiteInformationStore(tmp_path / "e.db"), (WAR, G_TECH), session=session)
    assert len(outcomes) == session.get.call_count == 1
    assert len(store.view_at(T).evidence_history) == 2


def test_empty_error_backoff_and_late_gap(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    outcomes, health = run(store, session=session_for("<rss><channel/></rss>"))
    assert json.loads(outcomes[0].detail)["outcome"] == "empty"
    assert json.loads(health[0].detail)["stale"]
    at = T + timedelta(minutes=15)
    outcomes, health = run(store, at=at, session=session_for(error=requests.ConnectionError()))
    assert json.loads(outcomes[0].detail)["outcome"] == "failure"
    assert json.loads(health[0].detail)["consecutive_failures"] == 1
    assert not run(store, at=at + timedelta(minutes=15))[0]
    outcomes, health = run(store, at=T + timedelta(days=2))
    detail = json.loads(health[0].detail)
    assert detail["late"] and detail["rolling_window_gap"] and detail["content_stale"]


def test_rate_limit_honored_across_same_host(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    response = requests.Response()
    response.status_code = 429
    response.headers["Retry-After"] = "7200"
    error = requests.HTTPError(response=response)
    run(store, session=session_for(error=error))
    session = session_for(rss())
    assert not run(store, (WAR, TECH), at=T + timedelta(minutes=30), session=session)[0]
    assert session.get.call_count == 0
    assert run(store, at=T + timedelta(hours=2), session=session)[0]


def test_domains_and_hosts_fair_bounded_and_ungated(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    # RSS and GDELT both legitimately return empty; acquisition is still unconditional.
    session = session_for("<rss><channel/></rss>")
    outcomes, health = run(store, BROAD_NEWS_CONFIG, session=session, max_sources=2)
    assert len(outcomes) == 2
    assert {r.subject for r in outcomes} == {"WAR_GEOPOLITICS", "TECHNOLOGY"}
    assert sum(json.loads(r.detail)["budget_deferred"] for r in health) == 2
    assert len({r.source_id.split(".")[1] for r in outcomes}) == 2
    next_outcomes, _ = run(
        store, BROAD_NEWS_CONFIG, at=T + timedelta(seconds=60), session=session, max_sources=2
    )
    assert len(next_outcomes) == 2
    assert {r.source_id for r in outcomes}.isdisjoint({r.source_id for r in next_outcomes})


def test_correction_and_non_btc_replay(tmp_path):
    from dataclasses import replace

    store = SQLiteInformationStore(tmp_path / "e.db")
    tech = replace(TECH, format="atom")
    run(store, (tech,), session=session_for(atom("Quantum laboratory reports breakthrough")))
    later = T + timedelta(minutes=15)
    run(
        store,
        (tech,),
        at=later,
        session=session_for(atom("Laboratory corrects measurement", updated=later.isoformat())),
    )
    assert store.view_at(T).observations[0].payload["claim"].startswith("Quantum")
    assert store.view_at(later).observations[0].payload["claim"].startswith("Laboratory")
    assert len(store.view_at(later).evidence_history) == 2


def test_os_lock_release_and_overlap(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    with job_lock(store), pytest.raises(OSError), job_lock(store):
        pass
    with job_lock(store):
        pass


@pytest.mark.parametrize("interval,budget", [(0, 4), (900, 1), (900, 17)])
def test_invalid_bounds(tmp_path, interval, budget):
    with pytest.raises(ValueError):
        run(SQLiteInformationStore(tmp_path / "e.db"), interval=interval, max_sources=budget)


def test_checkpoint_exact_cutoff_and_bounded_history(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    for index in range(20):
        at = T + timedelta(minutes=15 * index)
        run(store, at=at)
    at = T + timedelta(minutes=15 * 19)
    assert len(store.polling_history(WAR.fingerprint, at)) == 12
    assert (
        max(
            r.observed_at
            for r in store.polling_history(WAR.fingerprint, at - timedelta(microseconds=1))
        )
        < at
    )
    latest = store.polling_history(WAR.fingerprint, at)[0]
    assert not store.evidence_by_ids(latest.evidence_ids, at - timedelta(microseconds=1))
    assert store.evidence_by_ids(latest.evidence_ids, at)


@pytest.mark.parametrize("retry", ["Fri, 09 Jan 2026 14:00:00 GMT", "nan", "invalid", "1e300"])
def test_retry_after_edge_cases(tmp_path, retry):
    store = SQLiteInformationStore(tmp_path / "e.db")
    response = requests.Response()
    response.status_code = 429
    response.headers["Retry-After"] = retry
    outcomes, health = run(store, session=session_for(error=requests.HTTPError(response=response)))
    detail = json.loads(outcomes[0].detail)
    if retry.startswith("Fri"):
        assert detail["retry_after_seconds"] == 7200
    elif retry in {"nan", "invalid"}:
        assert detail["retry_after_seconds"] is None
    assert json.loads(health[0].detail)["consecutive_failures"] == 1


def test_recurring_consumer_budget_claims_and_replay(tmp_path):
    from tradingagents.information.claim_lifecycle import record_claim_assertion
    from tradingagents.information.consumer import (
        build_analysis_information,
        render_analysis_information,
    )

    store = SQLiteInformationStore(tmp_path / "e.db")
    run(store)
    row = store.view_at(T).observations[0]
    record_claim_assertion(
        store,
        claim_id=row.subject,
        kind="support",
        evidence_ids=(row.observation_id,),
        recorded_at=T,
        rationale="Curated report; no independence inferred",
    )
    rendered = render_analysis_information(build_analysis_information(store, T))
    assert "Ceasefire talks resume" in rendered and row.observation_id in rendered
    assert len(rendered) <= 28000
    assert "Ceasefire talks resume" not in render_analysis_information(
        build_analysis_information(store, T - timedelta(microseconds=1))
    )


def test_repeated_failure_backoff_recovers(tmp_path):
    store = SQLiteInformationStore(tmp_path / "e.db")
    error_session = session_for(error=requests.ConnectionError())
    run(store, session=error_session)
    second = T + timedelta(minutes=30)
    _, health = run(store, at=second, session=error_session)
    assert json.loads(health[0].detail)["consecutive_failures"] == 2
    assert not run(store, at=second + timedelta(minutes=30))[0]
    recovered = second + timedelta(minutes=60)
    _, health = run(store, at=recovered)
    assert json.loads(health[0].detail)["consecutive_failures"] == 0
    assert (
        json.loads(health[0].detail)["next_due"] == (recovered + timedelta(minutes=15)).isoformat()
    )


def test_stream_elapsed_budget_persisted_as_failure(tmp_path, monkeypatch):
    from tradingagents.information import news

    ticks = iter((0, 21))
    monkeypatch.setattr(news.time, "monotonic", lambda: next(ticks))
    outcomes, _ = run(SQLiteInformationStore(tmp_path / "e.db"))
    detail = json.loads(outcomes[0].detail)
    assert detail["outcome"] == "failure" and detail["error"] == "MarketDataCollectionError"
