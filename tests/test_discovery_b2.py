"""B2 contracts and observed-metadata replay; offline, no live claims from mocks."""

import json
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

from tests.test_adaptive_discovery import feed_session
from tests.test_broad_news import T, rss
from tests.test_graph_end_to_end import offline  # noqa: F401
from tradingagents.information.adaptive_discovery import _run_key, import_search, research
from tradingagents.information.binance_spot import CoverageRecord, CoverageStatus, MarketDataBatch
from tradingagents.information.discovery_sources import DISCOVERY_CONFIGS, RELATED_CONFIGS
from tradingagents.information.narrative_events import (
    render_narrative_events,
    selected_narrative_events,
)
from tradingagents.information.news import parse_news_snapshot
from tradingagents.information.store import SQLiteInformationStore


def test_open_topic_independent_of_feed_results_and_candidate_gate(tmp_path):
    store = SQLiteInformationStore(tmp_path / 'test.db')
    session = feed_session()
    report = research(store, run_id='open', now=T, clock=lambda: T, session=session,
                      open_queries=['obscure reservoir Laos'])
    query = report['open_queries'][0]
    assert not query['input_evidence_ids'] and query['status'] == 'pending'
    doc = {'run_id': 'open', 'query_id': query['query_id'], 'query': query['query'],
               'observed_at': T.isoformat(), 'method': 'human_manual', 'operator': 'test',
               'status': 'empty', 'results': [], 'channels_covered': ['manual web search'],
               'channels_missed': ['non-English unobserved'],
               'candidate_sources': ['https://new.example/feed/']}
    later = T+timedelta(seconds=1)
    receipt = import_search(store, doc, imported_at=later)
    assert receipt['fanout'] == 1 and receipt['origin'] == 'operator_open_topic'
    assert receipt['available_at'] == later.isoformat()
    assert receipt['candidate_approval_status'].startswith('PENDING')
    assert not any(r.source_id == 'new.example' for r in store.view_at(later).observations)
    assert not any(c.metric == 'discovery.query' for c in store.view_at(T).coverage)
    assert import_search(store, doc, imported_at=later+timedelta(seconds=1)) == receipt
    with pytest.raises(ValueError, match='different open queries'):
        research(store, run_id='open', session=session, open_queries=['changed'])
    with pytest.raises(ValueError, match='unreviewed publisher'):
        import_search(store, dict(doc, status='success', results=[{
            'source_id': 'new.example', 'title': 'Unauthorized', 'url': 'https://new.example/story'}]),
            imported_at=later)
    assert 'Manual external search receipts=1' in '\n'.join(render_narrative_events(store.view_at(later)))


@pytest.mark.parametrize('queries', [[''] , ['x'*257], ['a']*5, [None]])
def test_open_query_limits_before_requests(tmp_path, queries):
    session = feed_session()
    with pytest.raises(ValueError):
        research(SQLiteInformationStore(tmp_path / 'test.db'), run_id='bad', session=session,
                 open_queries=queries)
    session.get.assert_not_called()


@pytest.mark.parametrize('changes', [
    {'channels_covered': []}, {'candidate_sources': ['https://user:secret@host/story']},
    {'candidate_sources': ['file:///private']}, {'candidate_sources': ['https://x']*9},
    {'channels_missed': ['x'*257]}, {'snippet': 'unauthorized'},
])
def test_manual_coverage_and_candidate_validation_atomic(tmp_path, changes):
    store = SQLiteInformationStore(tmp_path / 'test.db')
    report = research(store, run_id='open', now=T, clock=lambda: T, session=feed_session(),
                      open_queries=['water'])
    q = report['open_queries'][0]
    doc = {'run_id': 'open', 'query_id': q['query_id'], 'query': q['query'],
               'observed_at': T.isoformat(), 'method': 'human_manual', 'operator': 'test',
               'status': 'empty', 'results': [], 'channels_covered': ['manual web']} | changes
    before = len(store.view_at(T).coverage)
    with pytest.raises(ValueError):
        import_search(store, doc, imported_at=T)
    assert len(store.view_at(T).coverage) == before


