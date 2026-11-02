# Confirmed missing Git — image-layer correction, 2026-11-01

**GO for a separately authorized A/B -03 attempt after accounting review. No launch/build performed.** [READINESS](READINESS.md) contains the current command and historical findings. This correction adds only the required Git OS-package layer to the same successful smoke image; frozen scientific artifacts are unchanged.

## Observation and correction

Private baseline-02 report confirms frozen_files_and_git_preflight,git_available=false,missing_filename=git,all21 frozen uploads present. Remote elapsed0.008480s; no Qwen/model import/download,inference or response. Report SHA256d00b4df031aa43c2d12eeb0abf01c56eef0b0598840976620be2ca32d2d9f0f9 unchanged. The earlier -01 discarded pathname remains unrecoverable; -02 supplies the direct evidence for this repair.

`build()` now uses **base_image.apt_install("git").env(...)**,then the existing file layers. Installed Modal1.2.3 image.py documents apt_install("git") and implements apt-get update/install with no GPU requested by default. No package installation executed locally or remotely. Git/OS dependency versions resolve at a later authorized build; availability is not yet measured. No Python reinstall,alternate base image/model/GPU or verification bypass. Existing complete pip-freeze equality and frozen model hashes still must pass at runtime. Preflight Git/file checks and phase/sanitized-error diagnostics retained.

Record actual MODAL_IMAGE_ID when exposed and the declared Git amendment/source smoke image ID in private remote provenance. The derived image ID will differ; this is an explicit system-package amendment,not a claim of byte-identical image contents. Frozen Python dependency pins/revision/inference settings,resource declaration,time limits,budget gate,retries0,single intentional submission and A/B-only baseline behavior unchanged. Default/manual next directory is fresh research/runs/ka-v2-baselines-03.

## Offline validation

Wrapper with already installed Modal1.2.3 interpreter through METIS_SMOKE_SDK_PYTHON,PYTHONDONTWRITEBYTECODE=1: **15 tests pass,0 skips,in0.396s;tool0.381s**. Frozen v2 validator: **16 pass,in0.517s;tool0.498s**. No failures or installs/downloads.

New AST regression asserts exactly one apt_install call,on base_image,sole argumentgit,no GPU/other options; no Python install or shell-run replacement. Native installed SDK spy invokes actual apt_install once for each of three lazy stage definitions,with networking/DNS/subprocess/model imports forbidden and empty account config. No hydration,image lookup/build,app.run or function submission. Existing tests confirm unchanged function configuration/LIMITS/RATE,Git preflight/missing-upload stops,redaction/diagnostics,independent frozen arm controls and no automatic next stage/retry. Placeholder offline images validate API definitions only and are never substituted into real execution.

## Preservation and decision

Previous five execution files are byte-preserved in [preflight_v2](preflight_v2/READINESS.md),prior manifestb6966eaf235a37edec24f07c26e3e3304073117a1de781a6ac585f6e25a9b71e. Earlier preflight_v1 unchanged. Current execution manifest **4518a052d55167a25da75fc1e5d992bdc5232e77a22b780b60a69a5e167eb553** binds3 current files plus10 historical files; this report/log append excluded. V2 freeze4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91 remains unchanged. All inventoried frozen/smoke/private ka-* records,including baselines01/02 and acceptance/accounting,match pre-task hashes. Private records remain Git-ignored. Pre-append log126325bytes/SHA08a6c3c417eca99db8a7ea272c10527faf1b123783919d95d9e75022972c06fa preserved.

**GO for separately authorized -03**,with runtime verification and cost review still required. CPU image-build charges may arise later; retain existing conservative allowances/reconcile prior attempts rather than assume zero spend. No guarantee of remote build success,full-sequence GPU fit,EOS completion or uninterrupted execution. Complete physical history remains unknowable and overall status remains INCONCLUSIVE even when technical checks pass. No training or C stage starts automatically.

This task0 Modal calls/submissions/image builds/GPU allocations/model downloads/inference/training/optimizer steps/tokens,$0 GPU spend. Actual past bill/GPU billing duration,authoring assistant tokens/cost,total task duration and CPU monetary cost unavailable. No production/frozen-protocol change,staging,commit or push. Stop before launch.
