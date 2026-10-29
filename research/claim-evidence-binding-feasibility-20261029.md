# 2026-10-29 — Offline claim–evidence binding feasibility probe

## Question and scope
Can a minimal, explicitly typed comparison identify mismatches between the meaning of a financial statement and the structured assertion that an existing verifier checks? This is a **feasibility demonstration**, not an evaluation of natural-language understanding, improved model output, or automated claim extraction. It does not reopen v0.7–v1.1 studies.

## Method
Twelve analyst-authored synthetic statement/mapping pairs (three aligned, five mismatched financial scopes, three unsupported conclusions, one explicitly conditional). The wording's intended `subject / metric / period / stance` and the verifier mapping's equivalent fields were **both manually supplied**. A minimal offline Python rule compared the supplied slots, with a rule not to treat a supported numeric fact as proof of an adequacy or causal conclusion. Categories were `aligned`, `mismatch`, `unsupported` and `conditional`.

Cases:
1. Daily portfolio total vs daily portfolio total — aligned.
2. Treasury rates P&L wording vs portfolio rates P&L mapping — mismatch.
3. Pay-fixed swap rates P&L wording vs receive-fixed swap mapping — mismatch.
4. Daily total wording vs scenario total mapping — mismatch.
5. HY spread-only wording vs HY net scenario mapping — mismatch.
6. Portfolio DV01 wording vs portfolio DV01 mapping — aligned.
7. Positive rates P&L used to prove hedge effectiveness — unsupported.
8. Cash mark used to prove liquidity adequacy — unsupported.
9. Spread move used to prove a forced-selling causal mechanism — unsupported.
10. Hypothetical default-loss possibility expressed conditionally — conditional.
11. Rates gain while overall portfolio loses — aligned.
12. IG DV01 wording vs portfolio-wide DV01 mapping — mismatch.

## Observations
The simple rule classified **12/12 authored fixtures** as their author-assigned categories: 3 aligned, 5 mismatched, 3 unsupported and 1 conditional. This result is nearly tautological because the correct semantic slots were supplied to the checker, and the expected categories were authored using the same rules. It must **not** be reported as 100% accuracy on natural financial language or as an improvement over production.

Production v0.7 already explicitly says original prose is *Not checked*. The research-only v1.0 typed evidence checker likewise requires a human mapping and does not verify arbitrary sentences. Therefore neither baseline is directly comparable on unparsed prose; we **did not execute** the existing repository verifiers against these fixtures. No comparative uplift, precision, recall or generalization can be estimated.

## Decision and stopping rule
**Stop; no production change.** Explicitly supplied semantic labels make discrepancies trivial to detect, but the scientifically interesting part—reliable extraction/binding of meaning from ordinary financial prose—remains untested. A future authorized experiment would need independently labeled, held-out prose with a fixed extractor and error/abstention criteria, plus actual baseline executions, before recommending integration.

## Execution and limits
- Offline Python rules script executed once in the local analysis environment on 2026-10-29; 12 fixtures, all 12 completed. No live Meta/model requests, token usage **0**, model/temperature **not applicable**.
- No extra environment/test harness, model deployment, training, or UI/backend changes. Local execution latency and formal tests against the Metis repository **not measured**.
- Cases were authored and scored using the same explicit slots; no blind review, separate held-out cases, real financial documents or empirical inference about Metis's AI output.
- Prior reports and private model records remain unchanged.
