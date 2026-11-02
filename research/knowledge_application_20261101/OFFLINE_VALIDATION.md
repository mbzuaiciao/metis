# Offline validation — 2026-11-01

**Preparation complete; no model execution.** Ran `python3 research/knowledge_application_20261101/validate_offline.py`: **11 tests passed in 0.319s** (unittest elapsed; shell tool wall 0.376s). Earlier preparation checks also passed; the final run followed protocol/test/template edits and regenerated the source freeze. No failed offline validation tests occurred. No production test/build was needed for these isolated research files.

Frozen version: `metis-knowledge-application-20261101-v1`; 14 source/data/protocol files. `freeze.json` SHA-256: `ebc1a75f9b871022d4f04cefc483dce2deb37252d6f30980950ea6ec6c3fe705`. This report and the appended central log entry are excluded from that freeze to record validation after hashing. No content change to a frozen file is permitted without a new version.

| Dataset | Hedge | Liquidity | Credit | Attribution | Total sufficient / insufficient |
|---|---:|---:|---:|---:|---:|
| Training | 15 (7 sufficient) | 15 (7) | 15 (8) | 15 (8) | 30 / 30 |
| Held-out paired scenarios | 5 (2 sufficient) | 5 (3) | 5 (2) | 5 (3) | 10 / 10 |

Checks passed:

1. JSONL schema, required fields, unique IDs/prompts, domain counts, three knowledge items per case, sufficiency/missing-information consistency.
2. Disjoint train/held-out structure labels, questions and evidence; no normalized direct reuse of question/evidence/answer strings in four prior tracked case files. Structural rationale is documented separately in `SPLIT_AUDIT.md`; automatic direct-reuse checks are not semantic independence certification.
3. Exactly two messages per response, no target answer or sufficiency-boundary reference inserted into prompts; knowledge has no situation evidence. A/C identical prompts; B knowledge identical to A, application user text identical with only the system instruction changed.
4. Fixed 40-task arm plans, identical shuffled case/probe order, 120 planned generations and frozen seeds/settings.
5. All five Python files parse. No optional training/model libraries imported at module top level.
6. Seven plan/help subprocess invocations under an audit hook that rejects network connects and Torch/Transformers/TRL/PEFT/Datasets/Accelerate imports. Defaults do no inference/training and write no run directories. Plans are exercised inside the validator; no `--execute` was passed.
7. Independent arithmetic checks for held-out collar bounds, signed factor vector, intraday deficit, FX prefunding, reserve top-up, tranche loss, allocation effect, short dividend/borrow P&L and execution cost; architecture-derived adapter parameter estimate. These are identity checks, not empirical financial validation.
8. Ignored `research/runs/` boundary and refusal of outputs outside it.
9. Source freeze verification and rejection of simulated digest corruption.
10. Human score parser rejects blanks, malformed binary lists, booleans and invalid score values.
11. End-to-end fabricated scoring fixtures test anonymous 120-slot packaging, composite passes, demonstrated-knowledge gaps, unavailable-case denominators, paired gains and duplicate/blank-score rejection. Fixtures contain no financial/model responses and are created only in an automatically deleted temporary directory. Their artificial counts are not experimental observations or human ratings.

Additional final checks: all local Markdown links resolve; whitespace checks include untracked files; every previously tracked research file was byte-identical to HEAD before appending the log. The log is subsequently verified as a prefix-preserving append. Existing archives were not edited, moved or regenerated; `research/runs/` remains ignored. No production code, dependency manifests, existing experimental files or Git commits were changed. The pre-existing branch is three commits ahead of its origin tracking branch; this preparation does not commit or push.

Not exercised: package installation/resolution, full transitive dependency lock, tokenizer/chat-template rendering with actual artifacts, completion-mask runtime assertions, GPU memory fit, CUDA kernels, adapter train/save/reload, full evaluation, human rubric review/adjudication, latency/throughput or billed cost. These limitations are explicit; static compatibility is not a runtime guarantee. Seeds/model revision/configuration are frozen but unexecuted. Human acceptance of the assistant-authored financial keys remains outstanding.

Experiment model calls **0**, experiment inference tokens **0**, training runs **0**, model/tokenizer downloads **0**, GPUs provisioned **0**, GPU spending **$0**. Public documentation/model metadata/pricing pages were read to verify the proposed model and API design; no inference endpoint was called. Inference latency, actual GPU-hours, peak VRAM, application/knowledge accuracy, C-over-A/B improvement and human agreement are **unavailable**. Coding-assistant authoring/research token usage, CPU monetary cost and total preparation duration were not captured. Stop after preparation; later command examples confer no execution authorization.
