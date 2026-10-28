# Liquidity shock: competing causal mechanisms

One live paired comparison and manual review, completed 2026-10-28. This is a prompted investigation of financial mechanisms, not causal identification or evidence of general model reliability. No LLM judge, scores, additional runs or benchmark infrastructure were used.

## Exact inputs and settings

- Source snapshot: `e572ac3bc9388d765019a51f9362bb71e767e522`.
- Model: `muse-spark-1.3`; endpoint: `https://api.meta.ai/v1/chat/completions`.
- One request returned A then B in the same completion; no conversation history, retries or demonstration substitution. Execution: 08:22:01–08:22:22 UTC (01:22 PDT), 2026-10-28.
- Existing provider parameters: `temperature=0.2`, `max_completion_tokens=8000`, HTTP timeout 60 seconds; no seed or other sampling overrides. Existing strict `response_format=json_schema`, schema name `causal_exploration`, output type `CausalExploration` with exactly two `Mechanism` objects. Each requires five factor directions/rationales, bounded shocks, alternatives, discriminating evidence, uncertainty and allowed evidence references. No private chain-of-thought requested.
- Usage: 7,871 prompt tokens; 6,099 completion tokens; 13,970 total. Completion metadata reports 4,482 reasoning tokens, included within completion usage; no reasoning trace was requested or inspected.
- Context: the same projection used by the existing causal harness: `assemble_context(Shocks(), "evidence_only")`, retaining `portfolio`, `market`, `daily`, `historical_context`, `conventions`, and evidence excluding `scenario`/`alternatives`. Thus positions, sensitivities, dated synthetic observations, daily calculations, historical facts/limitations and original references remain; prewritten market commentary and historical portfolio interpretations are absent. Inputs are synthetic, dated 2025-03-10, not live observations.
- Added context key `scenario_assumptions` contains the two editable objects below, in A/B order. No `common_rates_bp` key was supplied. These are analyst-selected controls, carried forward from the prior liquidity illustration except for B's yield reversal; they were not estimated by Meta.

```json
[
  {"rates_bp": -50.0, "ig_bp": 60.0, "hy_bp": 150.0, "equity_pct": -6.0, "fx_pct": -1.5},
  {"rates_bp": 50.0, "ig_bp": 60.0, "hy_bp": 150.0, "equity_pct": -6.0, "fx_pct": -1.5}
]
```

Exact `ReasoningRequest.question` (blank lines included):

```text
A liquidity shock is causing forced selling of Treasuries, credit, and equities. Under what conditions could Treasury yields rise rather than fall, and how would that change this portfolio's risk?

Investigate these two mechanisms in order:
A. Flight to safety: Investors seek government bonds. Treasury prices rise and yields fall. Credit spreads may widen and equities decline.
B. Forced liquidation: Investors sell Treasuries to raise cash or meet margin requirements. Treasury prices fall and yields rise. Credit spreads may widen and equities decline simultaneously.

Explain the transmission mechanisms, identify evidence that would distinguish them (including Treasury market depth, dealer balance-sheet capacity, funding spreads, and forced-liquidation pressures), and acknowledge conditions under which both forces operate simultaneously. Distinguish economic hypotheses from established facts. Use the exact editable, uncalibrated scenario assumptions supplied in context.scenario_assumptions: identical credit, equity and FX moves, with only the Treasury yield direction reversed. Explain portfolio risks qualitatively using supplied exposures, without computing new P&L, assigning causal probabilities, or claiming these controlled differences estimate causal effects.
```

The application's `explore()` fixes a common rate move and would reject B. Instead, this experiment invoked the **existing** `HTTPProvider("meta").structured(request, context, CausalExploration, system, "causal_exploration")` directly, retaining strict response, sign/bounds and evidence validation. The research-only system string was the source snapshot's `CAUSAL_SYSTEM` with exactly these replacements; application code and the default constraint were not changed:

```python
system = CAUSAL_SYSTEM.replace(
    "under the SAME supplied government-yield move.",
    "under the two supplied opposite government-yield moves."
).replace(
    "other plausible explanations for the same initial yield observation,",
    "other plausible explanations for either yield direction during the same liquidity shock,"
).replace(
    "Set rates_bp EXACTLY to context.common_rates_bp in BOTH mechanisms to isolate competing cross-asset assumptions around the same initial move. If a hypothesis conflicts with the supplied yield move, describe the conditional circumstances and uncertainty rather than silently changing the anchor.",
    "Use context.scenario_assumptions[0] EXACTLY for mechanism A and context.scenario_assumptions[1] EXACTLY for mechanism B. Only the yield sign differs; identical credit, equity and FX assumptions are experimental controls, not consequences estimated from either narrative. Explain conditions in which safe-haven demand and forced Treasury selling coexist and which force could dominate. Do not claim the scenario difference is an estimated causal effect."
).replace(
    "Treat the shared yield move as a hypothetical observation, separate from the dated snapshot.",
    "Treat both yield moves as hypothetical assumptions, separate from the dated snapshot."
)
```

The Meta response passed existing structural/evidence checks and an additional exact equality check against both supplied shock objects, without rewriting output. Allowed evidence IDs were `portfolio`, `daily`, `market`, `history-2008`, `history-2020`, `history-2022`. Private request/response records, usage, inputs and calculation checks are in ignored `research/runs/liquidity-mechanisms-20261028T082201Z/` (directory 0700, files 0600); credentials and HTTP headers are not recorded. Canonical request-body SHA-256: `815a8fa94c00b9e885859633db061f4b6f11306513a23a6257ce898cb3595f52` (JSON sorted keys, compact separators, UTF-8, `ensure_ascii=False`). No raw inference records are committed.

