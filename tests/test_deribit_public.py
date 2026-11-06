"""Synthetic wire-shaped fixtures only; no real exchange or production writes."""
import copy
import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from tradingagents.information.binance_spot import MarketDataBatch
from tradingagents.information.consumer import (
    build_analysis_information,
    render_analysis_information,
)
from tradingagents.information.deribit_public import (
    INGEST,
    PRIVATE,
    SAMPLE,
    SOURCE,
    URLS,
    PublicClient,
    acquire,
    collect,
    decimal,
    instrument,
    normalize,
    persist,
    render,
    selected,
)
from tradingagents.information.store import ObservationStoreConflict, SQLiteInformationStore

T = datetime(2026, 11, 6, 12, tzinfo=UTC)


def wires():
    return ({"jsonrpc": "2.0", "result": {
        "instrument_name": "BTC-PERPETUAL", "kind": "future", "base_currency": "BTC",
        "quote_currency": "USD", "settlement_currency": "BTC", "instrument_type": "reversed",
        "settlement_period": "perpetual", "price_index": "btc_usd", "is_active": True,
        "contract_size": 10, "tick_size": Decimal("0.5"), "min_trade_amount": 10}},
        {"jsonrpc": "2.0", "result": {"instrument_name": "BTC-PERPETUAL", "state": "open",
        "timestamp": int(T.timestamp()*1000), "mark_price": 75100, "index_price": 75000,
        "open_interest": 1000000, "current_funding": Decimal("-0.00001"), "funding_8h": Decimal("0.00002")}})


def receipts(offset=0, data=None):
    # Numeric fixture strings are JSON numbers on the wire, not binary floats.
    def encode(value):
        return json.dumps(value, default=str)
    return tuple({"endpoint": endpoint, "url": URLS[endpoint], "wire": json.loads(encode(wire),parse_float=Decimal),
        "raw": encode(wire), "sha256": hashlib.sha256(encode(wire).encode()).hexdigest(),
        "received_at": T+timedelta(seconds=offset+i), "status": 200, "elapsed_seconds": 0}
        for i, (endpoint, wire) in enumerate(zip(URLS, data or wires(), strict=True)))


class FixtureClient:
    def __init__(self, rows=None):
        self.rows, self.calls = rows or receipts(), []

    def get(self, endpoint):
        self.calls.append(endpoint)
        return self.rows[len(self.calls)-1]


def test_opt_in_before_transport():
    client = FixtureClient()
    with pytest.raises(PermissionError):
        acquire(client)
    assert client.calls == []
    acquire(client, enabled=True)
    assert client.calls == list(URLS)


def test_semantics_and_nullable_exchange_clock():
    m, t = wires()
    p = normalize(m, t, T)
    assert p['open_interest'] == '1000000' and p['oi_contracts_equivalent'] == '100000'
    assert p['oi_exchange_event_at'] is None and p['oi_delay_seconds'] is None
    assert p['current_funding'] == '-0.00001' and p['instrument']['settlement_currency'] == 'BTC'
    assert p['instrument']['expiry'] is None and p['traded_spot_futures_basis'] is None
    assert Decimal(p['mark_index_premium_pct']) > 0
    t['result'].pop('timestamp')
    assert normalize(m,t,T)['exchange_event_at'] is None
    t['result']['timestamp'] = int((T+timedelta(days=1)).timestamp()*1000)
    assert normalize(m,t,T)['exchange_future_clock']


@pytest.mark.parametrize('value', [True, 1.2, 'NaN', 'Infinity', '1e-2', '', '1.1234567890123456789', '-1', None,
                                  Decimal('1e9999999'),Decimal('1e-9999999')])
def test_bad_numbers(value):
    with pytest.raises(ValueError):
        decimal(value)


@pytest.mark.parametrize('key,value', [('instrument_name','ETH-PERPETUAL'),('quote_currency','USDT'),
    ('settlement_currency','USD'),('instrument_type','linear'),('contract_size',1),
    ('is_active',False),('kind','option'),('price_index','btc_usdt')])
def test_wrong_contract(key,value):
    m,_ = wires()
    m['result'][key] = value
    with pytest.raises(ValueError):
        instrument(m)


@pytest.mark.parametrize('key,value', [('open_interest',-1),('index_price',0),('mark_price',None),
    ('current_funding',2),('funding_8h','NaN'),('state','closed'),('timestamp',True),
    ('instrument_name','ETH-PERPETUAL')])
def test_bad_ticker(key,value):
    m,t = wires()
    t['result'][key] = value
    with pytest.raises(ValueError):
        normalize(m,t,T)


def test_atomic_restart_idempotency_pit_gap_and_private_export(tmp_path):
    path = tmp_path/'disposable.sqlite3'
    store = SQLiteInformationStore(path)
    rows = receipts()
    evidence = persist(store, rows, run_id='synthetic-1')
    at = rows[-1]['received_at']
    before = store.view_at(at-timedelta(microseconds=1))
    assert not selected(before)
    at_view = store.view_at(at)
    assert selected(at_view)[0].observation_id == evidence
    assert len(at_view.evidence_history) == 5 and len(at_view.coverage) == 3
    assert {r.metric for r in at_view.evidence_history} >= {SAMPLE,PRIVATE,INGEST}
    assert 'stale=False' in render(at_view)[0]
    assert 'stale=True' in render(store.view_at(at+timedelta(seconds=121)))[0]
    assert persist(SQLiteInformationStore(path), rows, run_id='synthetic-1') == evidence
    assert store.view_at(at) == at_view
    context = render_analysis_information(build_analysis_information(store,at))
    assert evidence in context and 'ATTRIBUTED Deribit' in context
    assert all(r['raw'] not in context for r in rows)
    assert 'never directional long/short' in context and 'no guaranteed funding cost' in context
    assert len(context) <= 28000
    # Changed receipt under an existing run cannot create any partial rows.
    altered = receipts(2)
    with pytest.raises(ObservationStoreConflict):
        persist(store, altered, run_id='synthetic-1')
    assert store.view_at(at+timedelta(days=1)) .evidence_history == at_view.evidence_history
    persist(store, receipts(300), run_id='synthetic-2')
    later = store.view_at(at+timedelta(days=1))
    assert len(later.gaps) == 1 and len(later.evidence_history) == 10
    assert store.view_at(at) == at_view
    with pytest.raises(ValueError,match='rollback'):
        persist(store,receipts(100),run_id='rollback')


