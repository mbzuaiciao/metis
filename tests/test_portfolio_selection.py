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
        assert [p['id'] for p in selections] == ['current', 'candidate-a', 'candidate-b', 'candidate-c']
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
        assert [a['context']['scenario']['total_pnl_usd'] for a in answers] == [-4240000, -3985000, -4519000, -2290000]
        for answer, selection in zip(answers[1:], selections[1:]):
            assert answer['context']['portfolio']['selection']['id'] == selection['id']
            assert answer['context']['portfolio']['selection']['construction'] == selection['construction']
        legacy = client.post('/api/reasoning', json={'question': 'Explain legacy', 'investigation_scope': 'daily', 'investigation_date': '2025-03-10'}).json()
        historical = client.post('/api/reasoning', json={'question': 'Explain CPI', 'investigation_scope': 'historical'}).json()
        assert historical['context']['scenario']['total_pnl_usd'] == -1496577.2
        monkeypatch.setattr('metis.reasoning.harness.assemble_context', lambda *args: pytest.fail('Followup reloaded holdings'))
        for answer in [*answers, legacy, historical]:
            continued = client.post('/api/reasoning', json={'question': 'Continue', 'investigation_id': answer['investigation_id']})
            assert continued.status_code == 200
            assert continued.json()['context'] == answer['context']
            assert client.post('/api/reasoning', json={'question': 'Replace', 'investigation_id': answer['investigation_id'], 'portfolio_id': 'candidate-a'}).status_code == 422


@pytest.mark.parametrize('portfolio_id', ['candidate-a', 'candidate-b', 'candidate-c'])
def test_candidate_daily_and_invalid_selections_fail_without_substitution(portfolio_id):
    with TestClient(api.app) as client:
        daily = client.post('/api/reasoning', json={'question': 'Explain', 'investigation_scope': 'daily', 'portfolio_id': portfolio_id})
        assert daily.status_code == 200
        context = daily.json()['context']
        assert context['daily'] == context['scenario'] == workstation(portfolio_id=portfolio_id)['daily']
        for extra in [{'portfolio_id': 'unknown'}, {'portfolio_id': portfolio_id, 'investigation_scope': 'historical'},
                      {'portfolio_id': portfolio_id, 'investigation_scope': 'daily', 'investigation_date': '2025-03-10'}]:
            assert client.post('/api/reasoning', json={'question': 'Explain', **extra}).status_code == 422
        assert client.post('/api/scenario?portfolio_id=unknown', json={}).status_code == 422


@pytest.mark.parametrize('portfolio_id,changed_rows,dv01,hy_cs01,equity_delta,daily_pnl', [
    ('current', {}, 50100, 5200, 26000000, -282200),
    ('candidate-a', {
        'HY-US': {'market_value_usd': 6000000, 'notional_usd': 6000000, 'dv01_usd_per_bp': 2400, 'cs01_usd_per_bp': 2100},
        'HY-EU': {'market_value_usd': 4500000, 'notional_usd': 4500000, 'dv01_usd_per_bp': 1800, 'cs01_usd_per_bp': 1800},
        'CASH': {'market_value_usd': 7500000, 'notional_usd': 7500000},
    }, 48700, 3900, 26000000, -250700),
    ('candidate-b', {
        'UST10': {'market_value_usd': 9000000, 'notional_usd': 9000000, 'dv01_usd_per_bp': 7200},
        'UST2': {'market_value_usd': 19000000, 'notional_usd': 19000000, 'dv01_usd_per_bp': 3420},
    }, 44520, 5200, 26000000, -338000),
    ('candidate-c', {
        'EQ-US': {'market_value_usd': 8500000, 'notional_usd': 8500000, 'equity_delta_usd': 8500000},
        'EQ-DM': {'market_value_usd': 4500000, 'notional_usd': 4500000, 'equity_delta_usd': 4500000},
        'CASH': {'market_value_usd': 17000000, 'notional_usd': 17000000},
    }, 50100, 5200, 13000000, -87200),
])
def test_four_independent_constructions_reconcile_all_holdings_and_exposures(portfolio_id, changed_rows, dv01, hy_cs01, equity_delta, daily_pnl):
    original = load_positions().set_index('id').to_dict(orient='index')
    expected = deepcopy(original)
    for id, fields in changed_rows.items():
        expected[id].update(fields)
    frame = load_positions(portfolio_id=portfolio_id)
    # Entire rows must match: B/C cannot inherit A's HY reduction, and swaps remain unchanged.
    assert frame.set_index('id').to_dict(orient='index') == expected
    assert len(frame) == 12
    assert frame.market_value_usd.sum() == 100000000
    data = workstation(portfolio_id=portfolio_id)
    assert data['exposures'] == {
        'dv01_usd_per_bp': dv01, 'cs01_usd_per_bp': 12600 + hy_cs01,
        'ig_cs01_usd_per_bp': 12600, 'hy_cs01_usd_per_bp': hy_cs01,
        'equity_delta_usd': equity_delta, 'fx_delta_usd': 12000000,
    }
    assert data['market'] == workstation()['market']
    assert data['nav_usd'] == sum(row['market_value_usd'] for row in data['allocation']) == 100000000
    assert data['daily']['total_pnl_usd'] == daily_pnl == sum(data['daily']['by_factor'].values())
    assert data['opening_nav_usd'] + daily_pnl == data['nav_usd']
    assert sum(row['pnl_usd'] for row in data['daily']['positions']) == daily_pnl
    assert load_positions().set_index('id').to_dict(orient='index') == original


