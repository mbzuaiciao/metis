# Frozen v3 commands

Preparation only; no scientific runtime command is authorized by this document. Read [PROTOCOL.md](PROTOCOL.md) and [execution prerequisites](../execution_v3/READINESS.md). V2 and all its outputs remain historical; never reuse them as v3 data.

Offline only,from repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/v3/validate_offline.py
PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/execution_v3/validate_offline.py
python3 research/knowledge_application_20261101/v3/evaluate.py --condition A
```

Actual exact-version configuration-only regression (already installed4.56.2 interpreter required; no downloads/install/weights/inference):

```sh
/absolute/path/to/existing-4.56.2-python -B research/knowledge_application_20261101/v3/generation_regression.py --out research/runs/ka-v3-generation-regression
```

The placeholder is not an available interpreter here. Wrong/missing version fails nonzero; no substitute5.x or passing report. Optional METIS_TRANSFORMERS_PYTHON supplies an existing exact interpreter to the offline suite. This exact-version validation must pass before any GPU stage; it is currently unverified.

Use the exact Modal baseline command in execution_v3/READINESS.md only after its mandatory regression/human amendment acceptance/accounting gates pass and execution is separately authorized. Later training/C remain separate explicit decisions and must use fresh v3 paths and complete v3 prerequisites. No retries,512-token extensions,checkpoint selection or alternative settings. Stop on non-EOS output,incomplete arm or any unverified prerequisite. The $20/4h planning bounds include historical v2 failures/setup; actual provider bill caps are not guaranteed.

After all v3 computation completes and GPU cleanup,supply only v3 A/B/C paths to score.py prepare,with private human packets and knowledge-first locking under the unchanged rubrics. Do not mix v2 responses,automatically judge financial content or amend criteria after outcomes. No scoring occurs during preparation.
