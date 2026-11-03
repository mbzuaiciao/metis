"""Event-inspired shocks use the existing engine; legacy research oracles stay intact."""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from metis.api.app import app
from metis.analytics.engine import Shocks, load_json


@pytest.mark.parametrize('index,factors,total', [
    (0, [2505000, -5900000, -6500000, -360000], -10255000),
    (1, [-269037, -93600, -1123200, -175200], -1661037),
    (2, [751500, -397000, -260000, 96000], 190500),
    (3, [250500, -167000, -780000, 60000], -636500),
])
def test_event_presets_reconcile_current_portfolio(index, factors, total):
    client = TestClient(app)
    data = client.get('/api/workstation').json()
    presets = data['historical_stress_presets']
    assert len(presets) == 4
    preset = presets[index]
    assert date.fromisoformat(preset['start_date']).weekday() < 5
    assert date.fromisoformat(preset['end_date']).weekday() < 5
    assert preset['start_date'] < preset['end_date']
    assert preset['basis'] and preset['window'] and preset['source_url'].startswith('https://')
    assert set(preset['shocks']) == set(Shocks.model_fields)
    response = client.post('/api/scenario', json=preset['shocks'])
    assert response.status_code == 200
    result = response.json()
    assert list(result['by_factor'].values()) == factors
    assert result['total_pnl_usd'] == total
    assert result['pnl_pct_nav'] == total / data['nav_usd'] * 100
    assert len(result['positions']) == 12
    assert sum(p['pnl_usd'] for p in result['positions']) == sum(factors) == total
    for p in result['positions']:
        s = preset['shocks']
        spread = s['ig_bp'] if p['spread_bucket'] == 'ig' else s['hy_bp'] if p['spread_bucket'] == 'hy' else 0
        assert p['rates_pnl'] == round(-p['dv01_usd_per_bp'] * s['rates_bp'], 2)
        assert p['credit_pnl'] == round(-p['cs01_usd_per_bp'] * spread, 2)
        assert p['equity_pnl'] == round(p['equity_delta_usd'] * s['equity_pct'] / 100, 2)
        assert p['fx_pnl'] == round(p['fx_delta_usd'] * s['fx_pct'] / 100, 2)
    assert data['scenarios'] == load_json('scenarios')


def test_cpi_reuses_cached_observations_without_changing_archive():
    observations = load_json('historical-20220913')['observations']
    shocks = load_json('historical-stress-presets')[1]['shocks']
    assert shocks['rates_bp'] == pytest.approx((observations['ust10']['current_yield_pct'] - observations['ust10']['previous_yield_pct']) * 100)
    assert shocks['ig_bp'] == observations['ig_spread']['change_bp']
    assert shocks['hy_bp'] == observations['hy_spread']['change_bp']
    assert shocks['equity_pct'] == observations['sp500']['reported_return_pct']
    assert shocks['fx_pct'] == observations['eurusd']['reported_return_pct']
