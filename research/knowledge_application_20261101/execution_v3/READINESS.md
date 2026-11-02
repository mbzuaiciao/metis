# Modal execution preparation for frozen v3

## Operational eligibility correction — 2026-11-02

The exact Transformers4.56.2 regression has since passed and the user accepted the v3 amendment; the complete A/B baseline has been verified (80/80, no truncations). Earlier preparation-state statements below are retained as historical context, not current blockers.

The frozen scientific protocol requires best-effort history disclosure, not an observed task assignment. The original wrapper additionally required a populated matching call-graph task_id. Saved PENDING snapshots with empty task IDs therefore blocked an otherwise complete baseline. The prior operational sources/report/manifest are preserved byte-identically in [eligibility_v1](eligibility_v1/READINESS.md).

The revised predicate permits unknown assignment only when the prior request records acceptance of the Modal-history limitation. It still requires complete technical status, matching logical call and returned container/input/execution IDs, confirmed cleanup, no diagnostic, no history query error/truncation and no positive reassignment. Conflicting observed task/container IDs reject progression even if the saved summary flag is false. Existing artifact ZIP hashes, scientific freeze, frozen baseline completeness/record hashes/configuration checks, generation-resolution equality and acceptance/accounting gates remain unchanged. Old reports, history and their saved eligible=false fields are never rewritten; the launcher recomputes eligibility under the amended operational policy.

No exactly-once claim, physical-history reconstruction or overall PASS follows. Hidden restarts remain unknown. No baseline rerun or scientific protocol version is needed. One separately authorized training submission may follow, with no automatic C evaluation:

```sh
uv run --isolated --no-project --python 3.12 --with modal==1.2.3 python research/knowledge_application_20261101/execution_v3/execute.py --stage train --execute --generation-regression research/runs/ka-v3-generation-regression/report.json --acceptance research/runs/ka-v3-acceptance.json --accounting research/runs/ka-v3-accounting.json --previous research/runs/ka-v3-baselines-01 --out research/runs/ka-v3-train-01
```

Current planning allowances remain $6 historical cost,3600 historical GPU seconds and $5 additional-charge reserve. Train+C with overhead6840s at the previously recorded $0.00063924/s projects $15.3724016 total,10440s against the4h planning bound. Actual attributable billing,image-build costs and hidden attempts remain unknown; this is no guaranteed billing cap. Reconcile new evidence before each stage.

## Original preparation instructions

Preparation only. [V3 protocol](../v3/PROTOCOL.md) supersedes only the demonstrated generation-resolution defect; execution_v2/v2 and all private failed runs remain unchanged. The same base smoke image plus apt_install("git"),pinned Python environment/model revision,L40S and stage/budget/history/completeness gates remain. The wrapper records the new freeze/config/HEAD/source hashes and full effective A/B/C decoding equality. It never imports v2 financial outputs as v3 baselines or training prerequisites. The original snapshot hashes/image metadata may be reused as model/environment provenance,not as scientific responses.

The source audit establishes the Transformers4.56.2 default-merging defect. The actual-version configuration-only regression is implemented but currently UNVERIFIED: searched local environments and uv cache contain5.x only. No dependency downloads/installs or substitute5.x evidence. **NO-GO for GPU execution until that regression passes.** This is a current validation blocker,not a reason to leave preparation unfrozen. See [offline report](OFFLINE_VALIDATION.md).

First run the configuration-only test in an **already installed** exact4.56.2 environment,with no weights or forward/generate call:

```sh
/absolute/path/to/existing-4.56.2-python -B research/knowledge_application_20261101/v3/generation_regression.py --out research/runs/ka-v3-generation-regression
```

This placeholder path must be replaced by a verified existing interpreter; no such environment was found here. It never installs dependencies. Passing private report.json binds the scientific/evaluation/regression/Qwen-metadata hashes and is mandatory before Modal imports/submission. A missing/wrong version returns nonzero without creating a passing report.

Run standard-library tests with PYTHONDONTWRITEBYTECODE=1. Optional actual-SDK tests use the already installed Modal1.2.3 interpreter via METIS_SMOKE_SDK_PYTHON. Optional exact Transformers test uses METIS_TRANSFORMERS_PYTHON,never a version override. No model/tokenizer inference is involved.

Later private acceptance file research/runs/ka-v3-acceptance.json needs freeze_sha256=new v3 freeze,accepted=true,human_reviewer,accepted_at_utc and modal_history_limitation_accepted=true,truthfully attributed to actual acceptance. No v3 sign-off is fabricated in preparation. Existing financial case/rubric hashes are unchanged; this acceptance concerns the narrow prospective amendment and its new source freeze,not a claim of another independent case review.

Later accounting file research/runs/ka-v3-accounting.json needs freeze_sha256=new v3 freeze,prior_cost_upper_usd,prior_gpu_seconds_upper,additional_cost_reserve_usd,and optional provider_billed_usd. Include **all historical v2/smoke/setup/failures**,not just v3,with dashboard scope/UTC/provenance and explicitly estimated allowances where actuals are unknown. The unchanged rate used by the gate is$0.00063924/s at previously recorded list prices,not a new quote. Remaining stage+overhead allowance11160s gives$7.1339184; no $20/4h budget reset. Old$3/1800s/$5 allowances are historical estimates,not current measured usage. Reconcile before authorizing. No cloud billing cap or guaranteed physical-attempt count.

Exact later first baseline command from repository root,after all prerequisites and separate execution authorization:

```sh
uv run --isolated --no-project --python 3.12 --with modal==1.2.3 python research/knowledge_application_20261101/execution_v3/execute.py --stage baseline --execute --generation-regression research/runs/ka-v3-generation-regression/report.json --acceptance research/runs/ka-v3-acceptance.json --accounting research/runs/ka-v3-accounting.json --out research/runs/ka-v3-baselines-01
```

It intentionally invokes A then B only (40+40 independent calls),not training/C. A truncation/error saves available outputs,stops and never retries. New exclusive private directories; do not reuse v2 paths or substitute responses. One separate training invocation may follow only complete hash-bound v3 A/B; then C only after sole complete training/adapter checks. Pass --previous research/runs/ka-v3-baselines-01 for train and --previous research/runs/ka-v3-train-01 for C,using fresh outputs ka-v3-train-01 and ka-v3-C-01. Refresh accounting and make a new stage decision between invocations; never execute an automatic shell sequence.

Overall status remains INCONCLUSIVE because public physical history is incomplete,independently of returned technical completeness. Missing runtime identity,visible reassignment,diagnostics,history-query errors/truncation or failed cleanup prevent advancement. Unknown assignment alone may advance only with recorded Modal-history acceptance; overall status stays INCONCLUSIVE. No performance/financial-learning claim from smoke or configuration tests; greedy generation can still truncate at512. Full-length memory,actual EOS rates,post-adapter equivalence and accounting remain runtime risks. No Modal,image build,GPU,downloads,inference,training or production changes in this preparation. No commit/push/merge.