## Quantitative comparison

The returned assumptions were reviewed and accepted unchanged, then calculated using the existing engine. Full `/api/scenario` results matched direct `calculate(load_positions(), Shocks(...))` results, including position and factor attribution. Both position sums and factor sums matched total P&L; all non-rate shocks and their factor contributions were identical. The JSON inputs above can be edited or reproduced using the existing scenario controls; they remain uncalibrated assumptions, not predictions.

| Assumption / consequence | A: flight to safety | B: forced liquidation |
| --- | ---: | ---: |
| Parallel government yields (bp) | −50 | +50 |
| IG / HY spreads (bp) | +60 / +150 | +60 / +150 |
| Equities / EUR/USD (%) | −6 / −1.5 | −6 / −1.5 |
| Rates P&L (USD) | +2,578,000 | −2,578,000 |
| Spread P&L (USD) | −1,357,500 | −1,357,500 |
| Equity P&L (USD) | −1,380,000 | −1,380,000 |
| FX P&L (USD) | −150,000 | −150,000 |
| **Total P&L (USD)** | **−309,500** | **−5,465,500** |
| Total / current USD 100m NAV | −0.3095% | −5.4655% |

**Financial interpretation checked against calculations:** A's positive rates contribution cushions, but does not eliminate, the loss. Under B it becomes an additional loss alongside credit and equities. B minus A is **−$5,156,000**, exactly `−$51,560/bp × (+50 − (−50))bp` for the supplied net DV01. This is a controlled linear sensitivity difference, **not an estimated causal effect** or an estimate of funding/liquidation costs.

The engine applies its parallel government-rate factor to Treasury holdings, swaps and credit bonds, including the European credit baskets. It does not isolate a cash-Treasury dislocation. The disjoint rates-contribution breakdown is Treasury holdings ±$908,000, rate derivatives ±$800,000 and credit bonds ±$870,000. The pay-fixed swap gains $600,000 in B while the receive-fixed swap loses $1,400,000; the net swap leg loses $800,000. HY spread-only loss stays **$667,500** in both cases; HY net loss changes from **$427,500** to **$907,500** because its rates leg reverses. CS01 remains first-order spread sensitivity, not a default-loss measure.

## Manual review: observations versus assessment

| Evaluation | Observed response | Manual assessment |
| --- | --- | --- |
| Both forces | A described reallocation into governments with functioning intermediation. B described margin/cash-driven sales of safe assets amid thin depth and constrained dealers. | Recognizes the requested distinction and gives financially plausible conditional transmission. The prompt supplied both mechanisms; this is not spontaneous discovery. |
| Rising Treasury yields | B explained sales overwhelming haven buying, lowering prices and raising yields despite risk-off sentiment. | Correct conditional price/yield logic. It does not determine whether these conditions hold in an actual event. |
| Coexistence and evidence | Both acknowledged simultaneous buying/selling and dependence on dealer absorption, funding and liquidation pressures. Proposed evidence included depth/price impact, inventories/fails, funding and FX-basis spreads, margin calls, leverage/basis unwinds, and fund inflows versus leveraged outflows. | Relevant investigative leads, explicitly unavailable. These proxies are neither measurements in this dataset nor identifying tests by themselves. |
| Hypotheses versus facts | Both mechanisms were labeled hypotheses; shock magnitudes were described as uncalibrated controls, with no causal probabilities. Missing live data and ambiguous EUR/USD were explicit. Alternatives included policy repricing, technical demand, supply/term-premia changes and inflation news. | Appropriately separates supplied synthetic facts, conditional narratives and untested alternatives. Valid historical reference IDs do not establish the proposed causal links. |
| Portfolio consistency | A described rates cushioning spread losses; B described rates compounding losses on credit bonds and net long duration. Long equities and long EUR were vulnerable under the imposed moves. No new P&L was asserted by the model. | Consistent with deterministic signs and separate credit/rates legs. Numerical results above are engine verification, not evidence of model arithmetic skill; the model was instructed not to calculate P&L. |

**Qualifications, omissions and errors:** no explicit numerical model error was observed because the response stayed qualitative and copied the controlled shocks correctly. Its A/HY wording links CS01-based losses with greater default/liquidity sensitivity; CS01 alone establishes neither default jumps nor liquidity exposure. Treat these as unmeasured concerns, not supplied analytics. Funding and basis diagnostics lack operational tenor/benchmark definitions or a procedure that would distinguish forced selling from correlated policy/supply shocks. The response does not develop maturity/on-the-run differences, Treasury-versus-swap basis or a calibrated feedback loop from margin calls to prices; the engine cannot quantify those channels either. These are limits of the explanation, not evidence that a rival mechanism is true.

## What this supports, and stopping point

An explicit competing-mechanism prompt elicited the rising-yield channel that the earlier generic liquidity example underdeveloped, including coexistence, relevant evidence and a financially consistent hedge reversal. It supports usefulness for **prompted financial synthesis and investigation design**. Because mechanisms, signs, candidate evidence and fixed magnitudes were largely supplied in the prompt, it does not demonstrate independent causal identification, calibrated severity, predictive accuracy or general reliability. No dominance threshold or actual cause is established. A single paired completion cannot isolate a causal effect of prompt wording relative to the earlier example.

Stopped after this one successful paired request and manual review. No application, analytics, schema, frontend or earlier ablation changes were necessary. Validation: **73 backend tests**, **12 frontend tests**, and the production build pass. Existing Starlette/httpx deprecation and large-bundle warnings remain. No new tests were added for this report-only change.
