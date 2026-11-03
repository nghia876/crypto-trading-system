"""Synthetic/offline contract tests, never evidence of live world coverage."""

import json
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock
from xml.sax.saxutils import escape

import pytest
import requests

from tests.test_broad_news import T, rss, session_for
from tests.test_graph_end_to_end import offline  # noqa: F401
from tradingagents.information.adaptive_discovery import _run_key, expand, import_search, research
from tradingagents.information.binance_spot import CoverageRecord, CoverageStatus, MarketDataBatch
from tradingagents.information.discovery_sources import DISCOVERY_CONFIGS, RELATED_CONFIGS
from tradingagents.information.narrative_events import narrative_events, render_narrative_events
from tradingagents.information.news import parse_news_snapshot
from tradingagents.information.store import SQLiteInformationStore
from tradingagents.information.world_radar import PolicySession


def feed_session():
    session = MagicMock()
    def get(url, **kwargs):
        if url.endswith('/robots.txt'):
            return session_for('User-agent: *\nAllow: /').get.return_value
        config = next(c for c in DISCOVERY_CONFIGS + RELATED_CONFIGS if c.source.endpoint == url)
        title = ('Bangladesh cyber law challenges artificial intelligence' if 'globalvoices' in url
                 else 'Cholera outbreak threatens water food and energy grid')
        return session_for(rss(title, url=config.source.endpoint + '?story=1')).get.return_value
    session.get.side_effect = get
    return session


def test_broad_channels_actual_expansion_journal_reopen_and_no_votes(tmp_path):
    store = SQLiteInformationStore(tmp_path / 'canonical.db')
    session = feed_session()
    report = research(store, run_id='synthetic-1', now=T, clock=lambda: T, session=session)
    assert len(report['polls']) == 3
    assert report['related_feed_decision']['source_id'] == RELATED_CONFIGS[1].source.source_id
    assert report['related_feed_decision']['input_evidence_ids']
    assert report['queries'] and all(q['status'] == 'executed' for q in report['queries'])
    assert report['topics']['HEALTH'] and report['topics']['REGULATION']
    assert report['topics']['ENERGY_GRID'] and report['topics']['WATER_FOOD']
    assert report['status'] == 'PARTIAL_METADATA_PILOT'
    assert all(q['external_status'] == 'manual_search_pending' for q in report['queries'])
    view = SQLiteInformationStore(store.path, read_only=True).view_at(T)
    assert all(r.payload['independent_confirmation'] == 'unknown' for r in view.observations)
    assert all(r.payload['evidence_level'] == 'HEADLINE_METADATA_ONLY' for r in view.observations)
    assert not SQLiteInformationStore(store.path, read_only=True).view_at(T-timedelta(seconds=1)).observations
    before = session.get.call_count
    assert research(store, run_id='synthetic-1', session=session) == report
    assert session.get.call_count == before
    repeat = research(store, run_id='synthetic-2', now=T+timedelta(seconds=1),
                      clock=lambda: T+timedelta(seconds=1), session=session)
    assert not repeat['queries'] and not repeat['polls']
    assert session.get.call_count == before
    assert len(narrative_events(view)) == 3


@pytest.mark.parametrize('budget', [0, 17, -1])
def test_invalid_query_budget(budget):
    with pytest.raises(ValueError):
        expand([], query_budget=budget)


@pytest.mark.parametrize('title', [
    'War and sanctions disrupt trade routes', 'Flood and wildfire force evacuation',
    'Reservoir drought threatens agriculture harvest', 'Grid power failure spreads',
    'Cholera outbreak overwhelms hospital', 'AI research faces cyber attack',
    'Court bans new regulation', 'Unclassified obscure development in Laos',
    '未确认消息 重大事件 需要调查',
])
def test_topics_never_gate_admission_and_queries_depend_on_inputs(title):
    c = DISCOVERY_CONFIGS[0]
    batch = parse_news_snapshot(rss(title, url='https://globalvoices.org/example'), c, retrieved_at=T)
    assert len(batch.observations) == 1
    q = expand(batch.observations, query_budget=1)
    assert q and q[0]['input_evidence_ids'] == [batch.observations[0].observation_id]


def manual_doc(report):
    query = report['queries'][0]
    return {'run_id': report['run_id'], 'query_id': query['query_id'], 'query': query['query'],
            'method': 'chatgpt_assisted_manual', 'operator': 'test operator',
            'observed_at': T.isoformat(), 'status': 'success',
            'results': [{'source_id': DISCOVERY_CONFIGS[0].source.source_id,
                         'title': 'Unconfirmed rumor of power outage',
                         'url': 'https://globalvoices.org/manual-result'}]}


