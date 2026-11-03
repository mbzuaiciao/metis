import json
from copy import deepcopy

import httpx
import pytest
from pydantic import ValidationError

from metis.analytics.engine import Shocks, load_json
from metis.reasoning.ablation import QUESTION, numeric_inputs, run_comparison
from metis.reasoning.harness import (
    DemoProvider, ReasoningRequest, assemble_context, evidence_only_context, reason,
    validate_interpretation,
)


def test_context_diff_is_only_interpretation_fields():
    shocks = Shocks(**next(s for s in load_json("scenarios") if s["id"] == "risk-off")["shocks"])
    full = assemble_context(shocks)
    original = deepcopy(full)
    evidence = assemble_context(shocks, "evidence_only")
    expected = deepcopy(full)
    del expected["market"]["commentary"]
    for episode in expected["historical_context"]:
        del episode["interpretation"]
    for scenario in expected["alternative_scenarios"]:
        if scenario["id"] == "risk-off":
            del scenario["description"]
    assert evidence == expected
    assert evidence_only_context(full) == evidence
    assert full == original == assemble_context(shocks, "full")
    assert numeric_inputs(full) == numeric_inputs(evidence)
    for key in ["portfolio", "daily", "scenario", "evidence", "conventions"]:
        assert evidence[key] == full[key]
    for before, after in zip(full["historical_context"], evidence["historical_context"]):
        for field in ["id", "title", "period", "fact", "source_title", "source_url", "limitation"]:
            assert after[field] == before[field]
        assert "interpretation" not in after
    assert "commentary" not in evidence["market"]
    assert full["scenario"]["total_pnl_usd"] == -4_240_000


def test_request_modes_and_demo_stay_runnable(monkeypatch):
    monkeypatch.setenv("METIS_PROVIDER", "demo")
    assert ReasoningRequest(question=QUESTION).context_mode == "full"
    with pytest.raises(ValidationError):
        ReasoningRequest(question=QUESTION, context_mode="unknown")
    with pytest.raises(ValidationError):
        ReasoningRequest(question=QUESTION, context_mode="evidence_only", history=[{"role": "assistant", "content": "Prior narrative"}])
    response = reason(ReasoningRequest(question=QUESTION, context_mode="evidence_only"))
    assert response["mode"] == "demo"
    assert response["context_mode"] == "evidence_only"
    assert response["usage"] is None
    assert "commentary" not in response["context"]["market"]


@pytest.mark.parametrize("reverse_order", [False, True])
def test_paired_mock_preserves_every_other_inference_input(monkeypatch, tmp_path, reverse_order):
    monkeypatch.setenv("METIS_PROVIDER", "meta")
    monkeypatch.setenv("METIS_MODEL", "fixture-model")
    monkeypatch.setenv("METIS_META_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("METIS_META_API_KEY", "private-test-key")
    captured = []

    def handler(req):
        body = json.loads(req.content)
        captured.append(body)
        payload = json.loads(body["messages"][-1]["content"])
        context = payload["context"]
        request = ReasoningRequest(question=payload["question"], shocks=Shocks(**context["scenario"]["shocks"]))
        # A deterministic transport fixture, not a judgment of generated prose.
        interpretation = DemoProvider().interpret(request, context)
        return httpx.Response(200, json={
            "choices": [{"finish_reason": "stop", "message": {"content": interpretation.model_dump_json()}}],
            "usage": {"prompt_tokens": 400, "completion_tokens": 200, "total_tokens": 600,
                      "completion_tokens_details": {"reasoning_tokens": 70}, "private": "must-not-record"},
        })

    original = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    destination = tmp_path / "paired"
    manifest = run_comparison(destination, reverse_order=reverse_order)
    assert manifest["live_comparison_completed"]
    assert manifest["quantitative_inputs_identical"]
    assert manifest["execution_order"] == (["evidence_only", "full"] if reverse_order else ["full", "evidence_only"])
    assert [run["condition"] for run in manifest["runs"]] == (["B", "A"] if reverse_order else ["A", "B"])
    assert len(captured) == 2
    a, b = deepcopy(captured[::-1] if reverse_order else captured)
    payload_a = json.loads(a["messages"][-1]["content"])
    payload_b = json.loads(b["messages"][-1]["content"])
    assert payload_b["context"] == evidence_only_context(payload_a["context"])
    assert payload_a["question"] == payload_b["question"] == QUESTION
    assert payload_a["output_schema"] == payload_b["output_schema"]
    a["messages"][-1]["content"] = b["messages"][-1]["content"] = "<only-context-varies>"
    assert a == b  # Same model, prompt, history, schema, sampling and token budget.
    assert len(a["messages"]) == 2  # No previous response is replayed into B.
    for mode in ["full", "evidence_only"]:
        record = json.loads((destination / f"{mode}.json").read_text())
        validate_interpretation(json.dumps(record["interpretation"]), record["context"], "meta")
        assert record["usage"] == {"prompt_tokens": 400, "completion_tokens": 200, "total_tokens": 600, "reasoning_tokens": 70}
        assert record["error"] is None
    all_records = "".join(p.read_text() for p in destination.glob("*.json"))
    assert "private-test-key" not in all_records
    assert "must-not-record" not in all_records
    with pytest.raises(FileExistsError):
        run_comparison(destination)  # Never overwrite an earlier paired record.


def test_missing_credentials_records_both_failures_without_demo(monkeypatch, tmp_path):
    monkeypatch.setenv("METIS_PROVIDER", "meta")
    monkeypatch.delenv("METIS_META_API_KEY", raising=False)
    manifest = run_comparison(tmp_path / "missing-credentials")
    assert not manifest["live_comparison_completed"]
    for entry in manifest["runs"]:
        assert not entry["succeeded"]
        assert "METIS_META_API_KEY" in entry["error"]
        record = json.loads((tmp_path / "missing-credentials" / entry["record"]).read_text())
        assert record["interpretation"] is None
        assert record["usage"] is None
