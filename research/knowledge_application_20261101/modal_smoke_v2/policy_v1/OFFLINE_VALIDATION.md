# Modal smoke preparation: offline validation — 2026-11-01

**Preparation only; NO-GO for GPU execution under the current strict bounds.** See [candidate/commands/pricing](README.md). No SDK installation/import, remote image build, resource creation, model download, training or inference occurred. No model reasoning was judged.

Confirmed v2 freeze SHA-256: `4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91`. All entries bound by that freeze and all 16 original v1 files still match their digests. These preservation checks read local bytes only; no case content was parsed or sent to Modal. The smoke entry point itself reads only the v2 freeze, config and requirements, never datasets or private archives.

Separate [smoke_freeze.json](smoke_freeze.json) SHA-256: `8621a3174e6729bdc9f186803739cdf3e7d3b5e833228ad74b580e11792b506c`. Four preparation sources are bound, with v2 config/requirements digests recorded. This validation report and the central-log append are post-freeze records, excluded from the smoke digest. Frozen v1/v2 files were not edited.

Command executed: `PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/modal_smoke_v2/validate_offline.py`.

**6 tests passed in 0.144s; tool wall 0.255s. No test failures.**

- Exact model/revision/config hash and all seven v2 pins; corruption rejected.
- Syntax and standard-library top-level imports; default plan, help and blocked `--execute` tested under an audit hook that rejects network and Modal/model-library imports. Blocked execution exits code 2 without creating an output directory.
- Pure synthetic token fixtures test exact completion boundaries/EOS and mask rejection for prompt leakage, masked/mismatched completion tokens and missing targets. Actual TRL/tokenizer behavior is not exercised.
- AST/static checks confirm one submitted `.remote` call in the candidate, zero ordinary retries, one container/input, explicit L40S, no warm/buffer containers, CPU/RAM limits, 840-second watchdog/function timeout plus 30-second startup and one-second scaledown, one `.train()` call, `max_steps=1`, BF16 and inherited settings. Static checks do not establish provider exactly-once scheduling or installed API compatibility.
- Explicit three-file upload allowlist; no repository-directory mount, study dataset access, secrets, volumes, deployment, map/spawn/generate or production imports. Synthetic prompt/target constants are fixed and nonfinancial. Private output location remains ignored.
- Mandatory NO-GO gate precedes candidate construction/launch, with no override option. No Modal operation is executed by offline validation. Candidate runtime checks for real gradients, mutation versions, finite logits and exact adapter reload remain unexecuted.

Additional checks: branch `research/omission-probe-20261101`; pre-existing dirty log and untracked v1/v2 preparation preserved. No staged paths, no staging action, no production change, no commit/push/merge. Changes for this task are six files in this separate smoke directory plus one dated prefix-preserving research-log append. No private archive was altered. Local links/whitespace and source hashes checked at completion.

## Negative finding and remaining blockers

The [official preemption documentation](https://modal.com/docs/guide/preemption) says GPU Functions may restart after preemption and cannot use the non-preemptible option. [Crash behavior](https://modal.com/docs/guide/retries) also reschedules containers independently of ordinary user-error retries. [Timeouts](https://modal.com/docs/guide/timeouts) are per attempt and can overrun slightly. Therefore a strict single GPU attempt/no-retry/aggregate 15-minute maximum cannot be guaranteed here. The prepared entry point refuses execution before importing Modal or creating resources. No current compliant GPU-launch command is claimed.

The manual command in README is a future syntax proposal and presently returns NO-GO. A separately approved execution alone does not waive those constraints. Require a provider-supported guarantee or an explicit scope amendment and reviewed preparation revision before any attempt; do not remove the guard casually.

Still unverified: Modal 1.2.3 client/API installation, image construction and transitive packages, snapshot download/network and disk throughput, account access/quota/L40S availability, actual CUDA/BF16/SDPA, tokenizer/template/TRL masks, gradient callbacks, checkpoint save/reload and memory. The first retained warmup step may have LR=0; finite nonzero gradients and optimizer invocation, not parameter improvement, are the intended check. Short synthetic length does not certify full 2048-token memory fit or scientific validity.

## Cost and accounting

[Current quoted list rates](https://modal.com/pricing): Functions L40S $0.000542/s, physical CPU $0.0000131/core/s, RAM $0.00000222/GiB/s. At one allocation lasting at most 900 billed seconds: GPU estimate $0.4878, CPU (2 cores) $0.02358, host memory (32GiB) $0.063936; conditional compute total $0.575316. These calculated figures are not a provider-enforced maximum. Image-build CPU/RAM, startup/teardown overrun, egress above included allowance, taxes/plan charges and infrastructure replacements can add charges. Credits are not assumed. No persistent volume and no region/non-preemptible premium requested.

Observed during this task: **0 GPU invocations, 0 optimizer steps, 0 model forward/generation calls, 0 inference tokens, 0 model/tokenizer downloads, 0 remote builds/resources, $0 GPU spending**. Public documentation browsing only; provider bill/usage, memory, runtime feasibility and all model outputs remain unavailable. Assistant authoring tokens/cost, total task duration and CPU monetary cost unavailable. Offline test durations are not GPU or inference timings.

Pre-append log-prefix SHA-256: `be80f2ecc636402ead60c2cee156797de7b995a08262150451bf345bf4454e12`. Stop after preparation/offline validation.
