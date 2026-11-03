"""Captured evidence continuity through the real API. Demo/mocked transports only."""
from copy import deepcopy
import importlib
import json

from fastapi.testclient import TestClient
import httpx
import pytest

from metis.reasoning.harness import DemoProvider
from metis.reasoning.followup import EvidenceSnapshots

api = importlib.import_module('metis.api.app')


@pytest.fixture(autouse=True)
def demo_and_fresh_store(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER', 'demo')
    monkeypatch.setattr(api, 'evidence_snapshots', EvidenceSnapshots())


def start(client, scope='scenario', **shocks):
    response = client.post('/api/reasoning', json={'question': 'Explain this calculation.',
        'investigation_scope': scope, 'shocks': shocks})
    assert response.status_code == 200, response.text
    return response.json()


def follow(client, answer, **extra):
    return client.post('/api/reasoning', json={'question': 'Which positions drove that?',
        'investigation_id': answer['investigation_id'], **extra})


@pytest.mark.parametrize('scope', ['daily', 'scenario'])
def test_followup_reuses_entire_snapshot_before_and_after_control_and_source_changes(monkeypatch, scope):
    with TestClient(api.app) as client:
        original = start(client, scope, rates_bp=-50, equity_pct=-15)
        before = follow(client, original).json()
        assert before['context'] == original['context']
        assert before['investigation_scope'] == scope
        # Simulate current controls being recalculated independently.
        changed = client.post('/api/scenario', json={'rates_bp': 70, 'equity_pct': 10}).json()
        assert changed['shocks'] != original['context']['scenario']['shocks']
        old = deepcopy(original)
        original['context']['portfolio']['nav_usd'] = 1  # Browser-returned data is not trusted.
        original['context']['scenario']['total_pnl_usd'] = 0
        # Even changing every current backend input must not refresh a follow-up.
        monkeypatch.setattr(api, 'workstation', lambda: pytest.fail('Follow-up reloaded workstation'))
        monkeypatch.setattr('metis.reasoning.harness.assemble_context', lambda *args: pytest.fail('Follow-up rebuilt context'))
        seen = []
        interpret = DemoProvider.interpret
        def inspect(self, request, context):
            seen.append(deepcopy(context))
            return interpret(self, request, context)
        monkeypatch.setattr(DemoProvider, 'interpret', inspect)
        response = follow(client, old)
        assert response.status_code == 200
        after = response.json()
        assert after['context'] == before['context'] == old['context'] == seen[0]
        assert after['verification'] == before['verification']
        assert after['mode'] == old['mode'] == 'demo' and after['model'] is None
        assert after['investigation_id'] == old['investigation_id']
        assert old['context']['portfolio']['nav_usd'] == 100_000_000
        # Each returned object is isolated from both provider and caller mutations.
        seen[0]['portfolio']['nav_usd'] = 2
        assert follow(client, old).json()['context'] == old['context']


def test_daily_scenario_daily_transitions_preserve_previous_calculations_and_ids():
    with TestClient(api.app) as client:
        daily = start(client, 'daily', rates_bp=100)  # Backend normalizes explicit daily scope.
        scenario = start(client, rates_bp=-50, ig_bp=75, hy_bp=250, equity_pct=-15, fx_pct=-5)
        daily_again = start(client, 'daily')
        assert len({a['investigation_id'] for a in [daily, scenario, daily_again]}) == 3
        assert daily['context']['scenario'] == daily['context']['daily']
        assert daily_again['context'] == daily['context']
        assert scenario['context']['scenario']['total_pnl_usd'] == -3347000
        for original in [daily, scenario, daily_again]:
            continued = follow(client, original).json()
            assert continued['context'] == original['context']
            assert continued['investigation_scope'] == original['investigation_scope']


@pytest.mark.parametrize('extra', [{'context': {'portfolio': {'nav_usd': 1}}}, {'shocks': {'rates_bp': 200}}, {'investigation_scope': 'daily'}])
def test_followup_cannot_replace_captured_truth_or_scope(extra):
    with TestClient(api.app) as client:
        original = start(client)
        assert follow(client, original, **extra).status_code == 422


def test_expired_snapshot_and_changed_mode_are_explicit_without_fallback(monkeypatch):
    monkeypatch.setattr(api, 'evidence_snapshots', EvidenceSnapshots(capacity=1))
    with TestClient(api.app) as client:
        old = start(client, 'daily')
        current = start(client, rates_bp=50)
        response = follow(client, old)
        assert response.status_code == 409
        assert 'no current calculation was substituted' in response.json()['detail']
        assert 'interpretation' not in response.json()
        monkeypatch.setenv('METIS_PROVIDER', 'meta')
        response = follow(client, current)
        assert response.status_code == 409 and 'Provider mode changed' in response.json()['detail']
        assert 'interpretation' not in response.json()


def test_mocked_live_followup_preserves_context_history_and_failure_handling(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER', 'meta')
    monkeypatch.setenv('METIS_MODEL', 'scope-test')
    monkeypatch.setenv('METIS_META_API_KEY', 'test-only')
    monkeypatch.setenv('METIS_META_BASE_URL', 'https://example.com/v1')
    captured = []
    fail = False
    def handler(request):
        body = json.loads(request.content)
        captured.append(body)
        context = json.loads(body['messages'][-1]['content'])['context']
        # Use the existing deterministic fixture to exercise real wire/schema handling.
        from metis.reasoning.harness import ReasoningRequest
        answer = DemoProvider().interpret(ReasoningRequest(question='Fixture'), context)
        return httpx.Response(200, json={'choices': [{'finish_reason': 'length' if fail else 'stop',
            'message': {'content': answer.model_dump_json()}}]})
    original_client = httpx.Client
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    with TestClient(api.app) as client:
        initial = start(client, 'daily')
        history = [{'role': 'user', 'content': initial['question']},
                   {'role': 'assistant', 'content': initial['interpretation']['summary']}]
        response = follow(client, initial, history=history)
        assert response.status_code == 200
        continued = response.json()
        assert continued['mode'] == 'meta' and continued['model'] == 'scope-test'
        payload = json.loads(captured[-1]['messages'][-1]['content'])
        assert payload['context'] == initial['context'] == continued['context']
        assert captured[-1]['messages'][1:-1] == history
        fail = True
        response = follow(client, initial, history=history)
        assert response.status_code == 502 and '[truncated]' in response.json()['detail']
        assert 'No demonstration fallback' in response.json()['detail']
        assert 'interpretation' not in response.json()
        fail = False
        assert follow(client, initial).json()['context'] == initial['context']
        monkeypatch.setenv('METIS_MODEL', 'another-model')
        assert follow(client, initial).status_code == 409
        assert len(captured) == 4  # Initial + success + simulated failure + success; no extra request on model change.


def test_evidence_only_snapshot_preserves_no_history_boundary():
    with TestClient(api.app) as client:
        response = client.post('/api/reasoning', json={'question': 'Evidence-only test', 'context_mode': 'evidence_only'})
        assert response.status_code == 200
        initial = response.json()
        assert follow(client, initial).status_code == 200
        response = follow(client, initial, history=[{'role': 'assistant', 'content': 'Prior narrative'}])
        assert response.status_code == 409 and 'do not accept conversation history' in response.json()['detail']

@pytest.mark.parametrize('scope', ['daily', 'scenario'])
def test_hypotheses_follow_captured_scope_without_changing_calculations(scope):
    from metis.analytics.engine import workstation, calculate, load_positions, Shocks
    with TestClient(api.app) as client:
        answer = start(client, scope, rates_bp=50, ig_bp=-10, hy_bp=-20, equity_pct=3)
        expected = workstation()['daily'] if scope == 'daily' else calculate(
            load_positions(), Shocks(rates_bp=50, ig_bp=-10, hy_bp=-20, equity_pct=3))
        assert answer['context']['daily' if scope == 'daily' else 'scenario'] == expected
        hypotheses = answer['interpretation']['hypotheses']
        assert len(hypotheses) == 2
        for hypothesis in hypotheses:
            assert ('Synthetic daily moves' if scope == 'daily' else 'Hypothetical assumptions (not observed moves)') in hypothesis['consistent_evidence']
            assert 'cannot distinguish' in hypothesis['uncertainty']
            assert hypothesis['available_checks'] and hypothesis['additional_evidence']
        assert follow(client, answer).json()['interpretation']['hypotheses'] == hypotheses
        assert answer['verification']
