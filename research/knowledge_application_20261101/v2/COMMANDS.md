# v2 commands for later controlled execution

**Only the offline section is authorized now.** Everything after it requires a separate execution authorization and an operator-enforced four-GPU-hour total limit. No provisioning command is supplied. Use one already authorized 48GB BF16-capable NVIDIA GPU; set provider auto-shutdown and record billing/start/end time before installing/downloading. Do not inspect A/B response content or score anything until C is saved and evaluated. No reruns, retries, tuning or replacement outputs. If any phase fails, retain its stderr/records and stop for a new decision.

From repository root, offline (standard library only, no network/model imports):

```sh
cd /Users/xq/Documents/GitHub/metis
python3 research/knowledge_application_20261101/v2/validate_offline.py
python3 research/knowledge_application_20261101/v2/train.py
python3 research/knowledge_application_20261101/v2/evaluate.py --condition A
python3 research/knowledge_application_20261101/v2/evaluate.py --condition B
python3 research/knowledge_application_20261101/v2/evaluate.py --condition C
```

Plan commands print instructions/inputs, not answers. They do not create output directories. Scripts verify `freeze.json` before planning or execution.

On the **later Linux GPU host**, place the same frozen repository at a chosen path and `cd` to its root; the following paths are relative to it. Check Git status and run the offline validation first. `timeout` below is GNU coreutils (Linux), not macOS. Open a restricted shell and record actual hardware/provider billing details manually in the ignored root. Budget covers environment setup, download and idle time as well as compute; individual phase timeouts do not enforce the aggregate four-hour cap.

```sh
umask 077
export CUDA_VISIBLE_DEVICES=0
mkdir -p research/runs/ka-environment-v2
python3.12 -m venv research/runs/ka-environment-v2/venv
. research/runs/ka-environment-v2/venv/bin/activate
python -m pip install -r research/knowledge_application_20261101/v2/requirements.txt
python -m pip check
python -m pip freeze > research/runs/ka-environment-v2/pip-freeze.txt
nvidia-smi -q > research/runs/ka-environment-v2/nvidia-smi.txt
export HF_HOME="$PWD/research/runs/ka-environment-v2/hf"
```

**Later model download, never during preparation:** exact revision, no remote code. The command prints its local snapshot path into a task-specific variable. Preserve these files without modification for all arms; snapshot file hashes are recorded after download. The model's LICENSE is retained in the snapshot.

```sh
export METIS_KA_SNAPSHOT="$(hf download Qwen/Qwen3-4B-Instruct-2507 --revision cdbee75f17c01a7cc42f958dc650907174af0554)"
python -c 'import hashlib,json,os,pathlib; p=pathlib.Path(os.environ["METIS_KA_SNAPSHOT"]); print(json.dumps({x.name:hashlib.file_digest(x.open("rb"),"sha256").hexdigest() for x in p.iterdir() if x.is_file()},indent=2))' > research/runs/ka-environment-v2/snapshot-sha256.json
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
python research/knowledge_application_20261101/v2/validate_offline.py
```

Non-EOS output/empty token sequence is saved and stops the evaluation with nonzero exit and an incomplete manifest. Training independently rejects incomplete A/B manifests or records before loading a model; `--baseline-runs` is mandatory, even for direct CLI invocation. Execute A then B before training, then train once and execute C on the same device/stack. New exclusive output directories prevent overwriting or resuming. `.stderr.txt` captures early failures that can occur before a manifest is written. Exit-on-error stops the sequence. No peek at generated answers; manifests may be checked for technical completion without reading content.

```sh
set -e
set -o pipefail
timeout 30m python research/knowledge_application_20261101/v2/evaluate.py --condition A --execute --model-path "$METIS_KA_SNAPSHOT" --out research/runs/ka-A-v2 > research/runs/ka-environment-v2/A.stdout.txt 2> research/runs/ka-environment-v2/A.stderr.txt
timeout 30m python research/knowledge_application_20261101/v2/evaluate.py --condition B --execute --model-path "$METIS_KA_SNAPSHOT" --out research/runs/ka-B-v2 > research/runs/ka-environment-v2/B.stdout.txt 2> research/runs/ka-environment-v2/B.stderr.txt
timeout 60m python research/knowledge_application_20261101/v2/train.py --execute --model-path "$METIS_KA_SNAPSHOT" --out research/runs/ka-train-v2 --baseline-runs research/runs/ka-A-v2 research/runs/ka-B-v2 > research/runs/ka-environment-v2/train.stdout.txt 2> research/runs/ka-environment-v2/train.stderr.txt
timeout 30m python research/knowledge_application_20261101/v2/evaluate.py --condition C --execute --model-path "$METIS_KA_SNAPSHOT" --adapter research/runs/ka-train-v2/adapter --out research/runs/ka-C-v2 > research/runs/ka-environment-v2/C.stdout.txt 2> research/runs/ka-environment-v2/C.stderr.txt
```

When computation completes, stop GPU billing before CPU-only human review. A/B knowledge responses should be identical under deterministic execution; disclose any discrepancies. No sample is replaced. Archive manifests, exact source freeze, model snapshot hashes, stderr, wall/startup/loading/download times, GPU billing cost and human-review provenance. If early failure leaves a missing manifest, record the failure in a dated addendum; do not fabricate one to make scoring run.

Prepare a shuffled condition-blind human packet (all three manifests required; incomplete tasks are represented as unavailable):

```sh
python research/knowledge_application_20261101/v2/score.py prepare --runs research/runs/ka-A-v2 research/runs/ka-B-v2 research/runs/ka-C-v2 --out research/runs/ka-human-v2
```

Custodian retains `key.json`, `human_packet.json`, the combined blank sheet and condition folders. First give knowledge raters only `knowledge_packet.json`, `knowledge_scores.csv` and `KNOWLEDGE_RUBRIC.md`. Lock original/adjudicated knowledge scores and hashes before releasing `application_packet.json`, `application_scores.csv` and `RUBRIC.md`. After both phases, join the two sheets by blind ID into the single 120-row `scores.csv`, preserving one header and both source sheets. Populate CSV by actual human review, retain separate rater sheets and adjudication notes, then place adjudicated scores in `research/runs/ka-human-v2/scores.csv`. Scores have no default pass values. Summarize only after scoring and adjudication:

```sh
python research/knowledge_application_20261101/v2/score.py summarize --packet research/runs/ka-human-v2 > research/runs/ka-human-v2/summary.json
```

Write a dated public aggregate report with per-case scores, denominators, failure/usage/latency/cost census, C versus A/B success-rule assessment and shared-knowledge versus newly-demonstrated-knowledge breakdown. Preserve raw responses/ratings privately under the ignored boundary. Append findings including negatives to `research/RESEARCH_LOG.md`. No production changes, deployment, merge or push are authorized by these commands.

## Smoke-test boundary

GO is a recommendation to seek separate authorization, not an execution instruction. No smoke command or bypass of the baseline gate is supplied. Define a bounded training-only/synthetic smoke scope separately before importing models or spending. See the protocol for checks and accounting; do not use held-out prompts or select hyperparameters/adapters from smoke outputs. The commands above run only the scientific study after smoke checks and human acceptance, under separate execution authorization.