def test_old_corpus_does_not_prove_two_functioning_publishers_this_run(tmp_path):
    store = SQLiteInformationStore(tmp_path / 'test.db')
    first = research(store, run_id='first', now=T, clock=lambda: T, session=feed_session())
    assert len(first['functioning_publishers_this_run']) == 2
    second = research(store, run_id='second', now=T+timedelta(seconds=1),
                      clock=lambda: T+timedelta(seconds=1), session=feed_session())
    assert second['corpus_items'] and not second['functioning_publishers_this_run']
    assert second['status'] == 'NOT_PROVEN'


@pytest.mark.parametrize('fixture_name,expected_copies', [
    ('live_acceptance.json', 35), ('session_02.json', 38),
])
def test_b2_actual_metadata_receipts_reopen_pit_and_market_graph(
        tmp_path, monkeypatch, offline, fixture_name, expected_copies):  # noqa: F811
    from tests.test_graph_end_to_end import PromptCapturingModel, _graph
    folder = Path(__file__).parent / 'fixtures/checkpoint_b2'
    report = json.loads((folder / fixture_name).read_text(encoding='utf-8'))
    store = SQLiteInformationStore(tmp_path / 'test.db')
    for item in report['specimens']:
        config = next(c for c in DISCOVERY_CONFIGS+RELATED_CONFIGS
                      if c.source.source_id == item['source_id'])
        batch = parse_news_snapshot(rss(escape(item['title']), escape(item['url']),
                                       item['published_raw']), config,
                                    retrieved_at=datetime.fromisoformat(item['retrieved_at']))
        store.append(replace(batch, observations=tuple(replace(r,
            first_seen_time=datetime.fromisoformat(item['first_seen_time']),
            payload=dict(r.payload) | {'snapshot_hash': item['snapshot_sha256']})
            for r in batch.observations)))
    at = datetime.fromisoformat(report['completed_at'])
    store.append(MarketDataBatch((), (), at, (CoverageRecord(
        _run_key(report['run_id']), 'discovery.world', report['run_id'], 'discovery.run',
        at, CoverageStatus.UNKNOWN, json.dumps(report)),)))
    assert len(store.view_at(at).observations) == expected_copies
    assert set(report['functioning_publishers_this_run']) == {'Global Voices', 'Inter Press Service'}
    assert all(e['counts']['omitted'] == 0 for e in report['independent_enumeration'].values())
    documents = (report['research_log']['manual_receipt_documents'] if 'research_log' in report
                 else json.loads((folder / 'manual_search.json').read_text(encoding='utf-8')))
    for doc, receipt in zip(documents,
                            report['manual_verification']['receipts'], strict=True):
        at = datetime.fromisoformat(receipt['imported_at'])
        assert import_search(store, doc, imported_at=at) == receipt
    view = SQLiteInformationStore(store.path, read_only=True).view_at(at)
    assert len(view.observations) == expected_copies  # re-observation is not a new article
    assert {eid for receipt in report['manual_verification']['receipts']
            for eid in receipt['evidence_ids']} <= {r.observation_id for r in view.observations}
    first = min(r.retrieved_at for r in view.observations)
    assert not store.view_at(first-timedelta(microseconds=1)).observations
    assert all(r.payload['independent_confirmation'] == 'unknown' for r in view.observations)
    assert len('\n'.join(render_narrative_events(view))) <= 6000
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
    graph.propagate('BTCUSDT', at.date().isoformat(), asset_type='crypto', decision_time=at)
    prompt = '\n'.join(model.prompts)
    assert json.dumps(selected_narrative_events(view)[0].payload['claim'])[1:-1] in prompt
    assert 'Manual external search receipts=2' in prompt
    assert all(len(p) <= 28000 for p in model.prompts)
