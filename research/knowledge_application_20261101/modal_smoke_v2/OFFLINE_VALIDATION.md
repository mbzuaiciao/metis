# Smoke disk correction 5 — offline validation, 2026-11-01

**GO for one separately authorized retry using fresh `research/runs/ka-modal-smoke-v2-04/`. No Modal launch.** Remove only `ephemeral_disk=51200` from function configuration. All other function options and all runtime code remain unchanged.

## Root cause and smallest correction

The observed third failure is confirmed by the existing private report: InvalidError, app_initialization, zero intentional submissions/no acknowledgement. The supplied message identifies a 51200MiB disk request outside524288–3145728MiB. No GPU training result was received. GPU allocation/billing cannot be confirmed from this local failure record; prior spend is not asserted zero.

The launcher explicitly chose51200MiB (=50GiB) during original preparation. This was a manual setting, with no measured footprint or SDK requirement behind it. It was incorrectly treated as a smaller resource quota. Installed Modal1.2.3 `app.py:707` defaults ephemeral_disk toNone; `_resources.py:15,51` passes the value directly to Resources.ephemeral_disk_mb without a local range check. `_functions.py` carries it in the local function spec and converts it during remote initialization. Thus lazy definition construction did not test the server's bounds.

[Current Modal resource documentation](https://modal.com/docs/guide/resources), checked2026-11-01, describes a default512GiB per-container quota and explicit overrides for larger disks, maximum3TiB. This is general container storage, not a documented L40S-specific minimum. The exact lower bound is evidenced by the observed server error; server code is not installed locally. Removing the unnecessary option selects default storage; no512GiB explicit allocation, persistent volume or new infrastructure is added. Physical worker free space may constrain writes before quota, so sufficiency is an estimate, not a guaranteed reservation.

## Disk estimate and billing

[The pinned Qwen repository](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/tree/cdbee75f17c01a7cc42f958dc650907174af0554) lists8.06GB decimal (~7.51GiB), with three safetensors shards and small tokenizer/config files. No model files downloaded. Planning allowances:

- Snapshot:8GiB.
- Python/Torch/CUDA dependency image and build caches:10–20GiB, unmeasured transitive installation allowance; some layers may not count against writable quota.
- Extra HF/Xet/download scratch/cache:10–20GiB allowance, not measured cache behavior.
- Adapter/tokenizer/output:estimated<0.25GiB for frozen r16 attention-only LoRA; synthetic tokenized data/logs are tiny.

Round up to64GiB total planning space. Runtime uses the same frozen local snapshot for reload, saves the adapter only and disables training checkpoints; no second base-weight download or full-model/optimizer save. Default512GiB quota is comfortably sufficient by estimate, subject to real worker capacity. No runtime changes needed.

The resource guide bills explicit disk through a20:1 disk-to-memory request floor. Even an explicit512GiB would imply25.6GiB memory, below the retained32GiB request, but is unnecessary. Removing the override adds no explicit disk request or persistent-storage charge. [Current list pricing](https://modal.com/pricing) still shows L40S $0.000542/s, CPU $0.0000131/core/s and memory $0.00000222/GiB/s. Conditional900s single-allocation estimate:GPU $0.4878; CPU2/RAM32GiB plus GPU $0.575316. Build/startup/shutdown, egress, plan/tax charges and infrastructure replacements may add cost. No guaranteed maximum or prior-bill claim.

## Offline regression and results

**17 tests pass,0 skipped,0.397s; tool wall0.381s.** Run with existing installed Modal1.2.3/Python3.12 via METIS_SMOKE_SDK_PYTHON and PYTHONDONTWRITEBYTECODE=1; no installs/downloads. Actual SDK child forbids socket/DNS/process/model-library access, clears account overrides, uses empty config, and never enters app.run/_load or any remote method.

New checks reject unsupported explicit sizes0/51200/524287/3145729 and nonintegers before SDK construction/planning. This smoke policy deliberately rejects even supported explicit sizes524288/3145728 pending separate review, rather than silently increasing a quota. Omitted/None disk is accepted. The actual SDK signature default and local candidate spec are None; the actual SDK pure resource converter yields disk0 with protobuf field absent and one GPU. No mocked server acceptance claim.

One initial test-harness failure:16 pass/1 fail,0.373s/tool0.355s. The test expected resource conversion during lazy construction, but SDK1.2.3 defers it until _load. Corrected by calling the actual pure converter directly alongside lazy construction and inspecting its spec. No remote initialization was attempted and no configuration was adjusted to satisfy that assertion.

Existing scaledown guard, exact pins, mask fixtures, callback/frozen-base/gradient/SFTConfig mechanics, resource/one-step limits, diagnostics/redaction, exclusive output, one spawn/no resubmission, conservative INCONCLUSIVE/history interpretation and upload allowlist all pass. Only disk option differs from archived policy_v4; runtime byte-identical. GPU L40S,840s watchdog/function timeout,30s startup,2s scaledown,retries0,max_inputs1,one optimizer step per execution unchanged. No held-out or production access/change.

## Preservation

Six previous preparation files preserved byte-for-byte in [policy_v4](policy_v4/README.md), predecessor manifest a663fcb45d0f8597308f659d89ee7a64cdfa5193c615e99be8df688b6decc8a3. Earlier archives untouched. Current [smoke_freeze.json](smoke_freeze.json): **8a03d5c3bce2df25e449e270069f6336ad8c126e3a233aa01cbba895d2e9a267**,28 matching bound entries. This report/log append excluded from digest.

Frozen v1 manifest14 entries, v2 manifest20 entries and original V1_MANIFEST hashes all match. V2 freeze remains4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91. Prior private reports byte-preserved and Git-ignored, SHA-256:

- -01:d96a27cb013c14923c8a83110c6e6f9c4dab5964dcce2ba8cda6734b484628c0
- -02:c0ca4752bb78214fe457e6691685db2ca38daa5f35816941203e3e2a3de69656
- -03:0126c666f4d30d02792e293b7638d5a977be5314747e56b8500ffb9863828743

No raw records copied into Git-visible artifacts. -04 directory absent; exclusive-create unchanged. No staged files/credentials/private records. Unrelated pending work preserved.

## Decision and limitations

**GO for a separately authorized -04 retry; command in [README](README.md). Stop without launch.** The disk override issue is corrected; real server acceptance, image/dependency resolution, actual free disk/GPU availability/memory/masks/gradients/reload remain untested. Best-effort history still requires overall INCONCLUSIVE even if returned technical checks pass. No exactly-once claim.

This task:0 remote Modal operations/submissions,0 GPU provisioning/downloads/builds/training/inference/model calls or tokens,$0 GPU spending. Actual GPU latency/memory/free disk and prior bill unavailable; authoring assistant tokens/cost,total task duration/CPU monetary cost unavailable. No production/frozen-data edits,staging,commit,push or merge. Research-log prefix105536 bytes,SHA-25670f20adb039770d7c65b2c76800f657032ef995df89d6b5324cb7169964f4b57 preserved.
