# Metis v0.3: paired financial reasoning ablation

## Procedure and provenance

Initial pair: one live sample per condition, run A then B beginning **2026-10-28 02:14:37 UTC**. A second and final pair ran **B then A**, beginning **2026-10-28 02:24:30 UTC**. Model: **muse-spark-1.3**, endpoint `https://api.meta.ai/v1/chat/completions`. All four calls used temperature **0.2**, maximum completion budget **8,000**, the same strict financial interpretation schema/evidence enum, the unchanged Metis system prompt, and empty conversation history. No retry, alternate model or automatic judge was used. The ablation stopped after these two pairs.

Question in both conditions:

> Given the portfolio's exposures, current market conditions, and relevant historical patterns, what are its principal risks, and why?

The Broad Risk-Off stress was identical: rates **−50bp**, IG spreads **+75bp**, HY spreads **+250bp**, equities **−15%**, EUR/USD **−5%**. Inputs are synthetic; the dated application snapshot is **2025-03-10**, not contemporaneous financial market data.

Local records: `research/runs/20261028T021437037949Z/{manifest,full,evidence_only}.json` for the initial pair and `research/runs/20261028T022430732934Z/{manifest,full,evidence_only}.json` for the replication. These private files are ignored by Git. They contain the full structured responses, actual contexts, question, model, shocks, usage, errors, execution order, and source hashes. This committed report contains reviewed paraphrases and checked figures, not raw model output or credentials. The recorded procedures are `uv run python -m metis.reasoning.ablation` and the same command with `--reverse-order`, respectively; they are documented for reproducibility, not a recommendation for additional runs. Fresh results need not match the sampled wording.

## Exact experimental difference

**A — Full Context:** the existing portfolio/calculations, market observations and causal commentary, historical facts and portfolio interpretations, scenario results and descriptions.

**B — Evidence Only:** the same context minus five fields: `market.commentary`, the three historical `interpretation` fields, and the causal “Growth shock” description on the risk-off alternative. Historical titles, periods, facts, limitations, original source titles/URLs, conventions, all evidence IDs, numerical inputs and calculated outputs remain available. Other alternative descriptions state technical shock assumptions and remain unchanged. No condition label is inserted into the model prompt.

Tests check exact projection equality, every numerical value by its context path, all retained facts/references, and identical wire parameters outside the context. The paired run's numerical-input SHA-256 is `e8dbbc23a1cc7a0665e742cbcf03f4360e01bec34de70cb3093e935a5dbc237a`.

## Initial pair: observations from the recorded responses

Both requests completed without execution errors and passed the existing strict field/constraint and evidence-ID validation. Both distinguished the dated daily loss (**−$560,770**) from the hypothetical stress loss (**−$3,347,000**).

| Checked result | A — Full Context | B — Evidence Only |
| --- | --- | --- |
| Principal loss drivers | Equities and credit; duration only partly offsets losses | Same core conclusion |
| Stress factor attribution | Rates +$2,578,000; credit −$1,975,000; equities −$3,450,000; FX −$500,000 | Same figures, with some rounding in the summary |
| Historical coverage | All three supplied episodes | All three supplied episodes |
| Risks discussed | Liquidity, funding/margin, counterparty, defaults, nonlinearity, curve/basis; US concentration | Similar risks; specifically connects $6m cash to possible margin needs |
| Prompt tokens | 9,400 | 9,241 |
| Completion tokens, including reasoning | 5,659 | 5,478 |
| Reported reasoning tokens | 3,427 | 3,582 |

Token counts and number of references are descriptive metadata, not quality measures. Private reasoning text was not requested or recorded.

## Initial pair: preliminary reviewer assessment — subjective, not automated grading

