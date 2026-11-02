"""User-invoked free WORLD research; one store, finite requests, no LLM API.

Topic rules label coverage, never filter admission. Queries are grounded in
retrieved metadata; automatic execution searches only the explicitly named local
corpus. External queries require a separately recorded manual search import.
"""

import argparse
import json
import re
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

import requests

from tradingagents.information.binance_spot import CoverageRecord, CoverageStatus, MarketDataBatch
from tradingagents.information.discovery_sources import DISCOVERY_CONFIGS, RELATED_CONFIGS
from tradingagents.information.news import _digest, parse_news_snapshot, poll_once
from tradingagents.information.observations import _require_aware
from tradingagents.information.polling import _state, coordinate, job_lock
from tradingagents.information.store import SQLiteInformationStore
from tradingagents.information.world_radar import PolicySession

TOPICS = {
    "WAR_GEOPOLITICS": r"war|conflict|missile|diploma|sanction|military|election",
    "TRADE": r"trade|tariff|export|shipping|migration",
    "CLIMATE_DISASTER": r"climate|flood|storm|quake|wildfire|hurricane",
    "WATER_FOOD": r"water|reservoir|drought|agricultur|crop|food|harvest|hunger",
    "ENERGY_GRID": r"energy|grid|power|electric|oil|gas",
    "HEALTH": r"health|disease|cholera|outbreak|vaccine|hospital",
    "SCIENCE_AI_TECH_CYBER": r"science|research|\bai\b|intelligence|tech|cyber|hack|chip",
    "REGULATION": r"regulat|legislat|law|policy|court|ban\b",
}
STOP = frozenset(["the", "a", "an", "in", "on", "of", "for", "and", "to", "with", "from", "is", "are", "as", "at", "by", "how", "why", "new", "says", "amid", "after", "over", "under", "this", "that"])


def _tokens(text):
    return [t for t in re.findall(r"[^\W_]+", text.casefold()) if len(t) > 2 and t not in STOP][:80]


def expand(rows, *, previous=(), query_budget=8):
    """One bounded expansion hop; never treats search matches as corroboration."""
    if not 1 <= query_budget <= 16:
        raise ValueError("query budget must be 1..16")
    decisions, seen = [], set(previous)
    for row in rows:
        words = list(dict.fromkeys(_tokens(row.payload['claim'])))[:4]
        if len(words) < 2:
            continue
        query = " ".join(words)
        key = _digest(query)
        if key in seen:
            continue
        seen.add(key)
        matches = [r.observation_id for r in rows
                   if len(set(words) & set(_tokens(r.payload['claim']))) >= 2][:8]
        decisions.append({"query_id": key, "query": query,
                          "input_evidence_ids": [row.observation_id],
                          "input_available_at": row.available_at.isoformat(),
                          "reason": "first four distinct non-stop headline tokens; one hop",
                          "executor": "local_permitted_metadata", "status": "executed",
                          "result_ids": matches, "external_status": "manual_search_pending",
                          "relation_status": "PROVISIONAL; lexical overlap only; origin UNKNOWN"})
        if len(decisions) == query_budget:
            break
    return decisions


def _run_key(run_id):
    if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', run_id):
        raise ValueError("run ID must be 1..128 letters/digits or _.:-")
    return "discovery-run:" + _digest(run_id)


