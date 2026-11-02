# Bounded Modal smoke preparation — v2, 2026-11-01

**Preparation only. NO-GO for execution under the strict current constraints.** No model download, remote image build, GPU/resource creation, training, inference, paid call, commit or push was performed. This separate directory does not change the [frozen v2](../v2/PROTOCOL.md), its gate, data, keys, rubric or results. Its manifest SHA-256 is confirmed as `4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91`.

## Provider-level blocker, not a permission request

Modal documents that GPU Functions can restart an input after preemption and reschedule containers after crashes. `retries=0`, `max_containers=1` and a single submitted input do not establish a single lifetime execution attempt. Non-preemptible Functions are not supported on GPUs. A replacement attempt gets another per-attempt timeout. Consequently, this preparation cannot honestly guarantee **at most one GPU invocation/attempt, no retries and an aggregate hard 15-minute GPU runtime/cost ceiling** on Modal Functions. The public Sandbox documentation inspected does not establish a GPU no-restart guarantee either; no alternative resource type is silently substituted.

The local `--execute` path is deliberately fail-closed **before importing Modal, constructing an Image/App, creating the output directory or contacting the service**. There is no override flag. Separately approving a GPU run would not by itself remove the original no-retry bound. A provider-supported guarantee, or an explicit user amendment to that bound followed by a reviewed preparation revision, is required first. No extra locks, persistent services or accounting infrastructure were added to try to claim exactly-once cloud execution.

