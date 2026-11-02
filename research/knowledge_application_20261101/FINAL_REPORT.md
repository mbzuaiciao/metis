# Metis financial knowledge-application pilot — final closure

**Closed 2026-11-02 (America/Los_Angeles). No further GPU execution is authorized.** The final v4 comparison is technically incomplete; financial performance remains unassessed. Historical readiness decisions and launch commands are preserved as provenance, not current authorization. No replacement responses, new protocol version or retraining is planned.

## Question, design and version history

**Hypothesis:** can LoRA improve application of financial knowledge already behaviorally demonstrated by the model, particularly recognition of decision-critical missing evidence, beyond a stronger prompt? Knowledge-probe correctness would be behavioral evidence of accessible knowledge, not proof of internal representations. No financial ratings have established that correctness here.

A used the frozen base checkpoint with the standard instruction; B used the same base with stronger evidence-checking instructions for application only; C used the sole final LoRA adapter with A's standard instruction. Knowledge instructions were identical across arms. Each task had a fresh system/user conversation; knowledge answers were not passed into application calls. The design scheduled 20 knowledge and 20 application calls per arm, 120 total. The synthetic dataset comprised 60 training examples and 20 paired held-out scenarios, balanced sufficient/insufficient evidence across hedge, liquidity, credit and attribution domains. Human scoring, knowledge-first locking and unchanged rubrics were predeclared; no automated financial judging was used.

| Version | Change and disposition |
|---|---|
| [v1](PROTOCOL.md) | Prepared, unexecuted; scientific review found dataset/probe/scoring issues. Preserved unchanged. |
| [v2](v2/PROTOCOL.md) | Corrected cases, knowledge keys, scoring separation and incomplete-run handling. Initial submissions failed preflight; baseline-03 saved 33 complete A responses and one truncation, then stopped. Intended greedy settings were overridden by model defaults in Transformers 4.56.2, producing sampling; these outputs cannot supply the intended greedy baseline. |
| [v3](v3/PROTOCOL.md) | Explicit `use_model_defaults=False` corrected resolution, verified on the actual pinned library. A/B completed 80/80; the sole training run completed; C saved 4 complete responses and one 512-token truncation at `eval-10/knowledge`, then stopped. |
| [v4](v4/PROTOCOL.md) | Prospective repair selected **after observing that held-out v3 C failure**: one fixed `no_repeat_ngram_size=20` intervention, identical A/B/C. Fresh A/B/C outputs; unchanged v3-trained adapter explicitly imported. Not an independent replication or untouched held-out confirmation. |

The final scientific freeze SHA-256 is `f1324b29108af9216c9eb140035dcdd99698af21052764e34d902f5493edddb1`; the execution manifest is `ed947bd8f3065f3df957a284a10f32dc0234a2b8e6142246b9e76ba54e2287d6`. All four frozen versions remain unchanged. V4 chronology explicitly permits fresh base evaluations after historical v3 training; no v4 training occurred.

## Verified technical observations

The technical observations below were verified against local execution artifacts under `research/runs/`; raw inference outputs are excluded from Git.

Model: `Qwen/Qwen3-4B-Instruct-2507`, revision `cdbee75f17c01a7cc42f958dc650907174af0554`; one recorded L40S, BF16/SDPA, and the [pinned stack](v4/requirements.txt), including Transformers 4.56.2. Training/data/order seeds were 20261101/20261102/20261103. All v4 arms used verified identical effective greedy decoding, one beam, no-repeat 20, 512-new-token limit, EOS 151645, pad 151643, repetition_penalty=1 and `use_model_defaults=False`.

The returned training run processed **60 examples, 3 epochs, 45 optimizer steps**, supported by 45 finite step records and 45/45 progress (no saved global_step checkpoint). Fixed LoRA: r=16, alpha=32, dropout=0.05, no bias, q/k/v/o projections; AdamW, LR=1e-4, batch=1/accumulation=4, linear schedule/warmup=3, completion-only loss. Training processed 27,549 input/target tokens; mean training loss 3.3022, runtime 37.7024s. Loss is not a financial-performance measure. The adapter has 288 finite tensors / 11,796,480 parameters; all 11 artifact hashes match [the original v3 import binding](v4/ADAPTER_IMPORT.json). Adapter-model SHA-256: `1963de65f0bcc6b3ddbb68d7c243ce0b024938be81ec4b481b4d66f3c6d14751`. No checkpoint selection or retraining; optimizer/RNG resume state was intentionally not saved.

| Final v4 arm/probe | Complete | Truncated | Unattempted |
|---|---:|---:|---:|
| A knowledge + application |20 + 20|0|0|
| B knowledge + application |20 + 20|0|0|
| C knowledge |1|1|18|
| C application |3|0|17|
| **All 120 scheduled slots** |**84**|**1**|**35**|

**V4 A/B completed all 80 responses.** Record hashes, unique case/probe IDs, raw termination records and 87-entry archive integrity passed. All 20 A/B knowledge outputs have identical token sequences, a technical control observation rather than a correctness score. Final C's 109-entry ZIP matches extracted files; all inherited A/B and training artifacts remain byte-identical. Condition C has zero complete paired knowledge/application cases.