@pytest.mark.parametrize('preset,expected', [
    ('inflation-2022', {
        'current': (-269037, -93600, -1123200, -175200, -1661037),
        'candidate-a': (-261519, -70200, -1123200, -175200, -1630119),
        'candidate-b': (-239072.4, -93600, -1123200, -175200, -1631072.4),
        'candidate-c': (-269037, -93600, -561600, -175200, -1099437),
    }),
    ('covid-2020', {
        'current': (2505000, -5900000, -6500000, -360000, -10255000),
        'candidate-a': (2435000, -5055000, -6500000, -360000, -9480000),
        'candidate-b': (2226000, -5900000, -6500000, -360000, -10534000),
        'candidate-c': (2505000, -5900000, -3250000, -360000, -7005000),
    }),
])
def test_four_portfolio_common_shocks_against_independent_full_factor_oracles(preset, expected):
    shocks = next(p['shocks'] for p in load_json('historical-stress-presets') if p['id'] == preset)
    results = []
    with TestClient(api.app) as client:
        for portfolio_id, (rates, credit, equity, fx, total) in expected.items():
            response = client.post('/api/scenario?portfolio_id=' + portfolio_id, json=shocks)
            assert response.status_code == 200, response.text
            result = response.json()
            assert result['shocks'] == shocks
            assert result['by_factor'] == {'rates_pnl': rates, 'credit_pnl': credit, 'equity_pnl': equity, 'fx_pnl': fx}
            assert result['total_pnl_usd'] == total == pytest.approx(sum(result['by_factor'].values()))
            assert result['pnl_pct_nav'] == pytest.approx(total / 100000000 * 100)
            assert sum(p['pnl_usd'] for p in result['positions']) == pytest.approx(total)
            for position in result['positions']:
                assert position['pnl_usd'] == pytest.approx(sum(position[f] for f in result['by_factor']))
            results.append(result)
    assert len({r['total_pnl_usd'] for r in results}) == 4
    # Less duration means smaller losses on rate rises, and smaller gains on rate falls.
    if shocks['rates_bp'] > 0:
        assert results[2]['by_factor']['rates_pnl'] > results[0]['by_factor']['rates_pnl']
    else:
        assert results[2]['by_factor']['rates_pnl'] < results[0]['by_factor']['rates_pnl']


def test_shorter_government_sleeve_improves_rate_only_selloff_without_removing_swap_risk():
    current = calculate(load_positions(), Shocks(rates_bp=100))
    shorter = calculate(load_positions(portfolio_id='candidate-b'), Shocks(rates_bp=100))
    assert current['total_pnl_usd'] == -5010000
    assert shorter['total_pnl_usd'] == -4452000
    assert shorter['by_factor']['rates_pnl'] == shorter['total_pnl_usd']
    assert {p['id']: p['pnl_usd'] for p in shorter['positions'] if p['id'].startswith('IRS-')} == {
        'IRS-R': -2450000, 'IRS-P': 1000000,
    }
