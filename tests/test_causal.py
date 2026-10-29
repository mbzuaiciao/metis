"""Contract and numerical tests, not automated judgments of economic correctness."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from metis.api.app import app
from metis.analytics.engine import Shocks, calculate, load_positions
from metis.reasoning.causal import CausalRequest, ProposedShocks, demo_exploration


@pytest.fixture
def meta(monkeypatch):
    monkeypatch.setenv("METIS_PROVIDER", "meta")
    monkeypatch.setenv("METIS_MODEL", "test-only-model")
    monkeypatch.setenv("METIS_META_API_KEY", "test-only-secret")
    monkeypatch.setenv("METIS_META_BASE_URL", "https://example.com/v1")


def mock_reply(monkeypatch, payload, finish="stop"):
    original = httpx.Client
    def handler(request):
        body = json.loads(request.content)
        assert request.url.path == "/v1/chat/completions"
        assert body["reasoning_effort"] == "low"
        assert body["response_format"]["json_schema"]["name"] == "causal_exploration"
        schema = body["response_format"]["json_schema"]["schema"]
        assert schema["$defs"]["ProposedShocks"]["required"] == list(Shocks.model_fields)
        assert "scenario" not in schema["$defs"]["Mechanism"]["properties"]["evidence_references"]["items"]["enum"]
        return httpx.Response(200, json={"choices": [{"finish_reason": finish, "message": {"content": payload}}]})
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))


def request():
    return CausalRequest(hypothesis="Recession fears", alternative="Inflation relief", common_rates_bp=-50)


def test_mechanism_consistency_contract(meta, monkeypatch):
    """Sign consistency is machine-checkable; causal coherence needs manual review."""
    for factor in Shocks.model_fields:
        engine_field = Shocks.model_json_schema()["properties"][factor]
        proposed_field = ProposedShocks.model_json_schema()["properties"][factor]
        assert proposed_field["minimum"] == engine_field["minimum"]
        assert proposed_field["maximum"] == engine_field["maximum"]
    expected = demo_exploration(request())
    mock_reply(monkeypatch, expected.model_dump_json())
    with TestClient(app) as client:
        response = client.post("/api/causal-exploration", json=request().model_dump())
    assert response.status_code == 200
    result = response.json()
    assert result["mode"] == "meta"
    assert result["exploration"] == expected.model_dump()
    for mechanism in result["exploration"]["mechanisms"]:
        assert set(mechanism["cross_asset"]) == set(Shocks.model_fields)
        assert all(effect["rationale"] for effect in mechanism["cross_asset"].values())
        assert mechanism["discriminating_evidence"] and mechanism["uncertainty"]
    assert "total_pnl_usd" not in result["exploration"]["mechanisms"][0]


def test_alternative_hypotheses_share_an_observation_not_a_true_cause(monkeypatch):
    monkeypatch.setenv("METIS_PROVIDER", "demo")
    with TestClient(app) as client:
        result = client.post("/api/causal-exploration", json=request().model_dump()).json()
    a, b = result["exploration"]["mechanisms"]
    assert a["proposed_shocks"]["rates_bp"] == b["proposed_shocks"]["rates_bp"] == -50
    assert a["cross_asset"]["ig_bp"]["direction"] != b["cross_asset"]["ig_bp"]["direction"]
    assert all(m["alternative_explanations"] for m in (a, b))
    assert all("not estimates or predictions" in m["assumption_note"] for m in (a, b))
    assert result["context"]["market"]["as_of"] == "2025-03-10"
    assert "commentary" not in result["context"]["market"]
    assert all("interpretation" not in h and h["fact"] and h["source_url"] for h in result["context"]["historical_context"])


def test_numerical_integrity_of_reviewed_shocks(monkeypatch):
    monkeypatch.setenv("METIS_PROVIDER", "demo")
    proposals = demo_exploration(request()).mechanisms
    with TestClient(app) as client:
        for mechanism in proposals:
            accepted = mechanism.proposed_shocks.model_dump()
            accepted["hy_bp"] += 10  # A user edit, not a model calculation.
            response = client.post("/api/scenario", json=accepted)
            assert response.status_code == 200
            assert response.json() == calculate(load_positions(), Shocks(**accepted))
        # Reproduces the existing Broad Risk-Off engine output exactly.
        accepted = proposals[0].proposed_shocks
        assert calculate(load_positions(), accepted)["total_pnl_usd"] == -3_347_000


@pytest.mark.parametrize("failure", ["invalid_json", "direction", "reference", "anchor", "truncated", "missing_factor"])
def test_invalid_live_proposals_fail_explicitly_without_substitution(meta, monkeypatch, failure):
    payload = demo_exploration(request()).model_dump()
    if failure == "direction":
        payload["mechanisms"][0]["cross_asset"]["hy_bp"]["direction"] = "down"
    if failure == "reference":
        payload["mechanisms"][0]["evidence_references"] = ["private-invented-id"]
    if failure == "anchor":
        payload["mechanisms"][0]["proposed_shocks"]["rates_bp"] = -25
    if failure == "missing_factor":
        del payload["mechanisms"][0]["proposed_shocks"]["hy_bp"]
    raw = "private-invalid-json" if failure == "invalid_json" else json.dumps(payload)
    mock_reply(monkeypatch, raw, "length" if failure == "truncated" else "stop")
    with TestClient(app) as client:
        response = client.post("/api/causal-exploration", json=request().model_dump())
    assert response.status_code == 502
    assert "No demonstration fallback" in response.json()["detail"]
    assert "exploration" not in response.json()
    assert "private-" not in response.text


def test_missing_credentials_and_bad_input_are_explicit(meta, monkeypatch):
    monkeypatch.delenv("METIS_META_API_KEY")
    with TestClient(app) as client:
        assert client.post("/api/causal-exploration", json=request().model_dump()).status_code == 502
        for change in [{"common_rates_bp": 301}, {"hypothesis": " "}, {"alternative": "Recession fears"}]:
            assert client.post("/api/causal-exploration", json=request().model_dump() | change).status_code == 422


@pytest.mark.parametrize("mode", ["demo", "meta"])
def test_workstation_reports_causal_mode_without_inference(monkeypatch, mode):
    monkeypatch.setenv("METIS_PROVIDER", f" {mode.upper()} ")
    with TestClient(app) as client:
        assert client.get("/api/workstation").json()["causal_mode"] == mode


def test_workstation_defaults_to_demo(monkeypatch):
    monkeypatch.delenv("METIS_PROVIDER", raising=False)
    with TestClient(app) as client:
        assert client.get("/api/workstation").json()["causal_mode"] == "demo"


def test_live_custom_hypotheses_still_reach_meta(meta, monkeypatch):
    payload = demo_exploration(request()).model_dump()
    payload["mechanisms"][0]["title"] = "Supply normalization"
    mock_reply(monkeypatch, json.dumps(payload))
    with TestClient(app) as client:
        response = client.post("/api/causal-exploration", json=request().model_dump() | {"hypothesis": "Supply normalization"})
    assert response.status_code == 200
    assert response.json()["request"]["hypothesis"] == "Supply normalization"
    assert response.json()["mode"] == "meta"
