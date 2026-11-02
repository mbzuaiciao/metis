# Execution readiness validation — 2026-11-01

Preparation complete; no scientific workloads submitted. See [financial acceptance table, controls, budget and commands](READINESS.md). No material financial error identified; human whole-protocol acceptance and explicit scope adjudication of eval-01/05/09/14/17 remain outstanding. Assistant review is not independent human adjudication. No labels, keys or scoring criteria changed.

## Evidence and preservation

- Branch research/omission-probe-20261101, observed HEAD9da0334b279396dd8c6f9026840c55ffaed69949. Existing tracked research-log edit and untracked experiment directory preserved. Runtime records current HEAD/status and source bytes even if preparation remains uncommitted.
- Scientific v2 freeze4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91 unchanged. All bound v1/v2 and smoke entries verified;32 directly inventoried existing guidance/log/v2/smoke/private-report files match their pre-task digests before the log append. Earlier failed reports and successful smoke remain byte-identical/private; no raw records added to public artifacts.
- Successful private smoke report SHA5ada9c69104bcb262599358854a3a56338e548772e1c96d8123545528c81ca97 verified. Technical pass, normal returned execution, no observed restart; overall INCONCLUSIVE/physical history incomplete. Measurements summarized in READINESS. No scientific outputs exist from this preparation.
- New execution-only manifest SHA256 **62a2b8947f93c645422018cf2424b8011829f92a415a7bdafe0aa45d0cd4cb04** binds execute.py,validate_offline.py,READINESS.md. This post-freeze report and central log excluded. Runtime/training/scoring sources in v2 and all smoke sources remain unchanged.

## Checks run

Frozen v2: `PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/v2/validate_offline.py` — **16 passed in0.494s**,tool0.498s. These include all20 held-out arithmetic/arm-control checks,60/20 schema/balance,isolated prompts,same A/C, B-only application instruction,512-token greedy config,knowledge/application key separation,truncation stop and complete-baseline training gate. No model judging.

Wrapper: `METIS_SMOKE_SDK_PYTHON=/absolute/path/to/existing-modal-1.2.3-python PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/execution_v2/validate_offline.py` — final **9 passed,0 skipped,in0.311s**,tool0.275s. No installed dependencies/downloads. Earlier9 passed0.289s/tool0.251s before adding hardware/download timing metadata. Earlier7 passed0.375s/tool0.378s; after adding layout/history checks8 passed/1 failed0.317s/tool0.296s because macOS /var resolves to /private/var in the temporary-path expected value. Corrected test to compare resolved paths,9 passed0.292s/tool0.247s. During source inspection the remote wrapper upload was placed under its research repository layout so its computed repository root matches frozen paths; the new relocation test verifies this offline. No remote trial/error or model-driven changes.

Checks:

1. Exact scientific/source/preparation digests; only21 frozen allowlisted files plus wrapper upload, no whole repo/.git/private archive mount.
2. Plan/help and missing-prerequisite execution under socket/optional-import prohibition. Missing human acceptance/accounting rejected before Modal imports/resources; no output directory created. No fabricated approval JSON.
3. $20 target and4h planning checks include conservative prior allowances,remaining-stage time/overhead and extra-charge reserve. Reject budget/time overages,negative and nonfinite inputs. Sample allowances give projected total~$11.13,not an actual bill or maximum.
4. Fake subprocess fixtures execute no model code. Complete A runs before B; a failed A stops B without replacement; snapshot mismatch stops all calls. Private bundle retains available records. Original frozen CLI truncation tests independently prove save-and-stop behavior and training rejects incomplete baselines.
5. One intentional spawn call in the launcher, no local retries/resubmission. Actual installed Modal1.2.3 lazy Function definitions for all three stage timeouts construct with default disk and one L40S, unhydrated/no app ID. Child process blocks sockets,DNS,subprocesses and model imports and uses empty Modal config. The placeholder Image is only a local SDK-definition fixture, never the execution environment; actual launch requires exact successful smoke image ID,without fallback.
6. Actual-image lookup,remote file layering,large artifact transfer and function execution are deliberately untested. Package pip-freeze and13 model file hashes will be verified against smoke before original scripts execute. Exact source/seed/prompt/adapter provenance retained.
7. Strict artifact extraction rejects traversal,absolute paths,symlinks,overwrites and uncompressed bundles>256MiB; pure fixture roundtrip passes.
8. Missing identity/history,observed assignment changes,technical failure,diagnostics or incomplete cleanup prevent advancement. Overall status remains INCONCLUSIVE,not PASS. Best-effort public history cannot rule out hidden physical replays; accepting that scientific limitation requires an explicit human field in the acceptance record.
9. Relocated wrapper imports under the remote research layout and computes the correct repo/v2 paths. No model dependency imported during this check.

## Decision and boundaries

**Conditional GO for A/B baselines only after human whole-protocol and Modal-history acceptance, reconciled prior usage/cost allowances,and separate launch authorization. NO-GO to launch now.** Frozen protocol explicitly requires competent human acceptance; this task has not supplied it. The READINESS table highlights judgment-sensitive grading boundaries without introducing new gold criteria. Human raters/custodian and knowledge-first locking still required after C; no automated LLM judge.

Baseline expected15–60min plus loading,$0.58–$2.69 configured compute under a70min function allowance,not a throughput guarantee. All stages have fixed separate bounds; no automatic next stage. Provider credits not verified and do not expand$20 target. Unknown prior image-build/overhead charges must be reconciled; budget gate is not a cloud cap. Full-length VRAM,generation latency/EOS completion,45-update training,exact-image reuse/transfer/account billing remain runtime risks. The short smoke establishes only its returned technical execution.

Git scope: new execution_v2/{execute.py,validate_offline.py,READINESS.md,execution_freeze.json,OFFLINE_VALIDATION.md}; append research/RESEARCH_LOG.md. Nothing staged,committed,pushed or merged. Existing untracked experiment files remain untracked; no production edits. New scientific calls0,training runs0,optimizer steps0,model downloads0,remote image builds0,GPUs provisioned0,inference tokens0,GPU spend$0 **during this preparation**. Historical smoke model work exists and is not reclassified as zero. Actual historical bill and authoring-assistant token/cost,total task duration/CPU monetary cost unavailable.

Pre-append research-log prefix109324bytes,SHA256d2b73a0bb189a320216ab353770716b77c718463a1a2e3d8eed4a45587ce3eae. Stop after reporting readiness; exact commands are documentation only.
