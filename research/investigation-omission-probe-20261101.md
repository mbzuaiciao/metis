# Investigation-guide omission probe — 2026-11-01

## Question

Does the current single-topic `vulnerabilityGuide` surface every pertinent risk when a headline references multiple risk dimensions? This is a **deterministic guide-routing probe**, not a model-inference benchmark, an evaluation of generated explanation completeness, or an authorized production change.

## Source and method

Inspected `frontend/src/investigation.ts` at commit `5f38bc0e9fcb1c1702149908165c35a2583e218a`. The helper matches ordered patterns and returns the **first** matching guide: funding, liquidity, joint market moves, credit, otherwise generic model boundaries. Its output is an analyst reading aid, not a complete financial risk classifier. Six synthetic headlines were deliberately constructed to exercise mixed and single topics. The independent required-topic labels below are author judgments, not blinded ground truth. An isolated Python replay of the four ordered regex selectors produced these selections. No model calls, private data, credentials, API requests, or production modifications.

| Case | Headline | Analyst-relevant domains | Selected guide | Unselected domains |
|---|---|---|---|---|
| 1 | Funding pressure as HY spreads widen | Funding & counterparties; Credit | Funding & counterparties | Credit |
| 2 | Forced sell-off in equities amid thin market liquidity | Liquidity; Joint market moves | Liquidity | Joint market moves |
| 3 | Large debt maturity wall creates refinancing risk | Refinancing | Model boundaries | Refinancing (specific guidance) |
| 4 | Variation margin calls on receive-fixed swaps | Funding & counterparties | Funding & counterparties | None in this scoped test |
| 5 | HY spread widening and issuer default concern | Credit | Credit | None in this scoped test |
| 6 | Equities and credit correlations rise in recession | Joint market moves; Credit | Joint market moves | Credit |

Four of six selected guides omit at least one analyst-labeled domain; this follows from first-match routing and limited patterns. Case 3 receives generic fallback advice that might suggest instrument terms, but no specific maturity/refinancing inquiry. These are **coverage illustrations**, not estimates of omissions in actual LLM answers. A separate AI-generated list of vulnerability items may contain more than one item, each with its own guide: this probe does not assess whole-answer completeness.

## Scientific interpretation

The result confirms a narrow design property: a single returned guide cannot simultaneously provide distinct guidance for multiple matched topics. It does **not** show that the Muse Spark agent missed these risks, that a user would miss them, or that a second checklist would improve real financial decisions. The examples were written with the ordered patterns visible, so they are not held-out cases. No independent labeling or statistical reliability claim is possible.

## Next minimal confirmatory experiment (not executed)

Freeze 6–10 previously unseen case briefs with independently reviewed required evidence questions. Run exactly one baseline Metis interpretation per case with the production settings and capture the entire answer, including all vulnerability items and stage-4 guides. Score coverage of the required questions, unsupported demands, and abstentions before examining any candidate intervention. Then compare one independent, fixed, domain-question checklist applied to the **same saved outputs**. The checklist should point out missing *questions*, not assert missing *losses*; it must not see case labels or a hidden answer key. No feature integration unless a concrete omission is detected and the check adds reliable, non-misleading information. A negative outcome ends the study.

## Disposition

**Research-only.** Do not modify `vulnerabilityGuide`, prompts, verifier, model settings, or UI on this evidence. No inference tokens or cloud expenses. The isolated replay runs locally; no full frontend test suite was run. Leave existing stopped studies and research files unchanged.
