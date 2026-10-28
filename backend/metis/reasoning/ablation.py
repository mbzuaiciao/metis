"""One paired financial-reasoning comparison; no grading or retry framework."""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

from dotenv import load_dotenv

from metis.analytics.engine import DATA, Shocks, load_json
from metis.reasoning.harness import (
    HTTPProvider, META_INFERENCE_PARAMETERS, SYSTEM, Interpretation, ProviderError,
    ReasoningRequest, assemble_context, evidence_only_context,
)

QUESTION = "Given the portfolio's exposures, current market conditions, and relevant historical patterns, what are its principal risks, and why?"


def digest(value: dict | str) -> str:
    encoded = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
    return hashlib.sha256(encoded.encode()).hexdigest()


def numeric_inputs(value, path="") -> dict:
    """Path-aware audit, so removing/moving any numerical evidence is detected."""
    if isinstance(value, dict):
        return {k: v for key, item in value.items() for k, v in numeric_inputs(item, f"{path}/{key}").items()}
    if isinstance(value, list):
        return {k: v for index, item in enumerate(value) for k, v in numeric_inputs(item, f"{path}/{index}").items()}
    return {path: value} if type(value) in {int, float} else {}


def write_private(path: Path, record: dict):
    with path.open("x", encoding="utf-8") as output:
        path.chmod(0o600)
        json.dump(record, output, indent=2, ensure_ascii=False)
        output.write("\n")


def run_comparison(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    preset = next(s for s in load_json("scenarios") if s["id"] == "risk-off")
    shocks = Shocks(**preset["shocks"])
    full = assemble_context(shocks)
    contexts = {"full": full, "evidence_only": evidence_only_context(full)}
    assert numeric_inputs(full) == numeric_inputs(contexts["evidence_only"])
    assert full["evidence"] == contexts["evidence_only"]["evidence"]
    provider = None
    configuration_error = None
    try:
        if os.getenv("METIS_PROVIDER", "demo").strip().lower() != "meta":
            raise ProviderError("Comparison requires METIS_PROVIDER=meta; demonstration output is not a live comparison.")
        provider = HTTPProvider("meta")  # Freeze model, credentials and endpoint for both calls.
    except ProviderError as exc:
        configuration_error = str(exc)

    source_files = [Path(__file__), Path(__file__).with_name("harness.py"), *sorted(DATA.glob("*.*"))]
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    manifest = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": provider.model if provider else os.getenv("METIS_MODEL", "").strip() or None,
        "endpoint": f"{provider.base}/chat/completions" if provider else None,
        "question": QUESTION, "scenario_id": preset["id"], "scenario_shocks": shocks.model_dump(),
        "inference_parameters": dict(META_INFERENCE_PARAMETERS),
        "system_prompt": SYSTEM, "response_schema": Interpretation.model_json_schema(),
        "evidence_ids": [e["id"] for e in full["evidence"]],
        "git_revision_at_run": revision,
        "source_sha256": {str(p.relative_to(DATA.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
        "context_sha256": {mode: digest(context) for mode, context in contexts.items()},
        "numeric_inputs_sha256": digest(numeric_inputs(full)),
        "quantitative_inputs_identical": True,
        "removed_context_paths": ["market.commentary", *[f"historical_context[{i}].interpretation" for i in range(len(full["historical_context"]))], "alternative_scenarios[3].description (risk-off)"],
        "execution_order": ["full", "evidence_only"], "conversation_history": [],
        "runs": [],
    }
    for condition, mode in [("A", "full"), ("B", "evidence_only")]:
        record = {
            "condition": condition, "context_mode": mode, "model": manifest["model"],
            "question": QUESTION, "scenario_shocks": shocks.model_dump(), "context": contexts[mode],
            "interpretation": None, "usage": None, "error": configuration_error,
        }
        started = monotonic()
        if provider is not None:
            request = ReasoningRequest(question=QUESTION, shocks=shocks, context_mode=mode)
            try:
                record["interpretation"] = provider.interpret(request, contexts[mode]).model_dump()
            except ProviderError as exc:
                record["error"] = str(exc)  # The adapter already sanitizes provider errors.
            record["usage"] = provider.last_usage
        record["elapsed_seconds"] = round(monotonic() - started, 3)
        filename = f"{mode}.json"
        write_private(output_dir / filename, record)
        manifest["runs"].append({"condition": condition, "context_mode": mode, "record": filename, "succeeded": record["interpretation"] is not None, "usage": record["usage"], "error": record["error"]})
    manifest["live_comparison_completed"] = all(run["succeeded"] for run in manifest["runs"])
    write_private(output_dir / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("research/runs") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    args = parser.parse_args()
    load_dotenv()
    result = run_comparison(args.output_dir)
    # Never print model text, API credentials or context into terminal logs.
    print(json.dumps({"output_dir": str(args.output_dir.resolve()), "live_comparison_completed": result["live_comparison_completed"], "runs": result["runs"]}, indent=2))
    return 0 if result["live_comparison_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
