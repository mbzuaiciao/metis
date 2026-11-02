# Revised smoke execution policy 2: offline validation — 2026-11-01

**GO for one separately authorized intentional submission. No execution performed.** This user-approved policy amendment permits infrastructure restarts while requiring INCONCLUSIVE operational interpretation whenever history is incomplete. See [README](README.md) and [launcher](modal_smoke.py). The original strict policy, reports and all six source artifacts are preserved byte-for-byte in [policy_v1](policy_v1/README.md); archived relative links retain their original-directory meaning. Original policy manifest SHA-256: `8621a3174e6729bdc9f186803739cdf3e7d3b5e833228ad74b580e11792b506c`.

## Frozen boundaries

v2 freeze SHA-256 remains `4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91`. All bound v2 and original 16 v1 files match their recorded digests. The scientific protocols, datasets, keys, rubric, source hashes and prior results were not modified. Preservation checks read local bytes only; study-case content is not parsed or mounted by the smoke runner. No private archive or production code was touched.

Current [smoke_freeze.json](smoke_freeze.json) SHA-256: `24d747195caab242996f5adfe8f286586a3878cc7cded8a7bfe65fe8ca5a1cd4`. This separately binds four revised smoke sources/documents plus six byte-preserved predecessor files. This report and the dated log append are post-freeze records excluded from its digest. The predecessor source freeze is not overwritten in history.

## Offline checks and exact results

Executed `PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/modal_smoke_v2/validate_offline.py`: **11 tests passed in 0.119s**, tool wall **0.182s**. Earlier revision pass: 10 tests passed in 0.181s, tool wall 0.208s. No test failures. Final pass adds explicit AST equivalence checks for preserved technical training/masking logic. Neither pass imported or called the real Modal SDK or GPU/model libraries.

- Default plan/help stay standard-library-only under import/network audit guards. Mocked `main --execute` reaches the launch function exactly once, with no platform-restart NO-GO guard.
- One intentional `spawn` site, no local submit loop, retries=0, one L40S, one container/input, no fallback/warm/buffer resources. GPU timeout/watchdog 840s, startup 30s, local result wait 900s and one-step setting unchanged. These are per-execution controls, not a complete physical-attempt/global billing guarantee.
- Mocked success, changed container assignment, result timeout, lost submission acknowledgement, graph error and cancellation error each submit once at most. Cleanup requests termination once where a call handle exists. Reusing an output directory fails before another submission. No resources were created by these tests: all call handles, app contexts and result payloads are fabricated Python objects in temporary directories.
- Graph snapshots record documented InputInfo IDs/status. Different task IDs on a single logical call are detected as restart or reassignment. Missing/truncated/error histories, malformed/missing results, interruptions and failed technical checks cannot produce overall PASS.
- Even a complete technical result with one matching observed task is INCONCLUSIVE, because best-effort public history is not an exhaustive physical-attempt ledger. `physical_history_complete=false` is fixed, not accepted from a returned payload or operator flag. `technical_status=passed` is separate from overall status. Exit code 2 means INCONCLUSIVE and must not trigger a local retry.
- Runtime ID collection uses an explicit allowlist. A fake identity token planted in the test environment is not recorded. Startup execution UUID/PID/UTC, app/function/call/input/container/image/region/cloud IDs and termination information are retained where exposed. Signals/watchdog publish sanitized interruption events; hard kills may prevent telemetry delivery.
- Exact completion-mask fixtures pass and invalid masks/EOS/boundaries are rejected. `check_mask`, version verification, `OneStepChecks` gradient/optimizer callback and all SFTConfig arguments are AST-identical to original preparation. EOS, actual collated token IDs, frozen-base mutation versions, exact adapter reload and finite CUDA logits remain checked in runtime source. Actual model execution is still untested.
- Three-file upload allowlist unchanged: synthetic runtime, frozen config, pinned requirements. No production/study-case imports, directory uploads, secrets, volumes, deployments, maps or generation. Private output boundary remains ignored. No files staged; no commit/push/merge.

Additional source/hash, current local links/whitespace and Git-scope checks passed at completion. Archived files are historical bytes; their relative links are not rewritten. Existing pending research-log/v1/v2 work remains preserved. No full production test/build is needed for this isolated policy correction.

## Execution interpretation and limitations

[Modal FunctionCall](https://modal.com/docs/reference/modal.FunctionCall) documents call-graph data as delayed, best effort and potentially truncated; [InputInfo](https://modal.com/docs/sdk/py/latest/types) exposes task/input/call IDs and status, not an exhaustive retry ledger. [Runtime IDs](https://modal.com/docs/guide/environment_variables) identify the returned container, not every prior attempt. Preemption/crash rescheduling remains possible. ID/assignment changes are observable evidence when present; absence of such changes is not evidence of exactly-once execution.

A returned execution can provide technical compatibility evidence, but the overall result remains INCONCLUSIVE with this API's incomplete history. No aggregate one-step, exactly-once, uninterrupted-run PASS or maximum-cost claim is made. One optimizer step is enforced per physical execution; hidden provider replays could repeat it. The user amendment removes the launch blocker, not these observations. No persistent ledger or new infrastructure was added.

The launcher records initial INCONCLUSIVE state before cloud/submission work, retains call identifiers, waits once, requests cancellation/termination, and exits its ephemeral app context. Local process death or cleanup/API failures remain ambiguous; cancellation acknowledgement is not measured physical GPU shutdown. Account/platform records must be retained after an authorized run. Still unverified: pinned SDK signatures, image/dependency resolution, model download speed, device availability, BF16/SDPA, real TRL masks/gradient hooks, save/reload and memory. All frozen model/training settings remain unchanged. This preparation is not authorization to launch.

## Pricing and accounting

[Modal list pricing](https://modal.com/pricing), reviewed 2026-11-01, remains $0.000542/L40S-second, $0.0000131/physical-core-second and $0.00000222/GiB-second. Conditional single-allocation/900-billed-second estimate: **$0.4878 GPU-only**, **$0.575316 including configured CPU/RAM**. Not a maximum bill: infrastructure replays, image-build resources, startup/teardown, egress above plan allowance, taxes/plan fees and cancellation failures may add charges. No credit assumed; no persistent volume requested. v2's overall planning allowance is not expanded.

This revision performed **0 intentional or physical GPU submissions, 0 optimizer steps, 0 model forward/generation calls, 0 inference tokens, 0 downloads, 0 image builds, 0 Modal resource operations, $0 GPU spending**. Public documentation browsing and synthetic offline fixtures only. Actual provider history/usage, GPU memory/latency, runtime compatibility and billed cost unavailable; assistant authoring tokens/cost, total task duration and CPU monetary cost unavailable.

Pre-append log-prefix SHA-256: `77489fbd26419b629841a32c2781882bc779b74e994a2c91d9f660f65c6a46b3`. Stop after implementation/offline validation.
