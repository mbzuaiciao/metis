"""Synthetic date selection and reconciliation; no live inference/retrieval."""
from copy import deepcopy
import importlib

from fastapi.testclient import TestClient
import pytest

from metis.analytics.engine import Shocks, calculate, load_positions, workstation
from metis.reasoning.followup import EvidenceSnapshots
from metis.reasoning.harness import DemoProvider

api = importlib.import_module('metis.api.app')


@pytest.fixture(autouse=True)
def demo(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER', 'demo')
    monkeypatch.setattr(api, 'evidence_snapshots', EvidenceSnapshots())


def test_default_selection_agrees_with_app_wide_workstation():
    with TestClient(api.app) as client:
        data = client.get('/api/workstation').json()
    assert data['investigation']['default_date'] == '2026-10-30'
    snapshots = {s['market']['as_of']: s for s in data['investigation']['snapshots']}
    assert set(snapshots) == {'2026-10-30', '2025-03-10'}
    assert snapshots['2026-10-30'] == workstation()
    assert snapshots['2025-03-10'] == workstation('2025-03-10')
    assert data['market']['as_of'] == '2026-10-30'
    assert 'not sourced market observations' in data['investigation']['disclosure']
    assert snapshots['2026-10-30']['positions'] == data['positions']
    assert snapshots['2026-10-30']['market'] == data['market']


@pytest.mark.parametrize('date,prior,total,factors', [
    ('2026-10-30', '2026-10-29', -282200,
     {'rates_pnl': 501000, 'credit_pnl': -333200, 'equity_pnl': -390000, 'fx_pnl': -60000}),
    ('2025-03-10', '2025-03-07', -560770,
     {'rates_pnl': 412480, 'credit_pnl': -407250, 'equity_pnl': -506000, 'fx_pnl': -60000}),
])
def test_selected_fixture_reconciles_levels_shocks_positions_and_nav(date, prior, total, factors):
    data = workstation(date)
    market, daily = data['market'], data['daily']
    assert market['as_of'] == date and market['previous_date'] == prior
    assert 'synthetic' in market['label']
    for rate in market['yields']:
        assert (rate['current_pct'] - rate['previous_pct']) * 100 == pytest.approx(daily['shocks']['rates_bp'])
    for spread in market['credit']:
        assert spread['change_bp'] == daily['shocks'][spread['bucket'] + '_bp']
    assert all(e['change_pct'] == daily['shocks']['equity_pct'] for e in market['equities'])
    assert market['fx'][0]['change_pct'] == daily['shocks']['fx_pct']
    assert daily['total_pnl_usd'] == total == sum(daily['by_factor'].values())
    assert daily['by_factor'] == factors
    assert total == sum(p['pnl_usd'] for p in daily['positions'])
    for position in daily['positions']:
        assert position['pnl_usd'] == sum(position[f] for f in factors)
    assert data['opening_nav_usd'] + total == data['nav_usd']
    assert sum(p['market_value_usd'] for p in daily['positions']) == data['nav_usd']


@pytest.mark.parametrize('date', [None, '2026-10-30', '2025-03-10'])
def test_daily_request_selects_whole_context_and_alternatives_before_provider(monkeypatch, date):
    seen = []
    interpret = DemoProvider.interpret
    def inspect(self, request, context):
        seen.append(deepcopy(context))
        return interpret(self, request, context)
    monkeypatch.setattr(DemoProvider, 'interpret', inspect)
    expected_date = date or '2026-10-30'
    data = workstation(expected_date)
    with TestClient(api.app) as client:
        response = client.post('/api/reasoning', json={
            'question': 'Explain the illustrative daily loss', 'investigation_scope': 'daily',
            'investigation_date': date, 'shocks': {'rates_bp': 100}})
    assert response.status_code == 200, response.text
    context = response.json()['context']
    assert context == seen[0]
    assert context['market'] == data['market']
    assert context['portfolio']['positions'] == data['positions']
    assert context['portfolio']['exposures'] == data['exposures']
    assert context['daily'] == context['scenario'] == data['daily']
    for alternative in context['alternative_scenarios']:
        calculated = calculate(load_positions(expected_date), Shocks(**alternative['shocks']))
        assert alternative['total_pnl_usd'] == calculated['total_pnl_usd']


def test_omitted_date_defaults_to_october_and_followups_remain_isolated(monkeypatch):
    with TestClient(api.app) as client:
        answers = []
        for extra in ({}, {'investigation_date': '2025-03-10'}):
            response = client.post('/api/reasoning', json={
                'question': 'Explain the illustrative daily loss', 'investigation_scope': 'daily', **extra})
            assert response.status_code == 200
            answers.append(response.json())
        assert [a['context']['market']['as_of'] for a in answers] == ['2026-10-30', '2025-03-10']
        monkeypatch.setattr(api, 'workstation', lambda *_: pytest.fail('Followup reloaded data'))
        monkeypatch.setattr('metis.reasoning.harness.assemble_context', lambda *_: pytest.fail('Followup rebuilt context'))
        for answer in answers:
            followup = {'question': 'Explain further', 'investigation_id': answer['investigation_id']}
            assert client.post('/api/reasoning', json=followup).json()['context'] == answer['context']
            assert client.post('/api/reasoning', json={**followup, 'investigation_date': '2026-10-30'}).status_code == 422


@pytest.mark.parametrize('date', ['2026-10-29', '2025-03-07', '2022-09-13', '../../market', 'invalid', ''])
def test_unsupported_daily_dates_fail_before_inference_or_capture(monkeypatch, date):
    monkeypatch.setattr(api, 'reason', lambda *_: pytest.fail('Unavailable data reached provider'))
    monkeypatch.setattr(api.evidence_snapshots, 'capture', lambda *_: pytest.fail('Unavailable data captured'))
    with TestClient(api.app) as client:
        response = client.post('/api/reasoning', json={
            'question': 'Explain', 'investigation_scope': 'daily', 'investigation_date': date})
    assert response.status_code == 422
    assert 'interpretation' not in response.json()
    if date[:1].isdigit():
        assert 'no data was substituted' in response.json()['detail']


@pytest.mark.parametrize('scope', ['historical', 'scenario'])
def test_daily_date_cannot_silently_change_other_scopes(scope):
    with TestClient(api.app) as client:
        response = client.post('/api/reasoning', json={
            'question': 'Explain', 'investigation_scope': scope, 'investigation_date': '2026-10-30'})
    assert response.status_code == 422


def test_all_default_paths_share_october_inputs_and_calculations():
    from metis.analytics.engine import exposures
    from metis.reasoning.harness import assemble_context
    with TestClient(api.app) as client:
        data = client.get('/api/workstation').json()
        assert data['market']['as_of'] == '2026-10-30'
        assert data['market']['previous_date'] == '2026-10-29'
        frame = load_positions()
        assert frame.to_dict(orient='records') == load_positions('2026-10-30').to_dict(orient='records')
        assert data['exposures'] == exposures(frame) == {
            'dv01_usd_per_bp': 50100, 'cs01_usd_per_bp': 17800,
            'ig_cs01_usd_per_bp': 12600, 'hy_cs01_usd_per_bp': 5200,
            'equity_delta_usd': 26000000, 'fx_delta_usd': 12000000}
        daily = client.post('/api/scenario', json=data['daily']['shocks']).json()
        assert daily == data['daily'] == workstation()['daily']
        default = client.post('/api/reasoning', json={
            'question': 'Explain daily P&L', 'investigation_scope': 'daily'}).json()
        assert default['context']['market'] == data['market']
        assert default['context']['portfolio']['positions'] == data['positions']
        assert default['context']['daily'] == default['context']['scenario'] == daily
        preset = data['scenarios'][3]['shocks']
        stress = client.post('/api/scenario', json=preset).json()
        assert stress == calculate(frame, Shocks(**preset))
        assert stress['total_pnl_usd'] == -4240000
        assert stress['by_factor'] == {
            'rates_pnl': 2505000, 'credit_pnl': -2245000,
            'equity_pnl': -3900000, 'fx_pnl': -600000}
        context = assemble_context(Shocks(**preset))
        assert context['portfolio'] == default['context']['portfolio']
        assert context['market'] == data['market']
        assert context['daily'] == daily and context['scenario'] == stress
        reasoning = client.post('/api/reasoning', json={
            'question': 'Interpret stress', 'investigation_scope': 'scenario', 'shocks': preset}).json()
        assert reasoning['context']['scenario'] == stress
        causal = client.post('/api/causal-exploration', json={
            'hypothesis': 'Recession fears', 'alternative': 'Inflation relief'}).json()
        assert causal['context']['portfolio'] == context['portfolio']
        assert causal['context']['market'] == {k: v for k, v in data['market'].items() if k != 'commentary'}
        assert causal['context']['daily'] == daily
        for mechanism in causal['exploration']['mechanisms']:
            shocks = mechanism['proposed_shocks']
            assert client.post('/api/scenario', json=shocks).json() == calculate(frame, Shocks(**shocks))
        # Selecting a legacy daily investigation never changes subsequent default stress/causal inputs.
        legacy = client.post('/api/reasoning', json={
            'question': 'Explain', 'investigation_scope': 'daily', 'investigation_date': '2025-03-10'}).json()
        assert legacy['context']['daily']['total_pnl_usd'] == -560770
        assert client.post('/api/scenario', json=preset).json() == stress
        for answer in [default, legacy, reasoning]:
            follow = client.post('/api/reasoning', json={
                'question': 'Continue', 'investigation_id': answer['investigation_id']}).json()
            assert follow['context'] == answer['context']
