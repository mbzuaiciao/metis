"""Offline financial oracles for retrieved ETF closes, coverage and archive isolation."""
from copy import deepcopy
import importlib

from fastapi.testclient import TestClient
import pytest

from metis.analytics import etf
from metis.analytics.engine import load_positions, workstation, load_json


def test_allocation_reconciles_without_invented_units_marks_or_risk():
    result = etf.portfolio()
    legacy = load_positions('2026-10-30').set_index('id')
    assert result['allocation_nav_usd'] == 100_000_000
    assert len(result['positions']) == 12
    assert sum(p['allocation_usd'] for p in result['positions']) == result['allocation_nav_usd']
    assert sum(p['weight_pct'] for p in result['positions']) == pytest.approx(100)
    funds = [p for p in result['positions'] if p['instrument'] == 'ETF']
    assert [p['id'] for p in funds] == ['LQD', 'EUIG', 'HYG', 'EUHY', 'SPY', 'HEFA']
    for p in result['positions']:
        assert p['allocation_usd'] == legacy.loc[p.get('legacy_id', p['id']), 'market_value_usd']
        assert p['observed_market_value_usd'] is p['units'] is p['dv01_usd_per_bp'] is p['cs01_usd_per_bp'] is None
    assert sum(p['allocation_usd'] for p in funds) == 64_000_000
    assert [p['allocation_usd'] for p in funds] == [15e6, 9e6, 8e6, 6e6, 17e6, 9e6]
    assert {p['id'] for p in result['positions'] if 'audit' in p} == {'UST10', 'UST2', 'IRS-R', 'IRS-P', 'FX-EUR', 'CASH'}
    for p in result['positions']:
        if 'audit' in p:
            assert p['audit']['minimum_data'] and p['audit']['recommendation']


def test_known_september_closes_partial_coverage_and_no_cross_region_proxy():
    result = etf.historical_prices('2022-09-12', '2022-09-13')
    rows = {p['id']: p for p in result['positions']}
    # Independently specified source observations, not old basket sensitivity/OAS calculations.
    assert rows['SPY']['start_observation']['close'] == pytest.approx(410.9700012207031)
    assert rows['SPY']['end_observation']['close'] == pytest.approx(393.1000061035156)
    assert rows['SPY']['price_return_pct'] == pytest.approx(-4.348248062901982)
    assert rows['SPY']['price_pnl_usd'] == -739202.17
    assert rows['LQD']['price_pnl_usd'] == -108192.91
    assert rows['HYG']['price_pnl_usd'] == -182009.82
    assert rows['HEFA']['price_pnl_usd'] == -193489.15
    assert result['covered_price_pnl_usd'] == -1222894.05
    assert result['covered_allocation_usd'] == 49_000_000
    for ticker, reason in [('EUIG', 'Nov 6, 2025'), ('EUHY', 'Nov 3, 2025')]:
        assert reason in rows[ticker]['reason']
        assert rows[ticker]['price_pnl_usd'] is rows[ticker]['price_return_pct'] is None
        assert rows[ticker]['start_observation'] is None
    assert result['portfolio_pnl_usd'] is result['total_return_pct'] is None


def test_october_price_leg_reconciles_and_is_separate_from_fictional_demo():
    result = etf.historical_prices('2026-10-29', '2026-10-30')
    covered = [p for p in result['positions'] if p['status'] == 'available']
    assert len(covered) == 6
    assert result['covered_allocation_usd'] == 64_000_000
    assert result['covered_price_pnl_usd'] == -417244.37
    assert sum(p['price_pnl_usd'] for p in covered) == pytest.approx(-417244.37)
    assert result['portfolio_pnl_usd'] is None
    assert workstation()['daily']['total_pnl_usd'] == -282200
    assert workstation('2025-03-10')['daily']['total_pnl_usd'] == -560770
    for p in covered:
        assert p['total_return_pct'] is None
        assert p['start_observation']['currency'] == 'USD'
        assert p['start_observation']['price_basis'] == 'unadjusted_close'
        assert p['start_observation']['source_url'].startswith('https://query1.finance.yahoo.com/')
        assert p['end_observation']['bar_timestamp_utc']
        assert p['dv01_usd_per_bp'] is p['cs01_usd_per_bp'] is None
        assert 'rates_pnl' not in p  # No rate/spread legs added to an ETF's full price move.


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'currency', 'basis', 'split', 'zero', 'nan', 'source'])
def test_incompatible_missing_observations_fail_closed(monkeypatch, change):
    quotes = deepcopy(load_json('etf-observations'))
    q = next(q for q in quotes['observations'] if q['ticker'] == 'LQD' and q['date'] == '2026-10-30')
    if change == 'missing': quotes['observations'].remove(q)
    elif change == 'duplicate': quotes['observations'].append(deepcopy(q))
    elif change == 'currency': q['currency'] = 'EUR'
    elif change == 'basis': q['price_basis'] = 'adjusted_close'
    elif change == 'split': q['split_events'] = [{'numerator': 2, 'denominator': 1}]
    elif change == 'zero': q['close'] = 0
    elif change == 'nan': q['close'] = float('nan')
    elif change == 'source': q['source_url'] = ''
    original = etf.load_json
    monkeypatch.setattr(etf, 'load_json', lambda name: quotes if name == 'etf-observations' else original(name))
    result = etf.historical_prices('2026-10-29', '2026-10-30')
    row = next(p for p in result['positions'] if p['id'] == 'LQD')
    assert row['status'] == 'unavailable' and row['price_pnl_usd'] is None
    assert result['covered_allocation_usd'] == 49_000_000


def test_missing_period_and_unverified_long_intervals_are_not_interpolated():
    for start, end in [('2022-09-13', '2022-09-14'), ('2022-09-12', '2026-10-30')]:
        result = etf.historical_prices(start, end)
        assert result['covered_price_pnl_usd'] is None
        assert result['covered_allocation_usd'] == 0
    with pytest.raises(ValueError): etf.historical_prices('2026-10-30', '2026-10-29')


def test_api_keeps_observed_etf_path_separate_from_archived_synthetic_inputs():
    app = importlib.import_module('metis.api.app').app
    with TestClient(app) as client:
        result = client.get('/api/workstation').json()
    assert result['etf_portfolio'] == etf.portfolio()
    assert result['etf_history'][0] == etf.historical_prices('2026-10-29', '2026-10-30')
    assert result['positions'] == workstation()['positions']
    assert result['daily']['total_pnl_usd'] == -282200
    assert result['exposures']['dv01_usd_per_bp'] == 50100
