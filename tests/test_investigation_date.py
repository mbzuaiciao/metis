"""Date availability checks; no live inference or market retrieval."""
import importlib

from fastapi.testclient import TestClient
import pytest

from metis.analytics.engine import workstation

api = importlib.import_module('metis.api.app')


def test_default_date_is_unavailable_without_relabeling_snapshot():
    with TestClient(api.app) as client:
        data = client.get('/api/workstation').json()
    assert data['investigation']['default_date'] == '2026-10-30'
    assert data['investigation']['status'] == 'unavailable'
    assert data['market']['as_of'] == '2025-03-10'
    assert data['market']['previous_date'] == '2025-03-07'
    assert data['daily']['total_pnl_usd'] == -560770
    assert data['positions'] == workstation()['positions']


@pytest.mark.parametrize('extra', [{}, {'investigation_date': '2026-10-30'},
                                    {'investigation_date': '2026-10-29'}])
def test_unavailable_dates_fail_before_inference_or_capture(monkeypatch, extra):
    monkeypatch.setattr(api, 'reason', lambda *_: pytest.fail('Unavailable data reached provider'))
    monkeypatch.setattr(api.evidence_snapshots, 'capture', lambda *_: pytest.fail('Unavailable data captured'))
    with TestClient(api.app) as client:
        response = client.post('/api/reasoning', json={
            'question': 'Explain the day', 'investigation_scope': 'daily', **extra})
    assert response.status_code == 422
    assert 'no data was substituted' in response.json()['detail']
    assert 'interpretation' not in response.json()


def test_explicit_synthetic_date_and_captured_followup_remain_available(monkeypatch):
    monkeypatch.setenv('METIS_PROVIDER', 'demo')
    with TestClient(api.app) as client:
        response = client.post('/api/reasoning', json={
            'question': 'Explain the illustrative daily loss', 'investigation_scope': 'daily',
            'investigation_date': '2025-03-10', 'shocks': {'rates_bp': 100}})
        assert response.status_code == 200, response.text
        answer = response.json()
        assert answer['context']['market']['as_of'] == '2025-03-10'
        assert answer['context']['scenario'] == workstation()['daily']
        followup = {'question': 'Explain further', 'investigation_id': answer['investigation_id']}
        assert client.post('/api/reasoning', json=followup).json()['context'] == answer['context']
        assert client.post('/api/reasoning', json={**followup, 'investigation_date': '2026-10-30'}).status_code == 422


@pytest.mark.parametrize('scope', ['daily', 'historical', 'scenario'])
def test_dates_are_validated_and_never_silently_ignored(scope):
    with TestClient(api.app) as client:
        response = client.post('/api/reasoning', json={
            'question': 'Explain', 'investigation_scope': scope,
            'investigation_date': 'invalid' if scope == 'daily' else '2026-10-30'})
    assert response.status_code == 422