def test_hash_malformed_api_and_receipt_rollback(tmp_path):
    store = SQLiteInformationStore(tmp_path/'disposable.sqlite3')
    rows = list(receipts())
    rows[1] = dict(rows[1],sha256='wrong')
    with pytest.raises(ValueError):
        persist(store,rows,run_id='bad')
    assert not store.view_at(T+timedelta(days=1)).evidence_history
    for update in ({'error':{}},{'testnet':True}):
        m,t = wires()
        t.update(update)
        with pytest.raises(ValueError):
            normalize(m,t,T)
    rows = list(receipts())
    rows[1] = dict(rows[1],received_at=T-timedelta(seconds=1))
    with pytest.raises(ValueError,match='rollback'):
        acquire(FixtureClient(rows),enabled=True)


def test_rights_revocation_is_point_in_time(tmp_path):
    store = SQLiteInformationStore(tmp_path/'disposable.sqlite3')
    persist(store,receipts(),run_id='test')
    at = T+timedelta(seconds=2)
    denied = replace(SOURCE,version='denied',metadata=tuple((k,'denied' if k=='personal_inference' else v) for k,v in SOURCE.metadata))
    store.append(MarketDataBatch((),(),at,source_definitions=(denied,)))
    assert selected(store.view_at(at-timedelta(microseconds=1)))
    assert not selected(store.view_at(at))


class Response:
    status_code = 200

    def __enter__(self):
        return self

    def __exit__(self,*args):
        pass

    def iter_content(self, size):
        yield b'{"jsonrpc":"2.0","result":{}}'


class Session:
    def __init__(self,response=None):
        self.response,self.calls = response or Response(),[]

    def get(self,url,**kwargs):
        self.calls.append((url,kwargs))
        return self.response


def test_transport_allowlist_pacing_no_redirects_and_bound():
    sleeps=[]
    session=Session()
    client=PublicClient(session,clock=lambda:T,monotonic=lambda:0,sleep=sleeps.append)
    client.get('get_instrument')
    client.get('ticker')
    assert sleeps == [1.1]
    assert session.calls[0][1]['allow_redirects'] is False
    assert session.calls[0][1]['timeout'] == (5,10)
    with pytest.raises(ValueError):
        client.get('ticker')
    with pytest.raises(ValueError):
        PublicClient(session).get('https://other.example')


@pytest.mark.parametrize('status',[301,403,429,500])
def test_denials_never_retry(status):
    response=Response()
    response.status_code=status
    session=Session(response)
    with pytest.raises(ConnectionError):
        PublicClient(session).get('ticker')
    assert len(session.calls)==1


def test_oversize_response_stops():
    class Large(Response):
        def iter_content(self,size):
            yield b'x'*262145
    with pytest.raises(ConnectionError):
        PublicClient(Session(Large())).get('ticker')


def test_small_numeric_exponent_exact_and_signed_zero():
    assert decimal(Decimal('1E-8')) == '0.00000001'
    assert decimal('-0.00001',signed=True) == '-0.00001'


def test_no_metadata_mutation():
    data=wires()
    old=copy.deepcopy(data)
    normalize(*data,T)
    assert data==old


def test_collection_backup_gates_and_exact_rows(tmp_path):
    import sqlite3

    from tradingagents.information.reconciliation import read_rows, validate

    path=tmp_path/'disposable.sqlite3'
    SQLiteInformationStore(path)
    client=FixtureClient()
    backup=tmp_path/'before.sqlite3'
    with pytest.raises(PermissionError):
        collect(path,backup,client=client,run_id='test')
    assert not client.calls and not backup.exists()
    with pytest.raises(ValueError):
        collect(path,backup,client=client,run_id='../invalid',enabled=True)
    assert not client.calls and not backup.exists()
    result=collect(path,backup,client=client,run_id='test',enabled=True)
    assert result['before']['counts']['observations']==0
    assert result['after']['counts']['observations']==5
    with sqlite3.connect(backup) as db:
        assert validate(db)==result['before']
        assert not read_rows(db)['observations']
    with pytest.raises(ValueError,match='already acquired'):
        collect(path,tmp_path/'repeat.sqlite3',client=FixtureClient(),run_id='test',enabled=True)


def test_ambiguous_same_instant_and_bad_data_leave_history_immutable(tmp_path):
    store=SQLiteInformationStore(tmp_path/'disposable.sqlite3')
    persist(store,receipts(),run_id='one')
    cutoff=T+timedelta(days=1)
    baseline=store.view_at(cutoff)
    with pytest.raises(ObservationStoreConflict):
        persist(store,receipts(),run_id='two')
    data=wires()
    data[1]['result']['open_interest']=-1
    with pytest.raises(ValueError):
        persist(store,receipts(2,data),run_id='bad')
    assert store.view_at(cutoff)==baseline
