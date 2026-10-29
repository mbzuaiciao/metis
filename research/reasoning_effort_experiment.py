"""Research-only evaluation of reasoning_effort="low" on Muse Spark 1.3.

No production changes, prompt modifications, token budget increases, or retries.
Maximum 8 live requests. Private records saved with 0600 permissions in ignored research/runs/.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic
from typing import Literal

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from metis.analytics.engine import Shocks, workstation
from metis.reasoning.harness import (
    HTTPProvider,
    Interpretation,
    META_INFERENCE_PARAMETERS,
    ProviderError,
    ReasoningRequest,
    SYSTEM,
    assemble_context,
    output_error,
    validate_interpretation,
)
from metis.verification.claims import verify_claims

MAX_CALLS = 8


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def write_private(path: Path, value: dict):
    with path.open("w", encoding="utf-8") as f:
        path.chmod(0o600)
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write("\n")


def define_cases():
    data = workstation()
    text = (REPO_ROOT / "frontend/src/investigation.ts").read_text()
    daily_q = re.search(r'export const dailyQuestion =\s*"([^"]+)"', text).group(1)
    scenario_q = re.search(r'export const scenarioQuestion =\s*"([^"]+)"', text).group(1)
    broad = next(s["shocks"] for s in data["scenarios"] if s["id"] == "risk-off")

    definitions = [
        (
            "01",
            daily_q,
            data["market"]["daily_shocks"],
            {
                "focus": "Daily loss attribution (exact showcase failure question)",
                "shocks": data["market"]["daily_shocks"],
                "expected": [
                    "Daily total -$560,770; rates +$412,480, spreads -$407,250, equities -$506,000, FX -$60,000.",
                    "Hedge/rates contribution (+412k) and total loss (-560k) are distinct.",
                    "Key positions: UST10 (+128k), UST2 (+17k), IRS-R (+224k), IRS-P (-96k), HYG net -$162k (rates +$18k, spread -$180k).",
                    "Distinguishes daily dated snapshot from hypothetical stress scenario; no asserted macroeconomic cause without evidence.",
                ],
            },
        ),
        (
            "02",
            scenario_q,
            broad,
            {
                "focus": "Broad Risk-Off scenario interpretation",
                "shocks": broad,
                "expected": [
                    "Stress total -$3,347,000 (-3.35% NAV) versus daily -$560,770.",
                    "Rates +$2,578,000, spreads -$1,975,000, equity -$3,450,000, FX -$500,000.",
                    "HY net loss -$872,500 decomposed into spread -$1,112,500 and rates +$240,000.",
                    "Identifies rate gains scaling linearly while credit spreads widen severely.",
                ],
            },
        ),
        (
            "03",
            (
                "How did the receive-fixed and pay-fixed swaps behave in the daily yield decline, "
                "and what can we conclude about hedge effectiveness from the portfolio loss? "
                "Distinguish signed sensitivities, directional contributions and an unstated hedge objective."
            ),
            data["market"]["daily_shocks"],
            {
                "focus": "Swaps behavior and hedge effectiveness under daily yield decline",
                "shocks": data["market"]["daily_shocks"],
                "expected": [
                    "Receive-fixed swap: DV01 +$28,000/bp, P&L +$224,000 (gains as yields fall).",
                    "Pay-fixed swap: DV01 -$12,000/bp, P&L -$96,000 (loses as yields fall).",
                    "Net swaps: DV01 +$16,000/bp, P&L +$128,000.",
                    "Positive aggregate rate gain does not establish mandate success/optimality without a stated objective.",
                ],
            },
        ),
        (
            "04",
            (
                "Can the cash balance, derivative marks and credit baskets establish funding adequacy, "
                "net counterparty exposure or issuer default losses under this stress? "
                "Give a useful scoped conclusion and the missing evidence, distinguishing marks and sensitivities from cash flows and losses."
            ),
            broad,
            {
                "focus": "Evidence boundaries, liquidity, counterparty, and unmodeled risks under stress",
                "shocks": broad,
                "expected": [
                    "$6m cash cannot establish funding adequacy without contractual margin/CSA terms, timing, and liquidity facility access.",
                    "Derivative marks do not equal net counterparty exposure without netting and collateral agreements.",
                    "CS01 measures spread sensitivity, not jump-to-default loss or recovery risk.",
                    "Appropriately abstains from declaring cash buffer definitively adequate or inadequate.",
                ],
            },
        ),
    ]

    return [
        {
            "id": key,
            "question": q,
            "shocks": s,
            "context": assemble_context(Shocks(**s)),
            "expectations": exp,
        }
        for key, q, s, exp in definitions
    ]


class ReasoningEffortMetaProvider(HTTPProvider):
    def __init__(self, reasoning_effort: Literal["low"] | None = None):
        super().__init__("meta")
        self.reasoning_effort = reasoning_effort

    def structured(self, request: ReasoningRequest, context: dict, output_model: type[BaseModel], system: str, schema_name: str) -> BaseModel:
        self.last_usage = None
        payload = json.dumps({"question": request.question, "context": context, "output_schema": output_model.model_json_schema()})
        messages = [t.model_dump() for t in request.history] + [{"role": "user", "content": payload}]

        url = f"{self.base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.key}"}
        schema = output_model.model_json_schema()

        def constrain_evidence(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "evidence_references":
                        value["items"]["enum"] = [e["id"] for e in context["evidence"]]
                    else:
                        constrain_evidence(value)
            elif isinstance(node, list):
                for value in node:
                    constrain_evidence(value)

        constrain_evidence(schema)

        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}] + messages,
            **META_INFERENCE_PARAMETERS,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        if self.reasoning_effort is not None:
            body["reasoning_effort"] = self.reasoning_effort

        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(url, headers=headers, json=body)
                response.raise_for_status()
                try:
                    data = response.json()
                except ValueError:
                    raise output_error(self.provider, "invalid_response_json", "HTTP response body is not JSON.") from None

            if isinstance(data, dict) and isinstance(data.get("usage"), dict):
                usage = data["usage"]
                self.last_usage = {
                    key: usage[key]
                    for key in ["prompt_tokens", "completion_tokens", "total_tokens"]
                    if type(usage.get(key)) is int and usage[key] >= 0
                }
                details = usage.get("completion_tokens_details")
                if isinstance(details, dict) and type(details.get("reasoning_tokens")) is int and details["reasoning_tokens"] >= 0:
                    self.last_usage["reasoning_tokens"] = details["reasoning_tokens"]
                self.last_usage = self.last_usage or None

            choice = data["choices"][0]
            finish = choice.get("finish_reason")
            if finish == "length":
                raise output_error(
                    self.provider,
                    "truncated",
                    "Meta reached the completion-token limit (finish_reason=length). Reasoning also consumes that budget.",
                )
            if finish == "content_filter" or choice["message"].get("refusal"):
                raise output_error(self.provider, "refused", "Meta did not return an interpretation due to content filters.")
            if finish != "stop":
                raise output_error(self.provider, "unexpected_finish_reason", f"Expected finish_reason=stop, got {finish}.")

            raw = choice["message"]["content"]
            if not isinstance(raw, str):
                raise TypeError("Expected string content in message.content")
            if not raw.strip():
                raise output_error(self.provider, "empty_content", "The completed response contains no interpretation text.")

            return validate_interpretation(raw, context, self.provider, output_model)

        except httpx.TimeoutException as exc:
            raise ProviderError(f"Live {self.provider} inference timed out. No demonstration fallback was used.") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            try:
                err_body = exc.response.json()
            except Exception:
                err_body = exc.response.text[:300]
            if status == 400:
                raise output_error(
                    self.provider,
                    "request_rejected",
                    f"HTTP 400 rejected the request: {err_body}",
                ) from exc
            guidance = {
                401: "Check the API key.",
                403: "Check endpoint and model access.",
                404: "Check METIS_MODEL and provider URL.",
                429: "Check provider quota.",
            }.get(status, "Check provider availability.")
            raise ProviderError(f"Live {self.provider} inference returned HTTP {status}: {err_body}. {guidance}") from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Cannot reach live {self.provider} endpoint: {exc}") from exc


def run_experiment(output_dir: Path):
    if os.getenv("METIS_PROVIDER") != "meta" or os.getenv("METIS_MODEL") != "muse-spark-1.3":
        raise ProviderError("Requires live METIS_PROVIDER=meta and METIS_MODEL=muse-spark-1.3.")

    output_dir = output_dir.resolve()
    if HERE / "runs" not in output_dir.parents:
        raise ValueError("Output directory must be within ignored research/runs/")

    output_dir.mkdir(parents=True, mode=0o700, exist_ok=False)

    rows = define_cases()

    tracked_paths = [
        Path(__file__),
        REPO_ROOT / "backend/metis/reasoning/harness.py",
        REPO_ROOT / "backend/metis/analytics/engine.py",
        REPO_ROOT / "backend/metis/verification/claims.py",
        REPO_ROOT / "frontend/src/investigation.ts",
        *sorted((REPO_ROOT / "backend/metis/data").glob("*")),
    ]

    protocol = {
        "title": "Muse Spark 1.3 Reasoning Effort Experiment (v1.2)",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "model": "muse-spark-1.3",
        "endpoint": os.getenv("METIS_META_BASE_URL", "").rstrip("/") + "/chat/completions",
        "settings_baseline_A": dict(META_INFERENCE_PARAMETERS),
        "settings_candidate_B": {**META_INFERENCE_PARAMETERS, "reasoning_effort": "low"},
        "timeout_seconds": 60,
        "max_calls": MAX_CALLS,
        "no_retries": True,
        "system_prompt": SYSTEM,
        "schema": Interpretation.model_json_schema(),
        "cases": [
            {
                "id": r["id"],
                "question": r["question"],
                "shocks": r["shocks"],
                "expectations": r["expectations"],
            }
            for r in rows
        ],
        "source_sha256": {str(p.relative_to(REPO_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked_paths},
        "input_hashes": {r["id"]: digest({"question": r["question"], "context": r["context"]}) for r in rows},
        "manual_criteria": [
            "Complete strictly validated JSON conforming to Interpretation (no truncation or schema violation).",
            "Correct signed attribution and arithmetic totals matching authoritative calculations.",
            "Distinguishes rates/hedge contribution from overall portfolio loss.",
            "Correct signed swap legs (receive positive, pay negative under falling yields).",
            "Recognizes that funding/counterparty/default risk is unquantified without contractual/netting data.",
            "No material financial regression or ungrounded certainty.",
        ],
        "decision_rule": (
            "Recommend integrating reasoning_effort='low' into production only if Condition B demonstrates an "
            "operational reliability benefit (eliminates truncation and reduces reasoning token consumption) "
            "without material financial or qualitative degradation across available cases. "
            "If evidence is inconclusive, rejected by the provider, or shows financial degradation: preserve baseline."
        ),
    }

    write_private(output_dir / "protocol.json", protocol)

    providers = {
        "A": ReasoningEffortMetaProvider(reasoning_effort=None),
        "B": ReasoningEffortMetaProvider(reasoning_effort="low"),
    }

    records = []
    start_time = monotonic()
    total_tokens_all = 0
    calls_executed = 0
    stop_early = False
    stop_reason = None

    print("=== STARTING REASONING EFFORT EXPERIMENT (v1.2) ===")
    print(f"Directory: {output_dir}")
    print(f"Cases: {len(rows)} | Conditions: A (omitted), B (low) | Max calls: {MAX_CALLS}\n")

    for row in rows:
        if stop_early:
            break
        for condition in ["A", "B"]:
            if calls_executed >= MAX_CALLS:
                stop_early = True
                stop_reason = f"Reached maximum allowed calls ({MAX_CALLS})."
                break

            provider = providers[condition]
            case_id = row["id"]
            question = row["question"]
            context = deepcopy(row["context"])

            record = {
                "case": case_id,
                "condition": condition,
                "reasoning_effort": "low" if condition == "B" else "omitted (baseline)",
                "question": question,
                "started_utc": datetime.now(timezone.utc).isoformat(),
                "response": None,
                "error": None,
                "usage": None,
                "verification": None,
            }

            calls_executed += 1
            print(f"[{calls_executed}/{MAX_CALLS}] Case {case_id} Condition {condition} (effort={record['reasoning_effort']})...", end="", flush=True)

            t0 = monotonic()
            try:
                result = provider.structured(
                    ReasoningRequest(question=question),
                    context,
                    Interpretation,
                    SYSTEM,
                    "financial_interpretation",
                )
                record["response"] = result.model_dump()
                record["verification"] = verify_claims(result.financial_claims, context)
                status_str = "SUCCESS"
            except ProviderError as exc:
                record["error"] = str(exc)
                status_str = f"FAILED: {exc}"
            except Exception as exc:
                record["error"] = f"Unexpected exception: {type(exc).__name__}: {exc}"
                status_str = f"UNEXPECTED ERROR: {exc}"

            elapsed = round(monotonic() - t0, 3)
            record["seconds"] = elapsed
            record["usage"] = deepcopy(provider.last_usage)

            if record["usage"]:
                total_tokens_all += record["usage"].get("total_tokens", 0)

            record["serialized_response_chars"] = len(json.dumps(record["response"])) if record["response"] else None

            write_private(output_dir / f"{case_id}-{condition}.json", record)

            u = record["usage"] or {}
            print(
                f" {status_str} ({elapsed}s) | "
                f"prompt={u.get('prompt_tokens', 'N/A')}, "
                f"comp={u.get('completion_tokens', 'N/A')}, "
                f"reasoning={u.get('reasoning_tokens', 'N/A')}, "
                f"visible={(u.get('completion_tokens', 0) - u.get('reasoning_tokens', 0)) if u.get('reasoning_tokens') else 'N/A'}"
            )

            compact_record = {
                "case": case_id,
                "condition": condition,
                "reasoning_effort": record["reasoning_effort"],
                "success": record["response"] is not None,
                "error": record["error"],
                "seconds": elapsed,
                "usage": record["usage"],
                "serialized_chars": record["serialized_response_chars"],
            }
            records.append(compact_record)

            # Stopping rule check: if provider rejected parameter with HTTP 400
            if record["error"] and "HTTP 400" in record["error"] and "reasoning_effort" in record["error"]:
                stop_early = True
                stop_reason = f"Provider rejected parameter reasoning_effort with HTTP 400 on Call {calls_executed}."
                print(f"\n[STOPPING RULE TRIGGERED] {stop_reason}")
                break

    wall_duration = round(monotonic() - start_time, 3)

    # Check source files remained unchanged during experiment
    source_unchanged = all(
        hashlib.sha256((REPO_ROOT / p).read_bytes()).hexdigest() == h
        for p, h in protocol["source_sha256"].items()
    )

    manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_calls": calls_executed,
        "max_allowed_calls": MAX_CALLS,
        "wall_seconds": wall_duration,
        "total_reported_tokens": total_tokens_all,
        "source_unchanged": source_unchanged,
        "stopping_rule_triggered": stop_early,
        "stopping_reason": stop_reason,
        "records": records,
    }

    write_private(output_dir / "manifest.json", manifest)

    if not source_unchanged:
        raise RuntimeError("Frozen source files changed during experiment execution!")

    print("\n=== EXPERIMENT EXECUTION COMPLETE ===")
    print(f"Total calls: {calls_executed} | Wall seconds: {wall_duration}s | Tokens reported: {total_tokens_all}")
    print(f"Manifest written to: {output_dir / 'manifest.json'}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    load_dotenv(REPO_ROOT / ".env")
    run_experiment(args.output_dir)
