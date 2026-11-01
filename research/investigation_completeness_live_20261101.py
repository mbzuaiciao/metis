"""Six-case, live-only Muse Spark investigation-completeness baseline.

From repo root:
  METIS_PROVIDER=meta METIS_MODEL=muse-spark-1.3 uv run python research/investigation_completeness_live_20261101.py

Requires the same existing .env credentials as Metis, loaded locally only.
No automatic rerun, no demo substitution, no scoring model.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

from dotenv import load_dotenv

from metis.analytics.engine import Shocks
from metis.reasoning.harness import (
    HTTPProvider, META_INFERENCE_PARAMETERS, ProviderError,
    ReasoningRequest, assemble_context,
)

HERE = Path(__file__).resolve().parent
CASES = HERE / "investigation-completeness-cases-20261101.json"
RUNS = HERE / "runs"
QUESTIONS = 6


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def private_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        os.chmod(path, 0o600)
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def main():
    load_dotenv(HERE.parent / ".env", override=False)
    if os.environ.get("METIS_PROVIDER") != "meta" or os.environ.get("METIS_MODEL") != "muse-spark-1.3":
        raise SystemExit("Requires METIS_PROVIDER=meta and METIS_MODEL=muse-spark-1.3; never use demo fallback.")
    study = json.loads(CASES.read_text(encoding="utf-8"))
    cases = study["cases"]
    assert len(cases) == QUESTIONS and len({case["id"] for case in cases}) == QUESTIONS
    provider = HTTPProvider("meta")
    run_dir = RUNS / ("investigation-completeness-20261101-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    run_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    manifest = {
        "study": study["study"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": provider.model,
        "settings": META_INFERENCE_PARAMETERS,
        "cases_sha256": hashlib.sha256(CASES.read_bytes()).hexdigest(),
        "records": [],
        "status": "started",
    }
    try:
        for case in cases:
            # Rubric is withheld from the model input.
            question = case["question"]
            request = ReasoningRequest(question=question, shocks=Shocks(), history=[])
            context = assemble_context(request.shocks)
            start = monotonic()
            try:
                answer = provider.interpret(request, context)
                record = {
                    "case_id": case["id"], "question": question,
                    "context_sha256": fingerprint(context),
                    "output": answer.model_dump(),
                    "usage": provider.last_usage,
                    "elapsed_s": round(monotonic() - start, 3),
                }
                private_json(run_dir / f"case-{case['id']}.json", record)
                manifest["records"].append({
                    "case_id": case["id"], "status": "valid",
                    "usage": provider.last_usage, "elapsed_s": record["elapsed_s"],
                })
                print(f"case {case['id']}: completed; {record['elapsed_s']}s")
            except ProviderError as error:
                manifest["records"].append({
                    "case_id": case["id"], "status": "failed",
                    "error_category": str(error).split(":")[0][:120],
                    "elapsed_s": round(monotonic() - start, 3),
                    "usage": provider.last_usage,
                })
                print(f"case {case['id']}: failed; stopping without retry")
                break
    finally:
        manifest["status"] = "complete" if len(manifest["records"]) == QUESTIONS and all(r["status"] == "valid" for r in manifest["records"]) else "stopped"
        private_json(run_dir / "manifest.json", manifest)
        print(f"Private records: {run_dir}; status: {manifest['status']}")
    if manifest["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
