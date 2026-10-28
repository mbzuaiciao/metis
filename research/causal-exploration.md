# Causal Exploration: focused manual checks

This is application validation, not another ablation, benchmark, causal discovery exercise or automated model judgment. The v0.3 ablation remains stopped. No scores or LLM judges are used. Raw responses and credentials are excluded from Git; the following is a reviewed summary of synthetic scenarios.

## What is checked

1. **Mechanism consistency:** manually examine whether an economic trigger and transmission plausibly explain the proposed factor directions. Contract tests can check five required factors, bounds and sign consistency, but cannot establish economic coherence.
2. **Alternatives:** manually examine whether the same yield observation can have other explanations and whether proposed evidence could help distinguish them. Two descriptions alone do not establish that either is true.
3. **Numerical integrity:** after explicit acceptance, compare all returned fields with the existing `calculate` engine. Editing an assumption must clear stale results; importing accepted shocks into Independent Shocks must reproduce the same result.

## Live example: recession fears versus inflation relief

Checked in the workstation on 2026-10-28 with Meta `muse-spark-1.3`, `https://api.meta.ai/v1/chat/completions`, temperature 0.2 and completion budget 8,000. One structured request returned both mechanisms. The supplied portfolio/market inputs remain synthetic, dated 2025-03-10. A shared hypothetical −50bp yield move was imposed; it was not inferred from live data. These model-proposed magnitudes are uncalibrated assumptions.

| Assumption / calculated result | Recession fears | Inflation relief |
| --- | ---: | ---: |
| Government yields (bp) | −50 | −50 |
| IG spreads (bp) | +40 | −15 |
| HY spreads (bp) | +150 | −40 |
| Equities (%) | −6 | +4 |
| EUR/USD (%) | −1 | +1 |
| Calculated rates P&L (USD) | +2,578,000 | +2,578,000 |
| Calculated spread P&L (USD) | −1,127,500 | +350,500 |
| Calculated equity P&L (USD) | −1,380,000 | +920,000 |
| Calculated FX P&L (USD) | −100,000 | +100,000 |
| Calculated total P&L (USD) | **−29,500** | **+3,948,500** |

**Observed output:** the recession description connected weaker growth expectations to lower policy-rate expectations, worse earnings, wider credit spreads and weaker equities. The inflation-relief description conditioned tighter spreads and stronger equities on resilient growth. Both marked EUR/USD ambiguous and explained their numerical FX choice as a conditional regional/rate-differential illustration. Alternatives included policy guidance, duration demand and regional weakness. Discriminating evidence included real yields versus breakevens, labor/PMI/earnings revisions and relative US/euro-area repricing, explicitly marked as unavailable.

**Manual assessment:** these are financially plausible conditional explanations for a common nominal yield decline. The hypotheses and discriminating evidence are useful synthesis, not identification of a causal effect. There is no evidence validating the magnitudes or establishing which mechanism applies. Financial outcomes differ because assumed cross-asset shocks differ; the comparison does not estimate an event's causal effect.

**Workflow check:** editing recession equities from −6% to −8% removed both previous calculations. Explicit reacceptance returned recession total **−489,500**, with inflation-relief total unchanged at **+3,948,500**. Direct engine checks matched every listed factor total. Sending the accepted A shocks to Independent Shocks reproduced **−489,500**. The model's original directional discussion and original −6% proposal were retained separately from the edited assumption. Mode switches preserved captured results and drafts.

## Additional focused live check: liquidity stress and custom hypothesis

A second structured request used the same model/parameters and −50bp anchor, comparing **Liquidity and funding stress** with a typed hypothesis, **Supply-chain normalization lowers inflation while growth stays resilient**. This covers the third suggested hypothesis and custom natural-language entry without adding a benchmark or further ablation runs.

| Assumption / calculated result | Liquidity / funding stress | Supply normalization |
| --- | ---: | ---: |
| Government yields (bp) | −50 | −50 |
| IG spreads (bp) | +60 | −15 |
| HY spreads (bp) | +150 | −40 |
| Equities (%) | −6 | +3 |
| EUR/USD (%) | −1.5 | +0.8 |
| Calculated total P&L (USD) | **−309,500** | **+3,698,500** |

**Observed output:** the stress mechanism connected funding pressure, balance-sheet constraints and forced selling to wider spreads, weaker equities and USD funding demand. It proposed obtaining funding spreads/volumes, FX swap basis, Treasury depth/bid-ask/fails and credit-flow data. The custom mechanism connected easing supply costs with lower inflation and resilient earnings, and proposed obtaining freight/delivery-time, input-price, wage, margin and regional policy data. Both offered alternative explanations and missing-evidence caveats. All magnitudes remained labeled uncalibrated assumptions.

**Manual assessment and observed weakness:** the signs are plausible in the specifically imposed falling-yield regime. However, the liquidity opening compresses a dash for cash and Treasury buying into a single falling-yield story without explaining why haven buying would dominate forced Treasury sales. Its uncertainty discussion mentions a yield reversal after policy support but does not directly develop a forced-selling/rising-yield alternative. Thus a structurally valid, sign-consistent answer can still underdevelop an economically important competing channel. This is a useful limitation of the example, not a measured error rate or a reason to assert the opposite outcome. The model did not estimate margin/funding costs, so the stress P&L quantifies the accepted market-factor assumptions only.

Both live requests passed structural/evidence validation on their first attempt. No raw responses are committed and no further examples are required for this milestone.

## Remaining limitations

- Prompting and sign checks do not validate the causal content. The model can omit channels or present plausible but untested explanations.
- The nominal yield anchor does not separate real yields, inflation compensation, term premia or the policy path. Different decompositions could reverse other factor directions.
- EUR/USD requires regional comparisons absent from the supplied data. The arbitrary ±1% assumptions demonstrate this uncertainty rather than resolve it.
- Linear P&L excludes defaults, convexity, liquidity, margin and funding costs. Economic discussion of these channels is not a quantified portfolio loss.
- Historical sources supply qualitative facts, not calibrated scenario coefficients or identified causal estimates. No real-time observations or probabilities are supplied.
- There are only a few hand-reviewed examples with a leading prompt and no independent economic ground truth. Successful structure and plausible prose do not prove independent reasoning.
