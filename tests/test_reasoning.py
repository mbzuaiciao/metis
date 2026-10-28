import json

import httpx
import pytest
from fastapi.testclient import TestClient

from metis.api.app import app
from metis.reasoning.harness import DemoProvider, HTTPProvider, ProviderError, ReasoningRequest, assemble_context, reason
from metis.analytics.engine import Shocks


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