| Dimension | A — Full Context | B — Evidence Only |
| --- | --- | --- |
| Financial correctness | Correct major totals, exposure signs and offsetting rates/spread legs. HY losses per invested dollar reflect the larger prescribed HY shock; this does not establish higher HY CS01 per dollar. | Correct major totals and useful separation of credit-bond rates/spread legs. One vulnerability item mislabels **−$872,500** as a HY credit loss: that is the **net** HY loss after **+$240,000** of rates gains; spread-only HY P&L is **−$1,112,500**. Its “second-order” description of spreads is also imprecise: CS01 here is first-order. |
| Economic coherence | Coherent explanation of why a growth-scare rally can coexist with risky-asset losses, closely following supplied commentary. | Reconstructs substantially the same interaction from observations and calculations without that commentary. The conclusion is economically plausible but does not reveal the mechanism by which the model produced it. |
| Historical applicability | Tends to repeat supplied interpretations and presents some broad historical hedge/liquidity claims more assertively. | More explicitly anchors 2008 and March 2020 to supplied facts before offering a conditional analogy. Both extend the sparse facts with broader regime claims, especially about 2022 risky-asset weakness; valid citation IDs do not verify every attached claim. |
| Non-obvious risks | Recognizes gross derivative exposure, basis and margin/counterparty risks beyond net P&L. | Similarly recognizes these omissions and mentions available cash. Neither can establish actual collateral shortfall from gross notional and $6m cash without netting/CSA, margin and funding terms. These risk categories are already suggested by the common system prompt. |
| Independent financial judgment | Dependence on context narratives cannot be separated from synthesis in this condition. | Produces the central assessment without the removed narratives, but is still scaffolded by the system prompt, scenario label, selected episodes and pretrained knowledge. One successful response is not proof of independent economic reasoning. |

**Interpretation:** this pair shows no clear deterioration in the central risk assessment after removing context narratives. B remains useful, with a material component-labeling error; A is not clearly superior. There is insufficient evidence to rank overall reasoning quality or claim a causal improvement. The assessment rests on comparison with deterministic inputs and source scope, not the model's own account of its reasoning.

## Reverse-order replication: verified controls and metadata

The runner received only a `--reverse-order` option, with a test covering both execution sequences. The reasoning harness, analytics, workstation, data and inference configuration were not changed. Before either replication call, the model, endpoint, question, system prompt, schema, shocks, evidence IDs, both complete context hashes and numerical-input hash were checked against the original manifest. The saved replication records were then checked for exact context equality against their corresponding original condition. All checks passed. B ran first and A second, without replaying either answer into the other request.

Both replication calls completed without errors and passed strict interpretation/evidence validation. No additional live calls were made after the second pair.

| Pair / condition | Execution position | Prompt tokens | Completion tokens, including reasoning | Reported reasoning tokens |
| --- | --- | ---: | ---: | ---: |
| Original A — Full Context | First | 9,400 | 5,659 | 3,427 |
| Original B — Evidence Only | Second | 9,241 | 5,478 | 3,582 |
| Replication B — Evidence Only | First | 9,241 | 5,053 | 2,721 |
| Replication A — Full Context | Second | 9,400 | 3,703 | 2,009 |

These differences in completion length and token usage are not quality scores or evidence of an execution-order effect.

## Comparison across both pairs — manual financial review

| Check | Original A→B pair | Replication B→A pair | What the evidence supports |
| --- | --- | --- | --- |
| Principal economic risks | Both identify equity and spread losses overwhelming rate gains, plus duration reversal and long-EUR exposure. | Both rank equities, credit/HY, duration reversal and EUR/USD in substantially the same way. | The central portfolio assessment is stable across these four samples; there is no substantive reversal of the conclusion. |
| Numerical headline | Both report daily −$560,770 and scenario −$3,347,000, with the correct factor totals. | Both repeat the correct totals: scenario rates +$2,578,000, credit −$1,975,000, equities −$3,450,000, FX −$500,000. | Core accounting and exposure signs remain correct. This does not validate every numerical or causal statement in the prose. |
| Historical relevance | All three episodes are discussed; B tends to anchor its analogy in supplied facts, while A follows supplied interpretations. | Both still use 2008 for joint credit/equity stress, March 2020 for market-functioning/liquidity risks, and 2022 for the contrasting inflation/rates regime. | Qualitative relevance persists. Some broader claims go beyond the sparse supplied facts; citation-ID validation does not verify claim-level historical support or establish that the portfolio would repeat those episodes. |
| HY net-versus-spread error | B labels −$872,500 as HY credit loss, although it is net HY P&L. | B does **not repeat** that labeling error, but does not state the disputed aggregate HY net/spread pair. A explicitly gives the correct −$1,112,500 HY spread contribution. | The original error is not reproduced in the second B sample. Its omission is not proof that B now consistently distinguishes the components. |
| Other financial issues | B's “second-order” wording for CS01 is imprecise. | B repeats that wording and gives a non-additive DV01 breakdown. A incorrectly makes duration gains conditional on spreads/equities not moving adversely. | Neither condition is uniformly error-free. Detail varies stochastically even when the headline synthesis is stable. |