def research(store, *, run_id, session, now=None, clock=None, query_budget=8, retention=40):
    """Persist immutable run manifest alongside existing intake/health journals."""
    key = _run_key(run_id)
    existing = store.coverage_by_id(key)
    if existing:
        return json.loads(existing.detail)
    now = now or datetime.now(UTC)
    _require_aware("now", now)
    if not 1 <= retention <= 100 or not 1 <= query_budget <= 16:
        raise ValueError("retention 1..100; query budget 1..16")
    policy = PolicySession(session, DISCOVERY_CONFIGS + RELATED_CONFIGS, wait_for_crawl_delay=True)
    outcomes, health = coordinate(
        store, DISCOVERY_CONFIGS + RELATED_CONFIGS, now=now, clock=clock, session=policy,
        source_ids={c.source.source_id for c in DISCOVERY_CONFIGS},
        interval=3600, max_sources=2, observation_limit=retention,
        window_start=now - timedelta(days=7))
    cutoff = max([now] + [r.observed_at for r in health])
    view = store.view_at(cutoff)
    inputs = [r for r in view.observations
              if r.observation_id in {eid for p in outcomes for eid in p.evidence_ids}]
    followup = None
    for topic, config in zip(('CLIMATE_DISASTER', 'SCIENCE_AI_TECH_CYBER'), RELATED_CONFIGS, strict=True):
        triggers = [r.observation_id for r in inputs if re.search(TOPICS[topic], r.payload['claim'], re.I)]
        if triggers:
            due = _state(store, config, cutoff, 3600)[3]
            host = urlsplit(config.source.endpoint).hostname
            host_backoff = any(
                urlsplit(other.source.endpoint).hostname == host
                and (history := _state(store, other, cutoff, 3600))[0]
                and history[0][-1][1].get('http_status') in {429, 503}
                and history[3] > cutoff
                for other in DISCOVERY_CONFIGS + RELATED_CONFIGS)
            followup = {'source_id': config.source.source_id, 'topic': topic,
                        'input_evidence_ids': triggers[:20], 'decided_at': cutoff.isoformat(),
                        'status': 'host_backoff' if host_backoff else
                                  'not_due_or_backoff' if due > cutoff else 'executed',
                        'reason': 'retrieved headline topic selects reviewed related feed; fanout=1'}
            if due <= cutoff and not host_backoff:
                extra = poll_once(store, (config,), poll_id='adaptive:' + run_id, session=policy,
                                  clock=clock, observation_limit=retention,
                                  window_start=now - timedelta(days=7))
                outcomes += extra
                cutoff = max(cutoff, extra[0].observed_at)
                followup['outcome'] = json.loads(extra[0].detail)['outcome']
                followup['completed_at'] = cutoff.isoformat()
                view = store.view_at(cutoff)
            break
    prior = [json.loads(c.detail) for c in view.coverage if c.coverage_id.startswith('discovery-run:')]
    previous = {q['query_id'] for p in prior
                if cutoff - datetime.fromisoformat(p['completed_at']) < timedelta(days=1)
                for q in p['queries']}
    # Canonical URL identity collapses repeated polls and cross-channel copies.
    latest = {}
    for row in sorted(view.observations, key=lambda r: (r.available_at, r.observation_id)):
        if (row.source_id in {c.source.source_id for c in DISCOVERY_CONFIGS + RELATED_CONFIGS}
                and row.metric == 'narrative.event'
                and cutoff - row.retrieved_at <= timedelta(days=7)):
            latest[row.subject] = row
    ordered = sorted(latest.values(), key=lambda r: (r.available_at, r.observation_id), reverse=True)
    rows = ordered[:200]
    queries = expand(rows, previous=previous, query_budget=query_budget)
    candidates = {_digest(' '.join(list(dict.fromkeys(_tokens(r.payload['claim'])))[:4]))
                  for r in rows if len(set(_tokens(r.payload['claim']))) >= 2}
    topics = {name: [r.observation_id for r in rows
                     if re.search(pattern, r.payload['claim'], re.I)][:20]
              for name, pattern in TOPICS.items()}
    report = {
        'run_id': run_id, 'started_at': now.isoformat(), 'completed_at': cutoff.isoformat(),
        'mode': 'publisher_feed_metadata_and_local_adaptive_search',
        'queries': queries, 'query_budget': query_budget, 'expansion_depth': 1,
        'related_feed_decision': followup, 'max_feed_requests': 3,
        'repetition_window_hours': 24, 'corpus_items': len(rows),
        'query_candidates': len(candidates),
        'queries_suppressed_repetition': len(candidates & previous),
        'queries_omitted_budget': max(0, len(candidates - previous) - len(queries)),
        'corpus_omitted': max(0, len(ordered) - len(rows)), 'topics': topics,
        'uncovered_topics': [name for name, ids in topics.items() if not ids],
        'polls': [dict(source_id=r.source_id, observed_at=r.observed_at.isoformat(),
                       **json.loads(r.detail)) for r in outcomes],
        'health': [dict(source_id=r.source_id, **json.loads(r.detail)) for r in health],
        'robots': policy.report(), 'retention_per_source': retention,
        'source_selection': [c.source.source_id for c in DISCOVERY_CONFIGS],
        'unknowns': ['PC offline windows UNKNOWN', 'upstream feed omissions UNKNOWN',
                     'publisher diversity is not independent reporting',
                     'external web search not automatically executed', 'summaries rights gated'],
        'actions': ['Inspect polls.error and robots before diagnosing publisher outage',
                    'Use health.next_due; do not retry in a tight loop',
                    'Repair or replace invalid feed endpoints after a new exact rights review',
                    'Execute pending external queries manually and import only eligible metadata'],
        'status': 'NOT_PROVEN' if len({r.payload['publisher_group'] for r in rows}) < 2 else 'PARTIAL_METADATA_PILOT',
    }
    store.append(MarketDataBatch((), (), cutoff, (CoverageRecord(
        key, 'discovery.world', run_id, 'discovery.run', cutoff, CoverageStatus.UNKNOWN,
        json.dumps(report, sort_keys=True), tuple(r.observation_id for r in rows)),)))
    return report


