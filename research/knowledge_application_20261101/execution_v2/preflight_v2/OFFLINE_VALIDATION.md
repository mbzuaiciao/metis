# Baseline preflight diagnostics correction — 2026-11-01

Preparation/offline validation only. **GO for a separately authorized diagnostic A/B attempt in fresh ka-v2-baselines-02, conditional on current accounting review.** This is not verification of actual Git/image availability,successful baseline inference or an uninterrupted PASS. No Modal call,image build,GPU,model download,inference or training was performed.

## Original failure and evidence limits

Private baseline-01 report retains FileNotFoundError,remote0.018857s,zero A/B outputs and no Qwen loading. The ZIP contains only baseline-execution.json and matches the returned report. The old wrapper discarded missing pathname,message,traceback and phase; those details cannot be recovered now. No exception text was retrospectively invented. The absence of stdout/arm manifests follows failure before evaluator invocation,not a transfer failure. Prior PENDING call-graph/incomplete-history warnings are separate from technical failure.

Exact-image Git presence remains **unconfirmed**. The recorded image ID matches the successful smoke image. Construction sources and installed Modal1.2.3 image.py show Python slim plus gcc/gfortran/build-essential and pinned Python packages,with no explicit Git installation. Saved reports contain no OS inventory or Git probe. We cannot inspect that image filesystem offline. The source recipe is evidence of omission from declared dependencies,not proof Git was absent at runtime.

Frozen common.py does require Git: enforce_versions calls runtime_metadata,whose Git subprocess catches CalledProcessError but not FileNotFoundError. An offline fixture confirms missing Git propagates to the old remote catch. A missing uploaded file during earlier freeze verification is still a possible explanation of the first run. Frozen common.py is unchanged; no verification bypass or monkey-patch is used at runtime.

## Implemented changes

- execute.py adds timestamped execution phases and a lightweight uploaded-file/Git check before frozen hash/version verification and GPU/model imports. It records all upload path existence booleans and git_available privately,then stops with descriptive FileNotFoundError if either is missing. Existing frozen integrity/version checks still follow.
- Exceptions retain phase,UTC caught time,type,sanitized message and chained stack basename/line/function. Known public frozen filenames are reported relatively and known executables by name. Arbitrary private filenames,credential/env values,paths,URLs,quoted/structured payloads are masked; no environment dump,locals or source lines. Secret-value filtering overrides public-name retention. Subprocess errors retain return code without command/arguments/output. All caught errors force technical incompleteness. Hard kills/write failures remain limitations.
- Default/current manual launch uses fresh research/runs/ka-v2-baselines-02. Baseline still runs A then B only,not train/C. Model revision,prompts,decoding,training parameters,L40S,CPU/RAM,default disk,timeouts,ordinary retries0,max_inputs1,budget gate and INCONCLUSIVE history policy unchanged.
- No image correction applied. **If Git is confirmed missing**, minimum future correction is one explicit apt_install('git') layer on the same successful smoke image,recording the changed image provenance and verifying unchanged Python pins/pip-freeze. No Git shim/fabricated provenance or frozen-source edit. If an uploaded file is missing,repair only its verified upload/path mapping instead.

Prior five execution source/document/report files are archived byte-for-byte under [preflight_v1](preflight_v1/READINESS.md),prior manifest62a2b8947f93c645422018cf2424b8011829f92a415a7bdafe0aa45d0cd4cb04. Archived relative links keep their original-directory meaning. Current [execution_freeze.json](execution_freeze.json) SHA256 **b6966eaf235a37edec24f07c26e3e3304073117a1de781a6ac585f6e25a9b71e** binds3 current artifacts plus5 historical artifacts; this post-freeze report and log append are excluded.

## Offline checks and results

Final wrapper command (existing installed SDK interpreter,never installs):

```sh
METIS_SMOKE_SDK_PYTHON=/absolute/path/to/existing-modal-1.2.3-python PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/execution_v2/validate_offline.py
```

**14 passed,0 skipped,in0.436s;tool0.427s.** Earlier13 tests passed0.379s/tool0.404s before adding exact unchanged-resource AST regression. No failed runs. Real installed Modal1.2.3 native definitions tested with no hydration/app.run/image lookup or build; child audit blocks networking/DNS/subprocesses/model imports and uses empty account config. Placeholder local Image fixture is not substituted into real execution.

Targeted regressions cover missing Git,missing uploaded files,known relative filename/executable retention,unknown private path redaction,environment-secret exclusion,no locals/source content,secret values resembling Git,UTC/phase/stack retention and subprocess return codes. Fake missing-upload runtime failure returns a saved diagnostic ZIP without invoking a subprocess or importing model libraries. Fake A subprocess failure preserves phase/exit1 and stops B; no response replacements. Actual frozen version helper exercised with mocked package metadata and missing-Git error; no actual Git/model call. AST comparison with archived function declaration plus LIMITS/RATE equality confirms resource,time and budget settings unchanged. Default/help remain offline; existing completion/baseline/identity/history/private-artifact controls retained.

Frozen v2 command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/v2/validate_offline.py
```

**16 passed in0.569s;tool0.555s.** Frozen scientific v2 manifest remains4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91. No datasets,labels,rubrics,scoring/evaluation/common code,protocol,pins or smoke artifacts changed.

## Preservation/accounting/decision

All inventoried v2/smoke/private ka-* files match pre-task hashes. Baseline-01 private report SHAaccf799ab78123570901083efcfba703678a7495b69e6268c40c9b32aa3cd9de; ZIP SHA802a1a3375fb3c17795b5fac09ee5d85b286110c21a0305a36599d41887a06ef unchanged; extracted baseline-execution.json unchanged. Acceptance/accounting records untouched,not rescoped or reapproved. Private records remain ignored; no credentials staged. Pre-append log122626bytes/SHA124c57a2c164b6cc9f632d4bed33307cdfbf4320596d0cf104494fb60baea3d4 preserved.

Current planning allowances remain$3prior/1800historicalGPU seconds/$5extra reserve,projected$15.1339184 for historical allowance plus all remaining stages,not an actual bill. Dashboard observation predates baseline-01; reconcile that new usage before authorization and do not reduce allowances merely to pass. This task incurred0 remote operations/submissions/GPUs/builds/downloads/training/inference/optimizer steps/tokens,$0GPU spending; historical billed cost/GPU seconds and assistant tokens/cost/total duration/CPU monetary cost unavailable. No persistent GPU resource created.

**GO only for separately authorized diagnostic -02 under those accounting conditions.** Actual preflight reports will determine whether further image/upload repair is needed; no claim the earlier missing-file cause is fixed. Command in [READINESS](READINESS.md). No automatic resubmission,training or C evaluation. No staging,commit,push or production edit. Stop after reporting.
