"""Illustrative candidate accounting, common shocks and captured scope; no live inference."""
from copy import deepcopy
import importlib

from fastapi.testclient import TestClient
import pytest

from metis.analytics.engine import Shocks, calculate, load_json, load_positions, workstation
from metis.reasoning.followup import EvidenceSnapshots
from metis.reasoning.harness import DemoProvider

api = importlib.import_module('metis.api.app')


@pytest.fixture(autouse=True)
def demo(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER', 'demo')
    monkeypatch.setattr(api, 'evidence_snapshots', EvidenceSnapshots())


def test_candidate_accounting_and_exact_proportional_exposures():
    current = load_positions().set_index('id')
    candidate = load_positions(portfolio_id='candidate-a').set_index('id')
    assert current.market_value_usd.sum() == candidate.market_value_usd.sum() == 100_000_000
    for id in ['HY-US', 'HY-EU']:
        for field in ['market_value_usd', 'notional_usd', 'dv01_usd_per_bp', 'cs01_usd_per_bp']:
            assert candidate.loc[id, field] == current.loc[id, field] * 0.75
    assert candidate.loc['CASH', 'market_value_usd'] == candidate.loc['CASH', 'notional_usd'] == 7_500_000
    for id in current.index.difference(['HY-US', 'HY-EU', 'CASH']):
        assert candidate.loc[id].equals(current.loc[id])
    assert load_positions().set_index('id').equals(current)
    assert workstation('2025-03-10')['daily']['total_pnl_usd'] == -560770


@pytest.mark.parametrize('preset,current_total,candidate_total,rates,credit', [
    ('covid-2020', -10255000, -9480000, 2435000, -5055000),
    ('inflation-2022', -1661037, -1630119, -261519, -70200),
    ('banking-2023', 190500, 221500, 730500, -345000),
    ('yen-2024', -636500, -617500, 243500, -141000),
])
def test_common_historical_shocks_have_independent_factor_and_total_oracles(preset, current_total, candidate_total, rates, credit):
    presets = load_json('historical-stress-presets')
    shocks = next(p['shocks'] for p in presets if p['id'] == preset)
    with TestClient(api.app) as client:
        current = client.post('/api/scenario', json=shocks).json()
        candidate = client.post('/api/scenario?portfolio_id=candidate-a', json=shocks).json()
    assert current == calculate(load_positions(), Shocks(**shocks))
    assert current['total_pnl_usd'] == current_total
    assert candidate['shocks'] == current['shocks']
    assert candidate['by_factor']['rates_pnl'] == rates
    assert candidate['by_factor']['credit_pnl'] == credit
    assert candidate['total_pnl_usd'] == candidate_total == sum(candidate['by_factor'].values())
    assert candidate_total == sum(p['pnl_usd'] for p in candidate['positions'])
    for factor in ['equity_pnl', 'fx_pnl']:
        assert candidate['by_factor'][factor] == current['by_factor'][factor]


def test_provider_receives_selected_calculation_and_followups_retain_each_context(monkeypatch):
    seen = []
    interpret = DemoProvider.interpret
    def inspect(self, request, context):
        seen.append(deepcopy(context))
        return interpret(self, request, context)
    monkeypatch.setattr(DemoProvider, 'interpret', inspect)
    shocks = {'rates_bp': -50, 'ig_bp': 75, 'hy_bp': 250, 'equity_pct': -15, 'fx_pct': -5}
    with TestClient(api.app) as client:
        selections = client.get('/api/workstation').json()['portfolio_selections']
        assert [p['id'] for p in selections] == ['current', 'candidate-a']
        assert {p['reference_date'] for p in selections} == {'2026-10-30'}
        answers = []
        for selection in selections:
            response = client.post('/api/reasoning', json={'question': 'Interpret selected stress',
                'investigation_scope': 'scenario', 'portfolio_id': selection['id'], 'shocks': shocks})
            assert response.status_code == 200, response.text
            answer = response.json()
            context = answer['context']
            assert context == seen[-1]
            assert context['portfolio']['positions'] == selection['snapshot']['positions']
            assert context['portfolio']['exposures'] == selection['snapshot']['exposures']
            assert context['scenario'] == client.post('/api/scenario?portfolio_id=' + selection['id'], json=shocks).json()
            assert context['market']['as_of'] == '2026-10-30'
            for alternative in context['alternative_scenarios']:
                assert alternative['total_pnl_usd'] == calculate(load_positions(portfolio_id=selection['id']), Shocks(**alternative['shocks']))['total_pnl_usd']
            answers.append(answer)
        assert [a['context']['scenario']['total_pnl_usd'] for a in answers] == [-4240000, -3985000]
        assert answers[1]['context']['portfolio']['selection']['id'] == 'candidate-a'
        legacy = client.post('/api/reasoning', json={'question': 'Explain legacy', 'investigation_scope': 'daily', 'investigation_date': '2025-03-10'}).json()
        historical = client.post('/api/reasoning', json={'question': 'Explain CPI', 'investigation_scope': 'historical'}).json()
        assert historical['context']['scenario']['total_pnl_usd'] == -1496577.2
        monkeypatch.setattr('metis.reasoning.harness.assemble_context', lambda *args: pytest.fail('Followup reloaded holdings'))
        for answer in [*answers, legacy, historical]:
            continued = client.post('/api/reasoning', json={'question': 'Continue', 'investigation_id': answer['investigation_id']})
            assert continued.status_code == 200
            assert continued.json()['context'] == answer['context']
            assert client.post('/api/reasoning', json={'question': 'Replace', 'investigation_id': answer['investigation_id'], 'portfolio_id': 'candidate-a'}).status_code == 422


def test_candidate_daily_and_invalid_selections_fail_without_substitution():
    with TestClient(api.app) as client:
        daily = client.post('/api/reasoning', json={'question': 'Explain', 'investigation_scope': 'daily', 'portfolio_id': 'candidate-a'})
        assert daily.status_code == 200
        context = daily.json()['context']
        assert context['daily'] == context['scenario'] == workstation(portfolio_id='candidate-a')['daily']
        for extra in [{'portfolio_id': 'unknown'}, {'portfolio_id': 'candidate-a', 'investigation_scope': 'historical'},
                      {'portfolio_id': 'candidate-a', 'investigation_scope': 'daily', 'investigation_date': '2025-03-10'}]:
            assert client.post('/api/reasoning', json={'question': 'Explain', **extra}).status_code == 422
        assert client.post('/api/scenario?portfolio_id=unknown', json={}).status_code == 422