def import_search(store, document, *, imported_at=None):
    """Complementary manual/ChatGPT search, not an automated search API.

    Only reviewed publisher metadata is accepted. Remote rights assertions and
    snippets cannot authorize retention. Import time is the availability floor.
    """
    at = imported_at or datetime.now(UTC)
    _require_aware('imported_at', at)
    if len(json.dumps(document)) > 100_000:
        raise ValueError('manual import exceeds 100KB')
    allowed = {'run_id', 'query_id', 'query', 'method', 'operator', 'observed_at',
               'status', 'results', 'error'}
    if set(document) - allowed or len(document.get('error', '')) > 256:
        raise ValueError('manual import contains unsupported fields or oversized error')
    parent = store.coverage_by_id(_run_key(document['run_id']))
    if parent is None or parent.observed_at > at:
        raise ValueError('parent run must be available')
    report = json.loads(parent.detail)
    query = next((q for q in report['queries'] if q['query_id'] == document['query_id']), None)
    if query is None or document['query'] != query['query']:
        raise ValueError('exact recorded query required')
    if document['method'] not in {'human_manual', 'chatgpt_assisted_manual'}:
        raise ValueError('manual provenance required')
    observed = datetime.fromisoformat(document['observed_at'])
    _require_aware('observed_at', observed)
    if observed > at or observed < parent.observed_at:
        raise ValueError('manual observation must follow parent run and precede import')
    if not document.get('operator') or len(document['operator']) > 128:
        raise ValueError('bounded operator provenance required')
    results = document.get('results', [])
    if len(results) > 8 or document['status'] not in {'success', 'empty', 'failure'}:
        raise ValueError('manual query status or result budget invalid')
    if (document['status'] == 'success') != bool(results):
        raise ValueError('success requires results; empty/failure cannot contain results')
    if document['status'] == 'failure' and not document.get('error'):
        raise ValueError('failure reason required')
    key = 'discovery-import:' + _digest(json.dumps(document, sort_keys=True))
    if existing := store.coverage_by_id(key):
        return json.loads(existing.detail)
    batches = []
    for result in results:
        config = next((c for c in DISCOVERY_CONFIGS
                       if c.source.source_id == result['source_id']), None)
        if config is None:
            raise ValueError('unreviewed publisher; rights review required')
        if set(result) - {'source_id', 'title', 'url', 'published_raw'}:
            raise ValueError('only headline/link/date metadata accepted; snippets rights gated')
        xml = ('<rss><channel><item><title>' + escape(result['title'])
               + '</title><link>' + escape(result['url']) + '</link>'
               + ('<pubDate>' + escape(result['published_raw']) + '</pubDate>'
                  if result.get('published_raw') else '') + '</item></channel></rss>')
        batch = parse_news_snapshot(xml, config, retrieved_at=at)
        if len(batch.observations) != 1:
            raise ValueError('result URL outside reviewed publisher')
        batches.append(batch)
    observations = tuple(replace(r,
        first_seen_time=store.first_seen_for_subject(r.subject) or at,
        payload=dict(r.payload) | {'discovery_run_id': document['run_id'],
                                  'manual_search_query_id': document['query_id'],
                                  'manual_search_query': document['query'],
                                  'snapshot_kind': 'manual_metadata_serialization_not_remote_response',
                                  'acquisition_method': document['method'],
                                  'manual_operator': document['operator'],
                                  'manual_observed_at': observed.isoformat()})
        for b in batches for r in b.observations)
    detail = dict(document) | {'imported_at': at.isoformat(), 'evidence_ids': [r.observation_id for r in observations]}
    store.append(MarketDataBatch(observations, (), at, (CoverageRecord(
        key, 'discovery.manual', document['run_id'], 'discovery.query', at,
        CoverageStatus.UNKNOWN, json.dumps(detail, sort_keys=True),
        tuple(r.observation_id for r in observations)),),
        tuple(c.source_definition for c in DISCOVERY_CONFIGS)))
    return detail


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--run-id')
    parser.add_argument('--manual-import', type=Path)
    parser.add_argument('--retention', type=int, default=40)
    parser.add_argument('--query-budget', type=int, default=8)
    args = parser.parse_args(argv)
    if args.report.exists() or (not args.run_id and not args.manual_import):
        parser.error('new report path and run ID or manual import required')
    if not args.store.is_file():
        parser.error('use the existing canonical SQLite store')
    store = SQLiteInformationStore(args.store)
    with job_lock(store), requests.Session() as session:
        if args.manual_import:
            if args.manual_import.stat().st_size > 100_000:
                parser.error('manual import exceeds 100KB')
            report = import_search(store, json.loads(args.manual_import.read_text(encoding='utf-8')))
        else:
            report = research(store, run_id=args.run_id, session=session,
                              retention=args.retention, query_budget=args.query_budget)
    with args.report.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)


if __name__ == '__main__':
    main()
