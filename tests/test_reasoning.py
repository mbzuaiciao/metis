import json

import httpx
import pytest
from fastapi.testclient import TestClient

from metis.api.app import app
from metis.reasoning.harness import DemoProvider, HTTPProvider, ProviderError, ReasoningRequest, assemble_context, reason
from metis.analytics.engine import Shocks, calculate, load_json, load_positions

DEMONSTRATION_QUESTION = "Given the portfolio's exposures, current market conditions, and relevant historical patterns, what are its principal risks, and why?"


@pytest.fixture(autouse=True)
def demo_environment(monkeypatch):
    monkeypatch.setenv("METIS_PROVIDER", "demo")
    monkeypatch.delenv("METIS_MODEL", raising=False)
    monkeypatch.delenv("METIS_META_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_demo_receives_actual_selected_scenario():
    result = reason(ReasoningRequest(question="Why are rates not protecting the portfolio?", shocks=Shocks(rates_bp=-50)))
    assert result["mode"] == "demo"
    assert result["model"] is None
    assert result["context"]["scenario"]["total_pnl_usd"] == 2_578_000
    assert result["context"]["portfolio"]["nav_usd"] == 100_000_000
    assert len(result["context_operations"]) == 4
    assert set(result["interpretation"]["evidence_references"]) <= {e["id"] for e in result["context"]["evidence"]}


@pytest.mark.parametrize("provider", ["meta", "anthropic"])
def test_live_provider_contract(monkeypatch, provider):
    """Transport contract test, not a live-model evaluation."""
    monkeypatch.setenv("METIS_MODEL", "test-model")
    monkeypatch.setenv("METIS_META_API_KEY", "test-only")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only")
    monkeypatch.setenv("METIS_META_BASE_URL", "https://example.com/v1")
    request = ReasoningRequest(question="What are my risks?", shocks=Shocks(equity_pct=-10))
    context = assemble_context(request.shocks)
    expected = DemoProvider().interpret(request, context)
    def handler(req):
        body = json.loads(req.content)
        assert body["model"] == "test-model"
        content = json.loads(body["messages"][-1]["content"])
        assert content["question"] == request.question
        assert content["context"]["scenario"]["total_pnl_usd"] == -2_300_000
        if provider == "meta":
            assert req.url.path == "/v1/chat/completions"
            assert req.headers["authorization"] == "Bearer test-only"
            assert body["messages"][0]["role"] == "system"
            return httpx.Response(200, json={"choices":[{"finish_reason":"stop","message":{"content":expected.model_dump_json()}}]})
        assert req.url.path == "/v1/messages"
        assert req.headers["x-api-key"] == "test-only"
        assert req.headers["anthropic-version"] == "2023-06-01"
        assert "system" in body
        return httpx.Response(200, json={"content":[{"type":"text","text":expected.model_dump_json()}],"stop_reason":"end_turn"})
    original = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    assert HTTPProvider(provider).interpret(request, context) == expected


def test_invalid_provider_reply_is_sanitized(monkeypatch):
    monkeypatch.setenv("METIS_MODEL", "test-model")
    monkeypatch.setenv("METIS_META_API_KEY", "test-only")
    monkeypatch.setenv("METIS_META_BASE_URL", "https://example.com/v1")
    original = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(lambda _: httpx.Response(401, text="private-upstream-content")), **kwargs))
    with pytest.raises(ProviderError) as caught:
        HTTPProvider("meta").interpret(ReasoningRequest(question="Risks?"), assemble_context(Shocks()))
    assert "private-upstream-content" not in str(caught.value)


def test_missing_credentials_never_mislabel_demo_as_live(monkeypatch):
    monkeypatch.setenv("METIS_PROVIDER", "anthropic")
    with pytest.raises(ProviderError, match="configuration is incomplete"):
        reason(ReasoningRequest(question="Risks?"))


def test_api_end_to_end():
    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        data = client.get("/api/workstation").json()
        preset = data["scenarios"][3]
        result = client.post("/api/scenario", json=preset["shocks"]).json()
        assert result["total_pnl_usd"] == -3_347_000
        response = client.post("/api/reasoning", json={"question":"How does a recession differ from inflation?", "shocks":preset["shocks"]})
        assert response.status_code == 200
        assert response.json()["context"]["scenario"] == result
        assert response.json()["context"]["daily"] == data["daily"]


@pytest.mark.parametrize("payload", [{"rates_bp":301}, {"equity_pct":-101}, {"fx_pct":"NaN"}, {"surprise":1}])
def test_invalid_scenario_is_rejected(payload):
    with TestClient(app) as client:
        assert client.post("/api/scenario", json=payload).status_code == 422


def test_empty_question_is_rejected():
    with TestClient(app) as client:
        assert client.post("/api/reasoning", json={"question":"   "}).status_code == 422


@pytest.fixture
def configured_meta(monkeypatch):
    monkeypatch.setenv("METIS_PROVIDER", "meta")
    monkeypatch.setenv("METIS_MODEL", "llama-test-fixture")
    monkeypatch.setenv("METIS_META_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("METIS_META_API_KEY", "test-only-secret")


def mock_meta_transport(monkeypatch, handler):
    original = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))


