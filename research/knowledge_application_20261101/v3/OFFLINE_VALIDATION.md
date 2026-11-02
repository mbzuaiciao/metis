# Frozen v3 offline validation — 2026-11-01

**V3 preparation/freeze complete. NO-GO for GPU execution pending actual Transformers4.56.2 regression,new amendment acceptance and reconciled accounting.** [Protocol/amendment](PROTOCOL.md),[execution prerequisites](../execution_v3/READINESS.md). No model generation/training/download or remote operation in this task.

## Source freeze and scope

Scientific freeze SHA256 **4a65d1ed2eab32e24fe228d0f79ed045a4b4135de6a6c465f5c3ec249efda983**,23 bound source/document/metadata files. Execution freeze SHA256 **8e7011211c9913090db946c01a5c82b0e9c4c7555149af62474d21fa7c2031a6**,separately binds wrapper/tests/readiness and the scientific freeze. This post-freeze report,execution report and research-log append are excluded from their manifests. Original v1/v2,execution_v2,smoke and all private failed runs match pre-task content hashes. V2 manifest4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91 unchanged. V2_MANIFEST.json binds every original v2 file; V1_MANIFEST retains original16-file inventory. No v2 output is imported as v3 evidence. Response content was not graded or used to select changes.

MATCHED_CONTENT.json records13 byte-identical v2/v3 files,including common.py,train.py,score.py,requirements,both rubrics and both datasets. All60 training and20 held-out records,knowledge/application prompts,keys/labels/targets,three arms,seeds,LoRA/optimizer settings and scoring thresholds unchanged. Config differs only in study identity. Relevant matching hashes:

- train.jsonl:e4ad10f6ab41e298388ca6c926769ce979024af0573b1eac1705ca7ba5eead89
- heldout.jsonl:bdd2f01bf950056ff8a4e4382d16f81e282fcd01b35181a955faaab60e7bc6f7
- RUBRIC.md:40835429a9fb60e16d8aeb2ae32509db228cdc17b9df28449f342352f31f41f9
- KNOWLEDGE_RUBRIC.md:e03fef33c139464842d248395c88f497e070b15669ac4230de90c32cd0efde47

QWEN_GENERATION_DEFAULTS.json is238bytes of model configuration metadata reconstructed from the already audited public text,not a new dataset/model download. Its835fffe355c9438e7a25be099b3fccaa98350b83451f9fd2d99512e74f1ade48 digest matches the prior snapshot record.

## Correction and exact-version boundary

Evaluate.py passes use_model_defaults=False directly to generate and actual _prepare_generation_config. It asserts prepared greedy mode/False/one beam/512/EOS151645/pad151643/repetition1/cacheTrue and actual tokenizer token IDs; records requested/effective config and resolution policy. Every arm shares the same helper. Wrapper checks full prepared A/B/C config equality and refuses unverified exact-version evidence before any GPU submission. Original collect function is AST-identical: saves non-EOS/empty outputs,marks incomplete,exits nonzero and stops further tasks. No forced EOS,token extension,retry,exclusion,financial-key change or training-code change.

Actual pinned regression is implemented in generation_regression.py using installed GenerationMixin._prepare_generation_config bound to a config-only stub,with no weights/forward/generate calls. It must demonstrate v2 sample versus v3 greedy and token/beam/penalty/cache/ABC consistency,then bind passing evidence to this exact freeze and source hashes. Runtime may not substitute a5.x regression.

**UNVERIFIED exact-version execution:** inventory of local uv cache/Python locations found only Transformers5.15.1,5.16.1,5.18.0. No4.56.2 environment/package was found. User explicitly directed preparation to continue without downloads and without treating5.x as equivalent evidence. The default interpreter's configuration-only script returned exit2 with status unverified/PackageNotFoundError and created no report/output directory. No exact4.56.2 installation or runtime method execution is claimed. Source audit supports the fix; a passing real-library regression is still required before GPU execution. No mocked guard test below substitutes for it.

## Offline tests actually run

