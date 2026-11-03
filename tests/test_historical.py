"""Historical production workflow checks; no live inference or causal validation."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
import httpx
import pytest

from metis.analytics.engine import workstation, calculate, load_positions, Shocks
from metis.reasoning.followup import EvidenceSnapshots
from metis.reasoning.harness import ReasoningRequest
from metis.reasoning.historical import historical_context, historical_demo

api = importlib.import_module('metis.api.app')


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER', 'demo')
    monkeypatch.setattr(api, 'evidence_snapshots', EvidenceSnapshots())


def test_historical_case_reuses_sources_engine_results_and_preserves_original_dataset(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    original = json.loads((root / 'research/historical-macro-20220913-inputs.json').read_text())
    updated = json.loads((root / 'backend/metis/data/historical-20220913.json').read_text())
    for key in ('episode', 'previous_date', 'as_of', 'macro_context'):
        assert updated[key] == original[key]
    for key in ('ust10', 'ust2', 'sp500', 'eurusd'):
        assert updated['observations'][key] == original['observations'][key]
    before = workstation()
    with TestClient(api.app) as client:
        response = client.post('/api/reasoning', json={'question': 'Explain the CPI day',
            'investigation_scope': 'historical', 'shocks': {'rates_bp': -100, 'ig_bp': 200}})
        assert response.status_code == 200, response.text
        answer = response.json()
        context = answer['context']
        assert context['market']['as_of'] == '2022-09-13'
        assert context['scenario']['shocks']['rates_bp'] == 5.37  # Server-owned inputs override client shocks.
        assert context['scenario']['total_pnl_usd'] == pytest.approx(-1496577.2)
        assert context['scenario']['by_factor'] == {'rates_pnl': -276877.2, 'credit_pnl': -80100, 'equity_pnl': -993600, 'fx_pnl': -146000}
        assert context['historical']['observations']['ig_spread']['change_bp'] == 0
        assert context['historical']['observations']['hy_spread']['change_bp'] == 18
        assert context['historical']['credit_spreads_included'] is True
        assert context['macro_context']['facts'] and len(context['portfolio']['positions']) == 12
        hypotheses = answer['interpretation']['hypotheses']
        assert len(hypotheses) == len({h['title'] for h in hypotheses}) == 3
        for h in hypotheses:
            assert all(h[key] for key in ['mechanism', 'consistent_evidence', 'portfolio_implications', 'uncertainty', 'available_checks', 'additional_evidence'])
        assert answer['verification'] == []  # No misleading historical period mappings.
        assert workstation() == before
        assert before['daily']['total_pnl_usd'] == -560770
        assert before['market']['as_of'] == '2025-03-10'
        monkeypatch.setattr('metis.reasoning.historical.historical_context', lambda: pytest.fail('Follow-up refreshed historical inputs'))
        follow = client.post('/api/reasoning', json={'question': 'What could distinguish them?', 'investigation_id': answer['investigation_id']})
        assert follow.status_code == 200
        assert follow.json()['context'] == context
        assert follow.json()['interpretation']['hypotheses'] == hypotheses


def test_meta_wire_has_three_joint_inputs_and_exactly_three_with_portfolio_field(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER', 'meta')
    monkeypatch.setenv('METIS_MODEL', 'test-only')
    monkeypatch.setenv('METIS_META_API_KEY', 'test-only')
    monkeypatch.setenv('METIS_META_BASE_URL', 'https://example.com/v1')
    seen = []
    invalid = False
    def handler(request):
        body = json.loads(request.content)
        seen.append(body)
        context = json.loads(body['messages'][-1]['content'])['context']
        assert context['portfolio']['exposures']['dv01_usd_per_bp'] == 51560
        assert context['historical']['observations']['sp500']['reported_return_pct'] == -4.32
        assert context['macro_context']['facts'][0]['source'] == 'bls'
        assert context['scenario']['shocks']['hy_bp'] == 18
        assert context['scenario']['by_factor']['credit_pnl'] == -80100
        assert context['scenario']['total_pnl_usd'] == pytest.approx(-1496577.2)
        assert context['historical']['observations']['ig_spread']['previous_spread_pct'] == 1.46
        assert context['historical']['observations']['hy_spread']['current_spread_pct'] == 4.68
        assert len(context['historical']['credit_proxy_mappings']) == 4
        assert '2025-03-10' not in json.dumps(context)
        schema = body['response_format']['json_schema']['schema']
        assert schema['properties']['hypotheses']['minItems'] == schema['properties']['hypotheses']['maxItems'] == 3
        assert 'portfolio_implications' in schema['$defs']['HistoricalHypothesis']['required']
        assert set(schema['required']) == set(schema['properties'])
        result = historical_demo(context).model_dump()
        if invalid:
            result['hypotheses'].pop()
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(result)}}]})
    original = httpx.Client
    monkeypatch.setattr(httpx, 'Client', lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    with TestClient(api.app) as client:
        payload = {'question': 'Explain historical moves', 'investigation_scope': 'historical'}
        first = client.post('/api/reasoning', json=payload)
        assert first.status_code == 200, first.text
        history = [{'role': 'user', 'content': 'Earlier historical question'}]
        follow = client.post('/api/reasoning', json={'question': 'Distinguish the mechanisms',
            'investigation_id': first.json()['investigation_id'], 'history': history})
        assert follow.status_code == 200
        assert seen[1]['messages'][1:-1] == history
        assert json.loads(seen[0]['messages'][-1]['content'])['context'] == json.loads(seen[1]['messages'][-1]['content'])['context']
        invalid = True
        failure = client.post('/api/reasoning', json=payload)
        assert failure.status_code == 502 and 'schema_validation' in failure.json()['detail']
        assert 'No demonstration fallback' in failure.json()['detail']
        assert len(seen) == 3  # No retry or fallback.


def test_credit_units_explicit_mapping_and_reconciliation():
    context = historical_context()
    obs = context['historical']['observations']
    for bucket, before, after, change in [('ig', 1.46, 1.46, 0), ('hy', 4.50, 4.68, 18)]:
        spread = obs[bucket + '_spread']
        assert spread['unit'] == 'Percent'
        assert spread['previous_spread_pct'] == before
        assert spread['current_spread_pct'] == after
        assert spread['previous_spread_bp'] == before * 100
        assert spread['current_spread_bp'] == after * 100
        assert spread['change_bp'] == pytest.approx((after - before) * 100) == change
        source = context['historical']['sources'][spread['source']]
        assert source['verified_on'] == '2026-11-03'
        assert source['url'].startswith('https://equibles.com/economicdata/')
    result = context['scenario']
    prior = calculate(load_positions(), Shocks(rates_bp=5.37, equity_pct=-4.32, fx_pct=-1.46))
    positions = {p['id']: p for p in result['positions']}
    expected = {'IG-US': ('ig', 6300, 0, -37590), 'IG-EU': ('ig', 5200, 0, -30072),
                'HY-US': ('hy', 2450, -44100, -59136), 'HY-EU': ('hy', 2000, -36000, -46740)}
    mappings = {m['position_id']: m for m in context['historical']['credit_proxy_mappings']}
    assert set(mappings) == set(expected)
    for pid, (bucket, cs01, credit_pnl, net_pnl) in expected.items():
        p = positions[pid]
        assert p['instrument'] == 'Cash bond basket'
        assert p['market_value_usd'] > 0 and p['notional_usd'] > 0
        assert p['spread_bucket'] == mappings[pid]['spread_bucket'] == bucket
        assert p['cs01_usd_per_bp'] == cs01 > 0
        assert p['credit_pnl'] == credit_pnl
        assert p['pnl_usd'] == net_pnl == p['rates_pnl'] + credit_pnl
        if pid.endswith('EU'):
            assert 'cross-region proxy' in mappings[pid]['basis']
    for new, old in zip(result['positions'], prior['positions']):
        for factor in ('rates_pnl', 'equity_pnl', 'fx_pnl'):
            assert new[factor] == old[factor]
        assert new['pnl_usd'] == old['pnl_usd'] + new['credit_pnl']
    assert result['total_pnl_usd'] == pytest.approx(prior['total_pnl_usd'] - 80100)
    assert result['total_pnl_usd'] == sum(result['by_factor'].values())


def test_signed_cs01_reverses_short_spread_leg_without_extra_rates():
    # Hypothetical sign reversal in a test fixture only; production contains no credit shorts.
    frame = load_positions().copy()
    frame.loc[frame.id == 'HY-US', 'cs01_usd_per_bp'] *= -1
    result = calculate(frame, Shocks(hy_bp=18))
    positions = {p['id']: p for p in result['positions']}
    assert positions['HY-US']['credit_pnl'] == 44100
    assert positions['HY-EU']['credit_pnl'] == -36000
    assert result['by_factor']['rates_pnl'] == 0  # Pure OAS move has no Treasury leg.


def test_unreviewed_credit_instrument_cannot_silently_inherit_proxy(monkeypatch):
    frame = load_positions()
    frame.loc[frame.id == 'HY-US', 'instrument'] = 'Unreviewed credit derivative'
    monkeypatch.setattr('metis.reasoning.historical.load_positions', lambda: frame)
    with pytest.raises(ValueError, match='mapping requires review'):
        historical_context()


def test_legacy_captured_partial_context_is_not_upgraded_or_overwritten(monkeypatch):
    import subprocess
    old_inputs = json.loads(subprocess.check_output(['git', 'show',
        '1114a87:backend/metis/data/historical-20220913.json']))
    with TestClient(api.app) as client:
        fresh = client.post('/api/reasoning', json={'question': 'Explain', 'investigation_scope': 'historical'}).json()
        legacy = deepcopy(fresh)
        context = legacy['context']
        context['historical'] = {key: old_inputs[key] for key in ('episode', 'observations', 'mapping_assumptions', 'sources')}
        context['historical']['coverage'] = 'Partial-factor hypothetical calculation; credit-spread P&L and complete historical total unavailable'
        context['market']['observations'] = old_inputs['observations']
        partial = calculate(load_positions(), Shocks(rates_bp=5.37, equity_pct=-4.32, fx_pct=-1.46))
        context['daily'] = context['scenario'] = partial
        context['portfolio']['positions'] = partial['positions']
        context['evidence'] = [{'id': 'portfolio', 'description': 'Synthetic holdings'}, {'id': 'scenario', 'description': 'Partial factors'},
            *[{'id': key, **value} for key, value in old_inputs['sources'].items()]]
        legacy['interpretation'] = historical_demo(context).model_dump()
        captured = api.evidence_snapshots.capture(legacy, 'historical')
        unchanged = deepcopy(captured)
        monkeypatch.setattr('metis.reasoning.historical.historical_context', lambda: pytest.fail('Refreshed captured inputs'))
        response = client.post('/api/reasoning', json={'question': 'What evidence distinguishes them?', 'investigation_id': captured['investigation_id']})
        assert response.status_code == 200
        assert response.json()['context'] == captured['context']
        assert response.json()['context']['scenario']['total_pnl_usd'] == pytest.approx(-1416477.2)
        assert response.json()['interpretation']['hypotheses'] == captured['interpretation']['hypotheses']
        assert fresh['context']['scenario']['total_pnl_usd'] == pytest.approx(-1496577.2)
        assert captured == unchanged  # No old answer/prose or its evidence was mutated.