### Verified errors and qualifications

The audit used unchanged deterministic calculations, not an LLM judge:

- **HY accounting reference:** CS01 $4,450/bp × +250bp gives spread P&L **−$1,112,500**. HY DV01 $4,800/bp × −50bp gives rates P&L **+$240,000**. Their sum is **−$872,500 net HY P&L**. This verifies the original B error and the correctness of replication A's spread amount; replication B does not assert the disputed aggregate amount.
- **Replication B's DV01 presentation:** its observation lists receive-fixed $28,000/bp, UST10 $16,000/bp, IG $12,600/bp, HY $4,800/bp and “net swaps” as components of $51,560/bp. This is not a valid additive decomposition: it omits UST2 and the payer offset and overlaps the receive-fixed swap with net swaps. The correct asset-class decomposition is **Treasuries $18,160/bp + net swaps $16,000/bp + credit $17,400/bp = $51,560/bp**. The quoted total is correct; the component presentation is misleading.
- **Replication A's conditional duration claim:** one vulnerability item makes duration gains contingent on spreads/equities not moving adversely. That is false in this exposure model: **rates P&L = −DV01 × yield shock**, independent of spread and equity shocks. Duration still contributes **+$2,578,000** in Broad Risk-Off despite those adverse moves. It is the portfolio's **net profitability**, not the positive rates contribution, that depends on the other losses. This is a material contribution-versus-total conceptual error even though A reports the right headline figures elsewhere.
- **Terminology and uncertainty:** replication B again calls spread sensitivity “second-order”; the implemented CS01 is first-order. Both conditions raise plausible funding, margin, basis and default risks, but gross notional alone cannot quantify net exposure after collateral/netting or prove a funding shortfall. “Missing tenor/maturity information” should mean missing detailed terms, not that no 2Y/5Y/10Y labels exist. The snapshot remains synthetic even where B loosely refers to an “actual” daily widening.

No new incorrect headline P&L total was found in the replication's cited numerical claims. The verified DV01 presentation flaw and the duration conditionality error prevent a blanket claim of financial correctness.

## Final conclusion, limitations and stopping decision

Across two pairs and two samples per condition, removing the five narrative fields did not visibly change the principal economic conclusions or eliminate relevant qualitative historical synthesis. This is evidence that useful **financial synthesis can occur without those particular prewritten context interpretations**. It is not proof of independent reasoning: both conditions retain a leading system prompt, selected historical episodes, a “risk-off” label and pretrained economic knowledge. The model's own explanatory fluency is not evidence of its internal reasoning process.

The HY error did not recur in replication B, but omission of the disputed aggregate amount limits that finding. New problems occurred in both conditions, so neither longer answers, more references, nor this two-pair comparison establishes overall superiority. There is no justified causal claim that reversing execution order improved or worsened either condition.

Limits remain: very small sample, nonrandomized A→B then B→A sequence, only one synthetic portfolio/scenario, a 159-token condition-specific input-length difference, an unpinned hosted model revision and shared prompt cues. Historical facts are sparse, and neither condition is a calibrated backtest. No automatic quality scores or statistical significance claims are assigned.

**The ablation is complete and stopped after the second paired run.** No further runs, conditions, datasets, providers or evaluation infrastructure were added. Validation: **61 tests pass**, including both runner orders; Git diff confirms analytics, harness, financial inputs and frontend files are unchanged by this replication task.
