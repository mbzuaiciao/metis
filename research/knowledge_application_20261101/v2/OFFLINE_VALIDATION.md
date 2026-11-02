# v2 offline validation — 2026-11-01 (America/Los_Angeles)

**Corrections and offline validation complete. No model runtime execution.** Version `metis-knowledge-application-20261101-v2` is separate from the unchanged v1. See [protocol](PROTOCOL.md), [changes](CHANGES.md), [all-case author review](CASE_REVIEW.md) and [v1 inventory](V1_MANIFEST.json).

Final command: `PYTHONDONTWRITEBYTECODE=1 python3 research/knowledge_application_20261101/v2/validate_offline.py`. **16 tests passed in 0.447s**, tool wall 0.474s. Earlier passes: 16 passed in 0.453s (tool wall 0.575s), then 16 passed in 0.450s (tool wall 0.503s). No test failures. One ancillary integrity-check invocation failed during Python parsing because a byte literal contained an em dash; the UTF-8 marker was corrected and the integrity check then passed. The failed check did not execute or modify files. The final pass follows wording/key clarification of alternative USD/EUR posting routes, an exact changed-field audit refresh and a refreshed freeze; no model/data-driven tuning occurred.

[freeze.json](freeze.json) SHA-256: `4deeb8fb0a8babdaf3c776f0859d26ccbe771ac55748fec08da94e1f440c5d91`. It binds **20 source/document entries**, including relative references to the historical review and version index. This report and central research-log addendum are excluded to allow post-freeze recording. [V1_MANIFEST.json](V1_MANIFEST.json) binds all original 16 parent-directory files, including v1 validation and freeze. Every original file still matches its inventory digest. Original v1 freeze SHA-256 remains `ebc1a75f9b871022d4f04cefc483dce2deb37252d6f30980950ea6ec6c3fe705`.

| Dataset | Hedge | Liquidity | Credit | Attribution | Total / sufficient / insufficient |
|---|---:|---:|---:|---:|---:|
| Training | 15 | 15 | 15 | 15 | 60 / 30 / 30 |
| Held-out paired scenarios | 5 | 5 | 5 | 5 | 20 / 10 / 10 |

## Checks and their limits

1. Schema/counts/balance and unique IDs/prompts; original ID/domain/structure-label/sufficiency-label preservation. Disjoint structure labels and direct prior-string reuse checks do **not** establish semantic independence.
2. All config fields other than the study version match v1, including model/revision, seeds, A/B instructions, generation and LoRA/training settings. Requirements pins remain unchanged.
3. Independent two-message conversations, identical A/C messages, B knowledge identical to A, and B application changes only the system instruction. No reference answer, application evidence or theoretical boundary is inserted into knowledge messages. Fixed 40-slot arm order, 120 slots total.
4. Every held-out knowledge prompt asks for the governing relationship; separate general `knowledge_boundary` exists. Overt absent/unknown/not-supplied lists removed from insufficient-case evidence; this lexical check does not certify financial meaning or absence of other cues.
5. Python AST parsing and no top-level model imports. Default plan/help subprocesses run under audit hooks rejecting network connections and optional model/training-library imports.
6. Independent arithmetic anchors for the collar, vector limits, timed funding, FX prefunding, reserve top-up, tranche, allocation, short P&L and arrival cost. Two return-path examples confirm identical monthly arithmetic differences need not give identical annual compounded differences. LoRA parameter estimate retained. These are arithmetic checks, not model or human-quality results.
7. Ignored private-output boundary; freeze integrity and simulated corruption rejection; byte preservation of v1.
8. Human parser rejects invalid/blank scores. Fabricated 120-slot fixtures check composite arithmetic, failures/coverage, matched gains and duplicate rejection. They are **not human ratings**.
9. Separate 60-slot knowledge/application packets and blank sheets; knowledge packets have exactly `knowledge_required` and `knowledge_boundary` as key fields and no application labels, answers or missing-evidence keys. The custodian must still enforce staged release and knowledge-score locking; software packaging cannot prove human blinding.
10. Pure synthetic callbacks demonstrate that truncation/empty-token status saves one record, stops before the next task, counts zero EOS completions, writes an incomplete manifest, and exits a subprocess nonzero. A synthetic generation exception writes incomplete status without a response. No GPU library or real generation is involved.
11. Fabricated complete A/B records pass the training gate; incomplete/started/failed manifests, repeated run directories, truncated, changed or missing records fail. A direct CLI preflight invoked with `--execute` and deliberately invalid synthetic baselines is rejected before optional imports or output creation, under an import/network guard. **No training/model execution occurred.**
12. Local Markdown links, whitespace and Git scope checked separately; only new version/history/review artifacts and a prefix-preserving research-log append are intended changes. The pre-existing log modification and original untracked v1 preparation are preserved. No production/test/build/dependency changes outside this research package.

## Financial review and remaining limitations

The assistant reviewed every revised example and all 20 theoretical keys against the question, scoped answer, missing criteria and rubric; [CASE_REVIEW.md](CASE_REVIEW.md) records 80 rationales plus exact changed fields. This is author review, **not independent human financial adjudication** or an automated LLM judge. The historical v1 review remains an identifiable assistant assessment.

Small purposive n=20, one seed/adapter, related reasoning templates, residual lexical/topic cues, author-dependent keys, theoretical-versus-application difficulty and response-style learning remain. Knowledge-correct behavior is evidence of an accessible relationship, not internal representation. Shared A/C knowledge-correct gains remain compatible with learning other details or procedures. No empirical improvement, financial reliability, causal mechanism or GPU fit is established.

Not exercised: dependency resolution/installation, full transitive lock, actual frozen tokenizer/template/EOS/padding, real collated completion masks/lengths, CUDA/BF16/SDPA kernels, backward gradients, adapter save/reload/device placement, measured peak VRAM, throughput, billing or human ratings. Historical resource/pricing arithmetic is not verification of present GPU compatibility or provider pricing.

**Recommendation: GO for a separately authorized bounded runtime smoke test only; NO-GO for scientific training/evaluation until human financial acceptance and runtime checks pass.** A later smoke test must use training-only or disposable synthetic inputs, preserve the held-out set, specify its own bounds before running and be accounted for within authorized total billing scope. No smoke execution or bypass of the baseline gate is provided here.

Experiment inference calls **0**; inference tokens **0**; model/tokenizer downloads **0**; training runs **0**; GPUs provisioned **0**; GPU spending **$0**. Actual GPU-hours, memory, inference/training latency, model quality, human agreement and billed runtime cost are unavailable. Assistant authoring tokens/cost, total task duration and CPU monetary cost were not captured. Offline fixture durations above are not inference benchmarks. No commit, push, merge, production change or private-archive modification.

Pre-addendum research-log prefix SHA-256: `ee394ac2cc6e3232379a94e4677fe824d1608ead91d80721d05c8c7bf06fe7a7`. The new dated entry preserves those exact bytes; this is not a rewrite of the v1 preparation entry.