def test_manual_query_import_pit_missingness_atomic_rights_and_idempotency(tmp_path):
    store = SQLiteInformationStore(tmp_path / 'canonical.db')
    report = research(store, run_id='manual-parent', now=T, clock=lambda: T, session=feed_session())
    document = manual_doc(report)
    later = T + timedelta(hours=1)
    result = import_search(store, document, imported_at=later)
    assert import_search(store, document, imported_at=later+timedelta(seconds=1)) == result
    assert not any(r.raw_reference.endswith('manual-result') for r in store.view_at(T).observations)
    row = next(r for r in store.view_at(later).observations if r.raw_reference.endswith('manual-result'))
    assert row.publication_time is None and row.available_at == later
    assert row.payload['acquisition_method'] == 'chatgpt_assisted_manual'
    assert row.payload['lifecycle'] == 'unconfirmed'
    for mutation in [{'snippet': 'not authorized'}, {'url': 'https://other.example/story'}]:
        invalid = json.loads(json.dumps(document))
        invalid['results'][0].update(mutation)
        with pytest.raises(ValueError):
            import_search(store, invalid, imported_at=later)
    invalid = dict(document, query='invented query')
    with pytest.raises(ValueError):
        import_search(store, invalid, imported_at=later)
    failure = dict(document, status='failure', results=[], error='manual search unavailable')
    assert import_search(store, failure, imported_at=later)['status'] == 'failure'


def test_failures_empty_coverage_and_actionable_health(tmp_path):
    store = SQLiteInformationStore(tmp_path / 'canonical.db')
    session = MagicMock()
    session.get.side_effect = requests.Timeout()
    report = research(store, run_id='blocked', now=T, clock=lambda: T, session=session)
    assert report['status'] == 'NOT_PROVEN'
    assert len(report['uncovered_topics']) == 8
    assert not report['queries'] and not report['related_feed_decision']
    assert all(p['error'] == 'RobotsUnavailable' for p in report['polls'])
    assert all(h['consecutive_failures'] == 1 for h in report['health']
               if h['selection_status'] == 'selected')
    assert 'external search pending/manual' in '\n'.join(render_narrative_events(store.view_at(T)))


def test_delay_opt_in_waits_and_default_remains_deferred(monkeypatch):
    from tradingagents.information import world_radar
    waits = []
    monkeypatch.setattr(world_radar.time, 'sleep', waits.append)
    monkeypatch.setattr(world_radar.time, 'monotonic', lambda: 100)
    session = session_for('User-agent: *\nCrawl-delay: 10\nAllow: /')
    policy = PolicySession(session, DISCOVERY_CONFIGS, wait_for_crawl_delay=True)
    policy.get(DISCOVERY_CONFIGS[0].source.endpoint)
    assert waits == [10] and session.get.call_count == 2


def test_actual_market_graph_with_reopened_pilot(tmp_path, monkeypatch, offline):  # noqa: F811
    from tests.test_graph_end_to_end import PromptCapturingModel, _graph
    store = SQLiteInformationStore(tmp_path / 'canonical.db')
    research(store, run_id='graph-pilot', now=T, clock=lambda: T, session=feed_session())
    rendered = '\n'.join(render_narrative_events(SQLiteInformationStore(store.path, read_only=True).view_at(T)))
    assert len(rendered) <= 6000
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
    graph.propagate('BTCUSDT', T.date().isoformat(), asset_type='crypto', decision_time=T)
    prompt = '\n'.join(model.prompts)
    assert 'Bangladesh cyber law' in prompt and 'Cholera outbreak' in prompt
    assert 'graph-pilot' in prompt and 'PROVISIONAL' in prompt
    assert all(len(p) <= 28000 for p in model.prompts)