Sources consulted 2026-11-01: [preemption](https://modal.com/docs/guide/preemption), [container-crash retries](https://modal.com/docs/guide/retries), [per-attempt timeouts and accuracy](https://modal.com/docs/guide/timeouts). These are primary provider documents; no GPU behavior was tested.

## Prepared candidate

Files: `modal_smoke.py` (local planner, safety gate and candidate Modal definition), `smoke_runtime.py` (synthetic runtime), `validate_offline.py` (standard-library checks), `smoke_freeze.json` (separate preparation digest binding). No Modal project exists in the repository; this follows the root Python 3.12/uv workflow without editing pyproject.toml or uv.lock. Local Modal client pin is `modal==1.2.3`; its installation/import/signature compatibility is not exercised. Remote image specifies Python 3.12 and all seven exact [v2 dependency pins](../v2/requirements.txt) via `Image.uv_pip_install`. No moving model alias or dependency fallback is allowed. Direct pins are not a full transitive lock; a future runtime records pip freeze/pip check.

The intended GPU is **one NVIDIA L40S, 48GB**, explicitly requested and checked at runtime. This is a disclosed 48GB-class choice for this smoke test, rather than the A40/A6000 examples in v2's resource estimate. An unavailable L40S or failed BF16/device check fails; no fallback GPU, precision or model is selected.

Candidate Modal settings: 840-second function timeout, 30-second startup timeout, one-second scaledown window, no warm/buffer containers, maximum one concurrent container, maximum one input per container, zero ordinary retries, 2 physical CPU cores with a hard 2-core limit, 32GiB host RAM with a hard 32GiB limit and 50GiB ephemeral disk. A process watchdog kills execution at 840 seconds after entry, before importing GPU libraries. Download, hashing, model loading, training and reload all occur inside that watchdog. Images are built without a GPU; build/queue time is outside the GPU execution cap. Provider scheduling, restart and teardown timing prevent a verified aggregate/billing maximum. A watchdog kill can itself trigger the provider's restart behavior, another reason the launch is blocked.

No deployment, schedule, volume, secret, detached job or persistent GPU resource is created by the candidate. `app.run()` is ephemeral. Only three explicitly named files are uploaded: smoke runtime, frozen config and pinned requirements. Automatic source inclusion is disabled; neither the repository, dataset, credentials nor private archives are mounted. Modal authentication, if ever authorized, stays local. Public Hugging Face access uses no injected token. Weights and adapter are ephemeral; the adapter is never a scientific-run adapter.

## Synthetic training scope and expected checks

Model/tokenizer: `Qwen/Qwen3-4B-Instruct-2507` at `cdbee75f17c01a7cc42f958dc650907174af0554`. One unique nonfinancial user example, `Return exactly the label: cobalt.`, with target `cobalt.` and v2's standard system instruction. No study-case files are opened. Four copies of this one example preserve batch=1/accumulation=4 for **exactly one optimizer step**. `max_steps=1` is the sole explicit training-length override; v2's epochs field remains 3 but Trainer stops after one step. This is not a 60-case training run, epoch comparison or financial evaluation.

The candidate checks the actual tokenizer assistant prefix, exact token boundary, expected `<|im_end|>`/151645 EOS and distinct pad token; verifies the actual TRL collator labels mask every prompt token and exactly retain all completion/EOS tokens; uses the unchanged BF16/SDPA, checkpointing, q/k/v/o LoRA, AdamW, learning rate, weight decay, scheduler, warmup, clipping and seeds. It checks LoRA-only trainability/optimizer membership, finite adapter gradients with at least one nonzero tensor, absent base gradients and unchanged frozen tensor mutation versions, and exactly four forward/backward microbatches/one optimizer callback/global step. Initial LoRA A gradients can be zero. **With the retained three-step warmup, the first optimizer learning rate can be zero; adapter weight changes or loss reduction are not pass criteria.** No hyperparameter is changed to force a visible update.

Save/reload is into a fresh BF16 base on the same GPU, after releasing the training model. Reloaded adapter tensors must exactly match saved tensors. One teacher-forced forward pass on the same synthetic text must produce finite CUDA logits. No autoregressive generation occurs, no answer is judged, and there is no numerical-logit equivalence/learning-quality claim. Files are removed with temporary storage cleanup; only metadata and hashes are returned. Peak allocated/reserved VRAM and elapsed download/load, optimizer and reload phases are recorded. A short synthetic sequence does not certify memory at length 2048 or full-study throughput.

Success would return a private `report.json` with `status=pass`, model/revision/config and environment provenance, token/mask/template data, optimizer_steps=1, forward_backward_microbatches=4, nonzero adapter-gradient count, base_frozen_checks_passed=true, reload_exact=true, finite_reload_logits=true, timings and peak memory. Any mismatch raises an exception; timeout/OOM/preemption/import failure is failure/unavailable, not a pass. A sanitized failure report is printed remotely where possible; fatal kills may leave only platform logs. The local wrapper saves failure type without raw exception text. No automatic repeat is attempted by application code.

## Offline and later launch commands

Run offline without installing Modal or GPU dependencies:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/modal_smoke_v2/validate_offline.py
python3 research/knowledge_application_20261101/modal_smoke_v2/modal_smoke.py
```

Proposed manual launch syntax for a later reviewed, separately authorized execution is:

```sh
uv run --isolated --no-project --python 3.12 --with modal==1.2.3 python research/knowledge_application_20261101/modal_smoke_v2/modal_smoke.py --execute --out research/runs/ka-modal-smoke-v2-01
```

**Do not run now. As prepared, this command exits NO-GO before any Modal resource/image operation.** It can install the local pinned Modal client through uv before reaching the script; no such installation was performed during preparation. There is currently no compliant functioning GPU launch command under the no-restart constraint. `uv run ... python` is intentional: using `modal run` on a module that defines an image at import could start image work before a local-entrypoint approval gate. The script never uses a deployment.

## Price estimate, not a guaranteed maximum bill

The [Modal list pricing page](https://modal.com/pricing), consulted 2026-11-01, quotes Functions L40S at **$0.000542/GPU-second** ($1.9512/hour), physical CPU at $0.0000131/core-second and memory at $0.00000222/GiB-second. For **one** allocation billed for at most 900 seconds at list rates, estimated GPU cost is `900*0.000542 = $0.4878` (about **$0.49 GPU-only**). At configured CPU/memory limits, another $0.02358 CPU + $0.063936 memory gives about **$0.5753 compute**, before other charges. This is conditional arithmetic, **not an enforceable maximum**, reservation, discount/credit assumption or spending authorization. Infrastructure restarts invalidate this bound. No region premium or non-preemptible multiplier is requested.

Image-build CPU/memory, billable cold startup/loading, shutdown overhead, network egress over plan allowances ($0.04/GiB listed), tax and account-plan charges may add cost; quota/availability are unknown. No persistent volume storage is requested. Existing credits may offset charges but are not assumed. Model ingress time counts inside the running GPU function's budget; actual transfer throughput is unknown. A model cache/image may remain as provider artifacts but keeps no GPU allocated. See [billing semantics](https://modal.com/pricing) and [physical CPU/resource limits](https://modal.com/docs/guide/resources). The v2 four-hour overall planning allowance is not expanded; later authorized setup/smoke costs must be accounted for, not silently added.

## Remaining blockers and decision

**NO-GO for execution under current strict constraints; prepared for review only.** The provider restart semantics are the principal blocker. Also untested are Modal SDK installation/API/image construction, transitive dependency resolution, public snapshot download speed, L40S availability, CUDA/BF16/SDPA behavior, real TRL masks/gradient hooks and adapter save/reload/memory. These are runtime unknowns, not claims of incompatibility. Human acceptance and all scientific execution gates remain separate. Stop after preparation/offline validation. No permission to relax constraints or execute is inferred from this README.
