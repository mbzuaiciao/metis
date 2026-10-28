# Metis v0.3: paired financial reasoning ablation

## Procedure and provenance

One live sample per condition, run A then B beginning **2026-10-28 02:14:37 UTC**. Model: **muse-spark-1.3**, endpoint `https://api.meta.ai/v1/chat/completions`. Both calls used temperature **0.2**, maximum completion budget **8,000**, the same strict financial interpretation schema/evidence enum, the unchanged Metis system prompt, and empty conversation history. No retry, alternate model or automatic judge was used.

Question in both conditions:

> Given the portfolio's exposures, current market conditions, and relevant historical patterns, what are its principal risks, and why?

The Broad Risk-Off stress was identical: rates **−50bp**, IG spreads **+75bp**, HY spreads **+250bp**, equities **−15%**, EUR/USD **−5%**. Inputs are synthetic; the dated application snapshot is **2025-03-10**, not contemporaneous financial market data.

Local records: `research/runs/20261028T021437037949Z/{manifest,full,evidence_only}.json`. These private files are ignored by Git. They contain the full structured responses, actual contexts, question, model, shocks, usage, errors, execution order, and source hashes. This committed report contains reviewed paraphrases and checked figures, not raw model output or credentials. Reproduce the procedure with `uv run python -m metis.reasoning.ablation`; a fresh result need not match the sampled wording.

## Exact experimental difference

**A — Full Context:** the existing portfolio/calculations, market observations and causal commentary, historical facts and portfolio interpretations, scenario results and descriptions.

**B — Evidence Only:** the same context minus five fields: `market.commentary`, the three historical `interpretation` fields, and the causal “Growth shock” description on the risk-off alternative. Historical titles, periods, facts, limitations, original source titles/URLs, conventions, all evidence IDs, numerical inputs and calculated outputs remain available. Other alternative descriptions state technical shock assumptions and remain unchanged. No condition label is inserted into the model prompt.

Tests check exact projection equality, every numerical value by its context path, all retained facts/references, and identical wire parameters outside the context. The paired run's numerical-input SHA-256 is `e8dbbc23a1cc7a0665e742cbcf03f4360e01bec34de70cb3093e935a5dbc237a`.

## Observations from the recorded responses

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

## Preliminary reviewer assessment — subjective, not automated grading

| Dimension | A — Full Context | B — Evidence Only |
| --- | --- | --- |
| Financial correctness | Correct major totals, exposure signs and offsetting rates/spread legs. HY losses per invested dollar reflect the larger prescribed HY shock; this does not establish higher HY CS01 per dollar. | Correct major totals and useful separation of credit-bond rates/spread legs. One vulnerability item mislabels **−$872,500** as a HY credit loss: that is the **net** HY loss after **+$240,000** of rates gains; spread-only HY P&L is **−$1,112,500**. Its “second-order” description of spreads is also imprecise: CS01 here is first-order. |
| Economic coherence | Coherent explanation of why a growth-scare rally can coexist with risky-asset losses, closely following supplied commentary. | Reconstructs substantially the same interaction from observations and calculations without that commentary. The conclusion is economically plausible but does not reveal the mechanism by which the model produced it. |
| Historical applicability | Tends to repeat supplied interpretations and presents some broad historical hedge/liquidity claims more assertively. | More explicitly anchors 2008 and March 2020 to supplied facts before offering a conditional analogy. Both extend the sparse facts with broader regime claims, especially about 2022 risky-asset weakness; valid citation IDs do not verify every attached claim. |
| Non-obvious risks | Recognizes gross derivative exposure, basis and margin/counterparty risks beyond net P&L. | Similarly recognizes these omissions and mentions available cash. Neither can establish actual collateral shortfall from gross notional and $6m cash without netting/CSA, margin and funding terms. These risk categories are already suggested by the common system prompt. |
| Independent financial judgment | Dependence on context narratives cannot be separated from synthesis in this condition. | Produces the central assessment without the removed narratives, but is still scaffolded by the system prompt, scenario label, selected episodes and pretrained knowledge. One successful response is not proof of independent economic reasoning. |

**Interpretation:** this pair shows no clear deterioration in the central risk assessment after removing context narratives. B remains useful, with a material component-labeling error; A is not clearly superior. There is insufficient evidence to rank overall reasoning quality or claim a causal improvement. The assessment rests on comparison with deterministic inputs and source scope, not the model's own account of its reasoning.

## Limits and smallest next step

One stochastic sample per condition, fixed A→B order, a 159-token input-length difference, an unpinned hosted model revision, and shared leading instructions limit attribution. The selected episodes and “risk-off” label already cue familiar narratives. Historical facts are sparse; neither arm is a historical backtest, and no market-data ingestion was added. The common prompt even asks for recession/inflation contrasts and specific omitted risks, so this experiment isolates **context-narrative dependence**, not fully unprompted judgment.

The smallest justified next step is one additional paired sample with the order reversed, using the same snapshots/settings and the same manual accounting checks. That would test whether the core result and the net-versus-spread error persist before adding any new experimental condition.