def test_meta_workflow_with_broad_risk_off(monkeypatch, configured_meta):
    """Mocked model transport through the real API; not verified live inference."""
    preset = next(s for s in load_json("scenarios") if s["id"] == "risk-off")
    expected_scenario = calculate(load_positions(), Shocks(**preset["shocks"]))
    request = ReasoningRequest(question=DEMONSTRATION_QUESTION, shocks=Shocks(**preset["shocks"]))
    fixture = DemoProvider().interpret(request, assemble_context(request.shocks)).model_dump()
    captured = []

    def handler(req):
        body = json.loads(req.content)
        captured.append(body)
        assert req.url.path == "/v1/chat/completions"
        assert req.headers["authorization"] == "Bearer test-only-secret"
        payload = json.loads(body["messages"][-1]["content"])
        assert payload["question"] == DEMONSTRATION_QUESTION
        context = payload["context"]
        assert context["scenario"] == expected_scenario
        assert context["scenario"]["by_factor"] == {"rates_pnl": 2_578_000, "credit_pnl": -1_975_000, "equity_pnl": -3_450_000, "fx_pnl": -500_000}
        assert len(context["portfolio"]["positions"]) == 12
        assert context["portfolio"]["exposures"]["dv01_usd_per_bp"] == 51_560
        assert context["market"] == load_json("market")
        assert context["historical_context"] == load_json("history")
        for alternative in context["alternative_scenarios"]:
            expected = calculate(load_positions(), Shocks(**alternative["shocks"]))
            assert alternative["total_pnl_usd"] == expected["total_pnl_usd"]
            assert alternative["by_factor"] == expected["by_factor"]
        assert "test-only-secret" not in req.content.decode()
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(fixture)}}]})

    mock_meta_transport(monkeypatch, handler)
    with TestClient(app) as client:
        result = client.post("/api/reasoning", json={"question": DEMONSTRATION_QUESTION, "shocks": preset["shocks"]})
    assert result.status_code == 200
    response = result.json()
    assert response["mode"] == "meta"
    assert response["model"] == "llama-test-fixture"
    assert response["interpretation"] == fixture
    assert response["context"]["scenario"] == expected_scenario
    assert len(captured) == 1
    assert "test-only-secret" not in result.text


@pytest.mark.parametrize("missing", ["METIS_MODEL", "METIS_META_BASE_URL", "METIS_META_API_KEY"])
def test_meta_configuration_names_missing_variable(monkeypatch, configured_meta, missing):
    monkeypatch.setenv(missing, "   ")
    with TestClient(app) as client:
        response = client.post("/api/reasoning", json={"question": DEMONSTRATION_QUESTION})
    assert response.status_code == 502
    assert missing in response.json()["detail"]
    assert "No demonstration fallback" in response.json()["detail"]
    assert "interpretation" not in response.json()
    assert "test-only-secret" not in response.text


@pytest.mark.parametrize("endpoint", ["http://localhost.evil.test/v1", "https://user:password@example.com/v1", "https://example.com/v1?api_key=secret", "https://", "https://example.com:bad/v1"])
def test_meta_rejects_invalid_or_credential_bearing_urls(monkeypatch, configured_meta, endpoint):
    monkeypatch.setenv("METIS_META_BASE_URL", endpoint)
    with pytest.raises(ProviderError) as caught:
        HTTPProvider("meta")
    assert endpoint not in str(caught.value)


@pytest.mark.parametrize("failure,expected", [
    (401, "API key"), (403, "access"), (404, "METIS_MODEL"), (429, "quota"),
    (500, "availability"), ("timeout", "timed out"), ("network", "network"),
    ("json", "structured interpretation"), ("truncated", "structured interpretation"),
    ("evidence", "structured interpretation"),
])
def test_meta_errors_are_actionable_and_never_fallback(monkeypatch, configured_meta, failure, expected):
    def handler(req):
        if failure == "timeout":
            raise httpx.ReadTimeout("test-only-secret", request=req)
        if failure == "network":
            raise httpx.ConnectError("test-only-secret", request=req)
        if isinstance(failure, int):
            return httpx.Response(failure, text="test-only-secret")
        content = "not-json"
        if failure == "evidence":
            request = ReasoningRequest(question=DEMONSTRATION_QUESTION)
            output = DemoProvider().interpret(request, assemble_context(request.shocks)).model_dump()
            output["evidence_references"] = ["invented-source"]
            content = json.dumps(output)
        return httpx.Response(200, json={"choices": [{"finish_reason": "length" if failure == "truncated" else "stop", "message": {"content": content}}]})

    mock_meta_transport(monkeypatch, handler)
    with TestClient(app) as client:
        response = client.post("/api/reasoning", json={"question": DEMONSTRATION_QUESTION})
    assert response.status_code == 502
    assert expected in response.json()["detail"]
    assert "No demonstration fallback" in response.json()["detail"]
    assert "interpretation" not in response.json()
    assert "test-only-secret" not in response.text