**Final failure:** the fifth C call, eval-10/knowledge, returned 512 tokens ending in token 279. There was no EOS 151645 or alternative terminator 151643 anywhere in its raw output. The evaluator saved it, raised TruncatedResponse at evaluate.py:44, and exited 1; the wrapper recorded CalledProcessError in C_subprocess. Git metadata/deprecation warnings were nonfatal. Adapter loading and generation succeeded; this was not an adapter integrity, timeout or artifact-transfer failure.

No exact 20-token sequence repeated in that output, but shorter loops persisted: an 8-token sequence occurred 10 times. Offline reconstruction with the hash-matched prompt, saved tokenizer and actual Transformers 4.56.2 rule checked all 512 prefixes: no constraint violations, and neither terminator was blocked. At 21 prefixes some candidate was banned; without logits this does not show which selections changed. Thus the intervention prevented the targeted exact repetition **but did not restore termination or complete evaluation**.

## Financial results, hypotheses and limitations

**Financial performance: unassessed.** No financial answer inspection, correctness rating, gap classification or scoring was performed for this closure. Complete-response status is not financial correctness. The preregistered success rule required all 120 slots complete with human scores, alongside application gains and maintained knowledge; that requirement was not met. A full A/B/C comparison is unavailable; neither improved application nor financial inferiority has been established.

**Hypotheses only:** the adapter may have learned problematic repetition/stopping behavior. EOS logits/probabilities and the learning mechanism are unknown; the evidence does not establish why EOS was not selected. Training completion, finite tensors and source provenance do not establish financial learning, causality, bitwise retraining reproducibility or LoRA's general effectiveness.

C's early fixed-order stopping creates non-random missingness; complete-only comparisons would be selective. There is only one complete C knowledge response and three complete applications, on different cases. Small author-generated, structurally related scenarios, one model/seed/adapter, prompt cues and response-style learning limit generalization. V4 was chosen after held-out diagnostics; versions must not be pooled or used to replace missing slots. User acceptance is recorded; no additional independent financial review is claimed.

Modal's public call graph is incomplete. Overall status remains INCONCLUSIVE even for technically complete stages; final C additionally has a genuine technical failure. No positive restart/reassignment was detected and cleanup was recorded, but full physical-attempt history cannot be certified. “One training run” means one intentional scientific submission and its returned artifact, not proof that hidden infrastructure never replayed work.

## Final usage and accounting

V4 used 85 recorded generation calls: 12,312 prompt and 26,597 completion tokens, including the truncated output. A/B remote elapsed 570.8965s; final C 80.5936s (local wall 97.7671s), with 19.5120s C generation-loop time. Training's returned remote duration was 99.2135s, distinct from its optimizer-loop runtime. These intervals overlap in scope and are not bills.

Accounting retains 12 local submission reports including smoke/setup/failures across versions: 2,512.8962s summed local walls and 2,367.1297s available returned remote durations. Do not add those sums together or treat them as billable GPU seconds/physical upper bounds. Historical evaluation usage, excluding restored duplicates, was 204 saved calls across v2–v4, 28,883 prompt / 64,292 completion tokens; that is resource bookkeeping, not pooled outcomes.

The final C duration at the previously recorded assumed GPU+CPU/RAM rate, $0.00063924/s, gives **$0.05152**, not a provider charge. Final conservative planning allowance is **$10 historical + $5 unreconciled-cost contingency = $15 against the $20 target**, with 5,400 historical GPU seconds allowed and **zero future stages**. The last increase was +$1 / +300s versus 80.59s returned / 97.77s local; no reserve was reduced to obtain closure. Actual attributable provider charges, billable GPU time, image-build costs and current credits remain unknown. Old dashboard observations are dated/workspace-wide. Neither $15 nor the 4h planning limit is a certified cloud cap; remaining margin authorizes no further spending.

Private `research/runs/ka-v4-accounting.json` records closure; its prior state is preserved in `ka-v4-accounting.before-final-closure.json`. Final metadata evidence and accounting summary are under ignored `research/runs/ka-pilot-closure-20261102/`, permissions 0600. No raw responses, token arrays, adapter binaries or credentials are added to Git.

## Closure and Antigravity audit handoff

**Pilot closed for further GPU execution, with incomplete scientific comparison.** No production integration or positive financial-learning conclusion follows. All versions, runs, failures, approvals, responses and adapter artifacts remain preserved. This report adds a dated conclusion rather than rewriting prior readiness decisions.

An independent Antigravity audit can start with this report, [research memory](../RESEARCH_LOG.md), the four protocol/freezes, [v4 import manifest](v4/ADAPTER_IMPORT.json), and the private closure evidence catalog. Locally inspect original `ka-v4-baselines-01`, `ka-v3-train-01`, `ka-v4-C-01` and their verification reports; recompute hashes, coverage, prepared-config equality and raw-token termination/repetition checks. Separate financial-case validity, technical completeness and billing uncertainty. The closure evidence catalog binds original records; no GPU execution or model inference is needed.

Defensible remaining analyses use existing outputs only: coverage/termination/repetition/latency summaries, integrity/provenance audit, and—if separately requested—condition-blind human financial ratings under the frozen knowledge-first procedure. Truncated/unavailable slots retain blank financial fields, primary nonpass status and exclusion from content-error denominators. Any completed-case analysis must disclose selection and cannot satisfy the original full-comparison claim. No scoring packets or ratings were created here. Provider billing reconciliation can update actual costs when supplied, without authorizing compute. No new experimental run is proposed.