V3 suite `PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/v3/validate_offline.py`: **19 scheduled,18 pass,1 explicitly skipped exact-version test**,final0.576s/tool0.567s. Earlier same18pass/1skip0.567s/tool0.572s. Checks include inherited16 scientific schema/arm-order/isolated-prompt/knowledge-key/scoring/truncation/training-baseline/private-output/integrity checks,byte-identical v2 inputs/protocol inventory,unchanged collect,explicit generate keyword,and fail-closed prepared-config guard. Synthetic config objects test validation only,not Transformers semantics.

Execution suite with installed Modal1.2.3 via METIS_SMOKE_SDK_PYTHON and PYTHONDONTWRITEBYTECODE=1: **16 pass,0 skipped**,final0.471s/tool0.461s. Native lazy Image/Function/apt_install declarations validated under socket/DNS/process/model-import prohibition and empty Modal config; no lookup/hydration/build/app.run/remote call. Guards reject v2/wrong-version/unverified regression evidence,budget/time excesses,unsafe ZIPs,incomplete baselines,missing Git/files and bad identities/history/cleanup. A/B decoding-profile drift fixture returns incomplete instead of advancing. Function options/LIMITS/RATE match execution_v2;no training-setting override.

One initial wrapper test-harness failure15pass/1fail0.490s/tool0.494s retained here: a relocated-path assertion still expected /v2 after copying the test. Corrected expected v3 path;16passed0.379s/tool0.363s,then16passed0.407s/tool0.472s after adding profile-drift fixture. No GPU/runtime experiment used to tune the fix. Final token-ID assertion caused source-freeze refresh and the final passes above.

## Exact file inventory

All added in v3/: CASE_REVIEW.md, CHANGES.md, COMMANDS.md, INHERITED_V2_PROTOCOL.md, KNOWLEDGE_RUBRIC.md, MATCHED_CONTENT.json, OFFLINE_VALIDATION.md, PROTOCOL.md, QWEN_GENERATION_DEFAULTS.json, RESULTS_TEMPLATE.md, RUBRIC.md, SPLIT_AUDIT.md, V1_MANIFEST.json, V2_MANIFEST.json, common.py, config.json, evaluate.py, freeze.json, generation_regression.py, heldout.jsonl, requirements.txt, score.py, train.jsonl, train.py, validate_offline.py.

All added in execution_v3/: OFFLINE_VALIDATION.md, READINESS.md, execute.py, execution_freeze.json, validate_offline.py.

Only an append to research/RESEARCH_LOG.md changes an existing file in this task; all pre-existing unrelated pending changes remain unchanged. No changes to v1,v2,execution_v2,smoke or private archives. New directories are untracked until separately authorized Git action; nothing staged/committed/pushed/merged. Private v3 acceptance/accounting/regression/baseline/training/C artifacts are not fabricated or created.

## Remaining risks and decision

NO-GO for execution until exact installed4.56.2 regression passes and its private report is supplied through --generation-regression; actual amendment acceptance and current accounting must bind the new freeze. Use the exact later baseline command in execution_v3/READINESS.md,with fresh ka-v3-baselines-01. It runs A/B only. V2 approval is not relabeled v3; human acceptance can refer to unchanged case/rubric hashes and this narrow implementation amendment without inventing an additional independent financial review.

512-token truncation remains possible under greedy; model will not be forced to emit EOS. Sampling/verbosity causation is not established by the earlier single truncation. V2/v3 cannot be pooled or treated as a controlled LoRA comparison; v3 primary analysis uses only its own frozen120 slots. Hardware nondeterminism,full-length memory/post-adapter runtime,small purposive sample,related templates,knowledge-accessibility versus internal-representation limits,human rating/blinding and hidden Modal replays remain. Full GPU/provenance checks still run later,not during this task.

Budget remains$20target/4GPUh total including all historical v2/smoke/setup/failures; no reset or new cost guarantee. No source approvals,pricing/credit balances or measured billing invented. This preparation0 remote operations/builds/GPUs/downloads/inference/training/model calls/optimizer steps/tokens,$0GPU spending. Actual prior bill/GPU duration,assistant authoring tokens/cost,total preparation duration and CPU monetary cost unavailable. Pre-append log129288bytes/SHA6be8bfe057b920bfa02ab36f6775d0f2af812768a8ce12c148fd2bcf74199902 preserved. Stop after offline preparation.
