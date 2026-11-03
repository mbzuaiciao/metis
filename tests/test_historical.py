"""Historical production workflow checks; no live inference or causal validation."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
import httpx
import pytest

from metis.analytics.engine import workstation
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
    assert (root / 'backend/metis/data/historical-20220913.json').read_bytes() == (root / 'research/historical-macro-20220913-inputs.json').read_bytes()
    before = workstation()
    with TestClient(api.app) as client:
        response = client.post('/api/reasoning', json={'question': 'Explain the CPI day',
            'investigation_scope': 'historical', 'shocks': {'rates_bp': -100, 'ig_bp': 200}})
        assert response.status_code == 200, response.text
        answer = response.json()
        context = answer['context']
        assert context['market']['as_of'] == '2022-09-13'
        assert context['scenario']['shocks']['rates_bp'] == 5.37  # Server-owned inputs override client shocks.
        assert context['scenario']['total_pnl_usd'] == pytest.approx(-1416477.2)
        assert context['scenario']['by_factor'] == {'rates_pnl': -276877.2, 'credit_pnl': 0, 'equity_pnl': -993600, 'fx_pnl': -146000}
        assert context['historical']['observations']['ig_spread']['change_bp'] is None
        assert context['historical']['observations']['hy_spread']['change_bp'] is None
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
