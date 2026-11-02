# V4 execution readiness — 2026-11-02

Preparation only. [Scientific amendment](../v4/PROTOCOL.md) introduces exactly no_repeat_ngram_size20 across fresh A/B/C,retains greedy/512/EOS151645 and truncation-as-failure,and explicitly imports the original v3-trained adapter unchanged. No training stage exists. No v3evaluation outputs become v4results. Best-effort physical history remains unknown/overall INCONCLUSIVE;matching returned runtime identities/cleanup and accepted history limitations may permit technical progression,never a PASS/exactly-once claim. Positive restart/reassignment,diagnostics,missing outputs,hash/config mismatch or truncation block progression.

The local launcher verifies the original training report/ZIP against frozen ADAPTER_IMPORT.json and makes an adapter-only bundle (11files plus original manifest/binding). Baseline loads no adapter. C receives that bundle plus only fresh complete v4A/B. Original v3 provenance is not rewritten. Before paid C submission,the local launcher validates the baseline ZIP,all80record hashes,raw token/termination metadata,config,prompts,identity and full effective A/B decoding equality. Remote checks repeat baseline/adapter validation before model imports/downloads. Same proven smoke Python image plus explicit apt_install('git'),L40S/CPU2/RAM32GiB/defaultdisk,retries0,max_inputs1,baseline4200s/C2400s,subprocess1800s,no fallback/resubmission/automatic next stage. Explicit private uploads only,no repository or credentials mount.

## Gates and current requirements

- Passing exact Transformers4.56.2 v4 configuration/repetition regression report binding the current freeze/evaluator/regression/default metadata. No model weights or inference required. Wrong/missing version or v3evidence rejected.
- Private research/runs/ka-v4-acceptance.json:freeze_sha256,accepted=true,modal_history_limitation_accepted=true,post_heldout_repair_accepted=true,import_original_v3_adapter_accepted=true,truthful human_reviewer and accepted_at_utc. Preparation leaves accepted=false with null amendment approval identity/time. Carry prior financial/rubric acceptance with original source/hash and disclose that no new independent review occurred. The user must explicitly accept this frozen v4amendment,new freeze,post-held-out repair status,unchanged original adapter,repetition/EOS risks and512stop;this is distinct from later launch authorization.
- Private research/runs/ka-v4-accounting.json:freeze_sha256,nonnegative finite prior_cost_upper_usd,prior_gpu_seconds_upper,additional_cost_reserve_usd and nullable provider_billed_usd. Include **all** historical v2/v3/smoke/failures/training/failedC/image builds;no budget reset. Current conservative planning:$8historical,4200historicalGPU seconds,$5reserve. This raises v3$7/3900s by$1/300s for failedC(remote96.9056/local113.3557s;configured estimate~$0.06195). Actual attributable provider charges,billableGPU seconds,imagebuild costs/current credits remain unknown. Historical user dashboard observations stay dated/workspace-wide.
- Existing recorded rate$0.00063924/s is a planning assumption,not a new provider quote. Baseline+C6840s including120s overhead each estimates$4.3724016. Total$17.3724016/$20,11040s/14400s planning. Headroom$2.6275984/3360s. Not a cloud cap or bound on hidden physical attempts. Refresh after baseline;stop if later allowance/projected remaining cost/time exceeds gates. Do not reduce reserves to force GO.

## Offline commands

From repository root with already installed CPU environments (no installs/downloads):

```sh
PYTHONDONTWRITEBYTECODE=1 research/runs/ka-v3-generation-environment/.venv/bin/python -B research/knowledge_application_20261101/v4/generation_regression.py --out research/runs/ka-v4-generation-regression
METIS_TRANSFORMERS_PYTHON="$PWD/research/runs/ka-v3-generation-environment/.venv/bin/python" PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/v4/validate_offline.py
METIS_SMOKE_SDK_PYTHON=/Users/xq/.cache/uv/archive-v0/UvqLSAmF-mYD4uRF/bin/python3.12 PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/execution_v4/validate_offline.py
```

## Separately authorized manual submissions — do not execute as a sequence

First A/B only,after all gates and explicit authorization:

```sh
uv run --isolated --no-project --python 3.12 --with modal==1.2.3 python research/knowledge_application_20261101/execution_v4/execute.py --stage baseline --execute --adapter-run research/runs/ka-v3-train-01 --generation-regression research/runs/ka-v4-generation-regression/report.json --acceptance research/runs/ka-v4-acceptance.json --accounting research/runs/ka-v4-accounting.json --out research/runs/ka-v4-baselines-01
```

Only after complete verified v4A/B,accounting update and a separate C decision/authorization:

```sh
uv run --isolated --no-project --python 3.12 --with modal==1.2.3 python research/knowledge_application_20261101/execution_v4/execute.py --stage C --execute --adapter-run research/runs/ka-v3-train-01 --generation-regression research/runs/ka-v4-generation-regression/report.json --acceptance research/runs/ka-v4-acceptance.json --accounting research/runs/ka-v4-accounting.json --previous research/runs/ka-v4-baselines-01 --out research/runs/ka-v4-C-01
```

Each command makes one intentional submission,not one guaranteed physical attempt. Use fresh private directories. No retry,extension,omission,replacement,financial scoring or tuning upon failure. Raw IDs/responses private0600/Git-ignored;do not print them or pass raw IDs to raters. Frozen score.py/keys/rubrics unchanged. No billable work authorized by these instructions.
