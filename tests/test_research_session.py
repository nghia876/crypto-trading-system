"""Isolated multi-session persistence and attention tests; no live operation claim."""

import sqlite3
from datetime import timedelta

import pytest

from tests.test_adaptive_discovery import feed_session
from tests.test_broad_news import T
from tradingagents.information.narrative_attention import sampled_attention
from tradingagents.information.research_session import collect
from tradingagents.information.store import SQLiteInformationStore


def test_restart_append_backup_pit_and_repeat_polls(tmp_path):
    path = tmp_path / 'isolated.sqlite'
    SQLiteInformationStore(path)
    session = feed_session()
    first = collect(path, tmp_path / 'before1.sqlite', run_id='one', session=session,
                    now=T, clock=lambda: T)
    before = SQLiteInformationStore(path, read_only=True).view_at(T)
    assert first['functioning_publishers_this_run'] == ['Global Voices', 'Inter Press Service']
    later = T + timedelta(days=1)
    collect(path, tmp_path / 'before2.sqlite', run_id='two', session=feed_session(),
            now=later, clock=lambda: later)
    reopened = SQLiteInformationStore(path, read_only=True)
    after = reopened.view_at(later)
    a, b = sampled_attention(before), sampled_attention(after)
    assert a['unique_articles'] == b['unique_articles'] == 3
    assert b['retained_versions'] > a['retained_versions']
    assert b['current_articles'] == 0 and b['previous_articles'] == 3
    assert {r.first_seen_time for r in after.observations} == {T}
    assert len(reopened.view_at(T).observations) == len(before.observations)
    assert not reopened.view_at(T-timedelta(seconds=1)).observations
    assert len([c for c in after.coverage if c.metric == 'discovery.run']) == 2
    assert any('offline' in u for u in first['unknowns'])
    assert sampled_attention(before)['corroboration'] == 'NOT_ASSESSED'
    with sqlite3.connect(tmp_path / 'before2.sqlite') as conn:
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    restored = SQLiteInformationStore(tmp_path / 'before2.sqlite', read_only=True).view_at(later)
    assert len(restored.evidence_history) == len(before.evidence_history)
    calls = session.get.call_count
    with pytest.raises(ValueError):
        collect(path, tmp_path / 'before1.sqlite', run_id='three', session=session)
    assert session.get.call_count == calls


def test_bridge_refuses_new_database(tmp_path):
    with pytest.raises(ValueError):
        collect(tmp_path / 'missing.sqlite', tmp_path / 'backup.sqlite',
                run_id='no', session=feed_session())
    assert not (tmp_path / 'missing.sqlite').exists()