def test_observed_live_metadata_replay_and_actual_graph(tmp_path, monkeypatch, offline):  # noqa: F811
    from tests.test_graph_end_to_end import PromptCapturingModel, _graph
    from tradingagents.information.narrative_events import selected_narrative_events
    folder = Path(__file__).parent / 'fixtures/checkpoint_b'
    report = json.loads((folder / 'live_acceptance.json').read_text(encoding='utf-8'))
    cutoff = datetime.fromisoformat(report['completed_at'])
    store = SQLiteInformationStore(tmp_path / 'canonical.db')
    for item in report['specimens']:
        config = next(c for c in DISCOVERY_CONFIGS+RELATED_CONFIGS if c.source.source_id == item['source_id'])
        batch = parse_news_snapshot(rss(escape(item['title']), escape(item['url']),
                                        item['published_raw']), config,
                                    retrieved_at=datetime.fromisoformat(item['retrieved_at']))
        store.append(replace(batch, observations=tuple(replace(r,
            first_seen_time=datetime.fromisoformat(item['first_seen_time']),
            payload=dict(r.payload) | {'snapshot_hash': item['snapshot_sha256']})
            for r in batch.observations)))
    store.append(MarketDataBatch((), (), cutoff, (CoverageRecord(
        _run_key(report['run_id']), 'discovery.world', report['run_id'], 'discovery.run',
        cutoff, CoverageStatus.UNKNOWN, json.dumps(report)),)))
    view = SQLiteInformationStore(store.path, read_only=True).view_at(cutoff)
    assert len(view.observations) == 16 and len(narrative_events(view)) == 12
    assert {r.payload['publisher_group'] for r in view.observations} == {'Global Voices'}
    assert report['status'] == 'NOT_PROVEN'  # two feeds are still ONE publisher
    assert all(not e['in_window_not_retained'] for e in report['independent_enumeration'].values())
    assert len('\n'.join(render_narrative_events(view))) <= 6000
    first = min(r.retrieved_at for r in view.observations)
    assert not store.view_at(first-timedelta(microseconds=1)).observations
    model = PromptCapturingModel()
    graph = _graph(tmp_path, monkeypatch, model, information_store_path=store.path)
    graph.propagate('BTCUSDT', cutoff.date().isoformat(), asset_type='crypto', decision_time=cutoff)
    prompt = '\n'.join(model.prompts)
    assert selected_narrative_events(view)[0].payload['claim'] in prompt
    assert report['run_id'] in prompt
    assert all(len(p) <= 28000 for p in model.prompts)
    receipt = json.loads((folder / 'manual_search.json').read_text(encoding='utf-8'))
    imported = import_search(store, receipt, imported_at=datetime.fromisoformat(receipt['observed_at']))
    assert imported['status'] == 'empty' and not imported['evidence_ids']
    assert len(store.view_at(datetime.fromisoformat(receipt['observed_at'])).observations) == 16


def test_budget_accounting_retention_and_same_url_repetition(tmp_path):
    store = SQLiteInformationStore(tmp_path / 'canonical.db')
    report = research(store, run_id='caps', now=T, clock=lambda: T, session=feed_session(),
                      query_budget=1, retention=1)
    assert len(report['queries']) == 1 and report['queries_omitted_budget'] >= 1
    assert all(p['items'] <= 1 for p in report['polls'])
    doc = manual_doc(report)
    doc['results'][0]['url'] = DISCOVERY_CONFIGS[0].source.endpoint + '?story=1'
    doc['results'][0]['title'] = 'Bangladesh cyber law challenges artificial intelligence'
    import_search(store, doc, imported_at=T+timedelta(seconds=1))
    view = store.view_at(T+timedelta(seconds=1))
    assert len(view.observations) == 4 and len(narrative_events(view)) == 3
    assert all(r.payload['independent_confirmation'] == 'unknown' for r in view.observations)


def test_cross_feed_host_backoff_blocks_adaptive_and_next_broad_run(tmp_path):
    store = SQLiteInformationStore(tmp_path / 'canonical.db')
    session = feed_session()
    original = session.get.side_effect
    def get(url, **kwargs):
        if url == DISCOVERY_CONFIGS[0].source.endpoint:
            response = MagicMock()
            response.status_code = 429
            response.headers = {'Retry-After': '7200'}
            response.raise_for_status.side_effect = requests.HTTPError(response=response)
            response.__enter__.return_value = response
            return response
        if url == DISCOVERY_CONFIGS[1].source.endpoint:
            return session_for(rss('AI research and cyber regulation',
                                   url='https://www.ipsnews.net/example')).get.return_value
        return original(url, **kwargs)
    session.get.side_effect = get
    report = research(store, run_id='rate-1', now=T, clock=lambda: T, session=session)
    assert report['related_feed_decision']['status'] == 'host_backoff'
    assert not any(call.args[0] in {c.source.endpoint for c in RELATED_CONFIGS}
                   for call in session.get.call_args_list)
    later = T+timedelta(hours=1)
    next_session = feed_session()
    research(store, run_id='rate-2', now=later, clock=lambda: later, session=next_session)
    assert not any('globalvoices.org' in call.args[0] for call in next_session.get.call_args_list)
