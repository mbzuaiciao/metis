"""Fixed reconstruction arithmetic and provenance checks; no live inference/data retrieval."""
from copy import deepcopy
from datetime import date
import importlib
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from metis.analytics import events
from metis.analytics.engine import load_json, workstation
from metis.analytics.etf import historical_prices
from metis.reasoning.causal import CausalRequest, demo_exploration


EXPECTED = {
    'cpi-2022': [-72000, -32300, -122500, 123750, -108192.91, -81000, -182009.82, -63000, -739202.17, -193489.15, -150127.36, 0],
    'march-2025': [144000, 19000, 245000, -123750, 51237.46, -54000, -30207.22, -52500, -452804.95, -205259.47, -23339.17, 0],
    'october-2026': [57600, 9500, 98000, -78750, 7195.66, 10071.27, -15468.06, -13891.89, -301393.7, -103757.65, -2063.59, 0],
}


@pytest.mark.parametrize('id,total', [('cpi-2022', -1620071.41), ('march-2025', -482623.35), ('october-2026', -332957.96)])
def test_fixed_position_oracles_reconcile_all_signed_values(id, total):
    snapshot = events.event_snapshot(id)
    rows = snapshot['positions']
    assert [r['id'] for r in rows] == ['UST10', 'UST2', 'IRS-R', 'IRS-P', 'LQD', 'EUIG', 'HYG', 'EUHY', 'SPY', 'HEFA', 'FX-EUR', 'CASH']
    assert [r['pnl_usd'] for r in rows] == EXPECTED[id]
    assert sum(r['start_value_usd'] for r in rows) == snapshot['start_nav_usd'] == 100_000_000
    assert snapshot['estimated_pnl_usd'] == total
    assert sum(r['pnl_usd'] for r in rows) == pytest.approx(total)
    assert sum(r['end_value_usd'] for r in rows) == pytest.approx(snapshot['end_nav_usd'])
    assert snapshot['end_nav_usd'] - snapshot['start_nav_usd'] == pytest.approx(total)
    assert snapshot['coverage_count'] == 12
    assert all(r['status'] == 'Estimated' for r in rows)
    assert all(r['end_value_usd'] - r['start_value_usd'] == pytest.approx(r['pnl_usd']) for r in rows)
    assert 'not actual historical holdings' in snapshot['disclosure']
    assert 'cannot identify' in snapshot['causal_use']


def test_observed_yield_units_and_hypothetical_duration_not_market_prices():
    snapshot = events.event_snapshot('cpi-2022')
    a, b = snapshot['positions'][:2]
    assert [i['value'] for i in a['inputs']] == [3.37, 3.42, 8]
    assert a['inputs'][0]['status'] == 'Observed'
    assert a['inputs'][2]['status'] == 'Hypothetical assumption'
    assert a['pnl_usd'] == -18_000_000 * 8 * .0005
    assert b['pnl_usd'] == pytest.approx(-10_000_000 * 1.9 * .0017)
    assert a['terms']['exposure'] == 'Hypothetical constant-maturity Treasury exposure'
    assert 'CUSIP' not in a['terms'] and 'close' not in a


@pytest.mark.parametrize('id', EXPECTED)
def test_off_market_otc_strikes_reproduce_start_end_marks_and_direction(id):
    s = events.event_snapshot(id)
    for r in [r for r in s['positions'] if r['id'].startswith('IRS')]:
        t = r['terms']
        start, end = r['inputs'][:2]
        pv01 = t['signed_pv01_usd_per_bp']
        assert pv01 == t['direction'] * t['notional_usd'] * t['annuity_years'] / 10000
        assert pv01 * (t['fixed_rate_pct'] * 100 - start['value'] * 100) == pytest.approx(r['start_value_usd'])
        assert pv01 * (t['fixed_rate_pct'] * 100 - end['value'] * 100) == pytest.approx(r['end_value_usd'])
        assert t['effective_date'] == s['start'] < s['end'] < t['maturity_date']
        assert date.fromisoformat(t['maturity_date']).weekday() < 5
        assert 'not notional' in t['initial_mark_relation']
        assert r['inputs'][2]['status'] == 'Approximate input'
    fx = next(r for r in s['positions'] if r['id'] == 'FX-EUR')
    t = fx['terms']
    for index, key in [(0, 'start_value_usd'), (1, 'end_value_usd')]:
        assert t['eur_bought'] * .96 * (fx['inputs'][index]['value'] - t['strike_usd_per_eur']) == pytest.approx(fx[key], abs=.005)
    assert date.fromisoformat(t['maturity_date']).weekday() < 5
    assert t['usd_sold'] == pytest.approx(t['eur_bought'] * t['strike_usd_per_eur'])
    assert t['eur_bought'] * fx['inputs'][0]['value'] == pytest.approx(12_000_000)
    cash = next(r for r in s['positions'] if r['id'] == 'CASH')
    assert cash['start_value_usd'] == cash['end_value_usd'] == 4_000_000
    assert cash['pnl_usd'] == 0 and all(i['status'] == 'Hypothetical assumption' for i in cash['inputs'])


