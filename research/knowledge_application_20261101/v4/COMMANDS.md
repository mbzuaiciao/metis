# Frozen v4 commands

Offline from repository root,no optional dependency installation:

```sh
PYTHONDONTWRITEBYTECODE=1 research/runs/ka-v3-generation-environment/.venv/bin/python -B research/knowledge_application_20261101/v4/generation_regression.py --out research/runs/ka-v4-generation-regression
METIS_TRANSFORMERS_PYTHON="$PWD/research/runs/ka-v3-generation-environment/.venv/bin/python" PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/v4/validate_offline.py
PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/execution_v4/validate_offline.py
```

Fresh private exact-version report is required by the launcher. See execution_v4/READINESS.md for separately authorized manual baseline and C commands. No training command or automatic sequence. Never reuse an output directory or prior-version response. No financial scoring until C is locked;unchanged score.py consumes only fresh v4A/B/C.