def test_ineligible_etfs_are_explicit_current_mandate_hypotheticals_not_fabricated_closes():
    for id in ['cpi-2022', 'march-2025']:
        rows = events.event_snapshot(id)['positions']
        for r in [r for r in rows if r['id'] in {'EUIG', 'EUHY'}]:
            assert all(i['status'] == 'Hypothetical assumption' and i['source_url'] is None for i in r['inputs'])
            assert 'Not an ETF price' in ' '.join(r['assumptions'])
            assert 'unadjusted close' not in str(r)
    for id, dates in [('cpi-2022', ('2022-09-12', '2022-09-13')), ('october-2026', ('2026-10-29', '2026-10-30'))]:
        old = historical_prices(*dates)
        new = events.event_snapshot(id)
        for r in old['positions']:
            if r['status'] == 'available':
                new_row = next(n for n in new['positions'] if n['id'] == r['id'])
                assert new_row['pnl_usd'] == r['price_pnl_usd']
                assert all(i['status'] == 'Observed' for i in new_row['inputs'])
    march_spy = next(r for r in events.event_snapshot('march-2025')['positions'] if r['id'] == 'SPY')
    assert [i['value'] for i in march_spy['inputs']] == [575.9199829101562, 560.5800170898438]


@pytest.mark.parametrize('missing', ['yield', 'fx', 'etf', 'duplicate', 'split'])
def test_missing_or_invalid_required_inputs_leave_whole_result_unavailable(monkeypatch, missing):
    market = deepcopy(load_json('event-market-observations'))
    quotes = deepcopy(load_json('event-etf-observations'))
    if missing in {'yield', 'fx'}:
        series = 'DGS10' if missing == 'yield' else 'DEXUSEU'
        market['observations'] = [r for r in market['observations'] if not (r['series'] == series and r['date'] == '2025-03-10')]
    else:
        q = next(q for q in quotes['observations'] if q['ticker'] == 'SPY' and q['date'] == '2025-03-10')
        if missing == 'etf': quotes['observations'].remove(q)
        if missing == 'duplicate': quotes['observations'].append(q.copy())
        if missing == 'split': q['split_events'] = [{'numerator': 2}]
    original = events.load_json
    monkeypatch.setattr(events, 'load_json', lambda name: {'event-market-observations': market, 'event-etf-observations': quotes}.get(name) or original(name))
    s = events.event_snapshot('march-2025')
    assert s['estimated_pnl_usd'] is s['end_nav_usd'] is None
    assert any(r['status'] == 'Unavailable' and r['pnl_usd'] is r['end_value_usd'] is None for r in s['positions'])
    assert s['coverage_count'] < 12


def test_only_three_windows_and_archived_api_outputs_remain_separate(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER', 'demo')
    app = importlib.import_module('metis.api.app').app
    with TestClient(app) as client:
        data = client.get('/api/workstation').json()
    assert [e['id'] for e in data['event_snapshots']] == list(EXPECTED)
    assert data['daily'] == workstation()['daily']
    assert data['daily']['total_pnl_usd'] == -282200
    assert workstation('2025-03-10')['daily']['total_pnl_usd'] == -560770
    with pytest.raises(ValueError): events.event_snapshot('new-window')


def test_causal_request_captures_reference_without_revaluing_archived_scenarios(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER', 'demo')
    app = importlib.import_module('metis.api.app').app
    base = dict(hypothesis='Recession fears', alternative='Inflation relief', common_rates_bp=-50)
    with TestClient(app) as client:
        old = client.post('/api/causal-exploration', json=base).json()
        result = client.post('/api/causal-exploration', json={**base, 'event_snapshot_id': 'cpi-2022'}).json()
        invalid = client.post('/api/causal-exploration', json={**base, 'event_snapshot_id': 'new-window'})
    assert invalid.status_code == 422
    assert result['context']['event_reference'] == events.event_snapshot('cpi-2022')
    assert result['context']['portfolio'] == old['context']['portfolio']
    assert result['context']['daily'] == old['context']['daily']
    assert result['exploration'] == old['exploration']


def test_mocked_meta_receives_qualified_event_provenance_not_observed_nav(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER', 'meta')
    monkeypatch.setenv('METIS_META_API_KEY', 'test-only')
    monkeypatch.setenv('METIS_META_BASE_URL', 'https://example.com/v1')
    monkeypatch.setenv('METIS_MODEL', 'test-only')
    request = CausalRequest(hypothesis='Recession fears', alternative='Inflation relief', event_snapshot_id='march-2025')
    reply = demo_exploration(request).model_dump_json()
    calls = []
    original = httpx.Client
    def handler(req):
        body = json.loads(req.content)
        text = json.dumps(body['messages'])
        assert 'event_reference' in text and 'march-2025' in text
        assert 'Hypothetical assumption' in text and 'Approximate input' in text
        assert 'not observed holdings/NAV' in text and 'do not mix their P&L' in text
        assert 'fred.stlouisfed.org' in text and 'query1.finance.yahoo.com' in text
        calls.append(body)
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': reply}}]})
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    from metis.reasoning.causal import explore
    result = explore(request)
    assert len(calls) == 1 and result['context']['event_reference']['estimated_pnl_usd'] == -482623.35
