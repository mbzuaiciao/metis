# Financial reasoning observer experiment

## Protocol fixed before live inference

Research question: does one independent Meta observer and one revision add useful financial corrections beyond the existing deterministic verification annotations? This is a fixed ten-case research run, not a product feature or general agent framework. Case definitions/expectations below and in `observer-cases.json` are defined before the first live call. Results will be appended without changing prompts or expectations.

### Conditions and accounting

- **A:** one initial Muse Spark explanation.
- **B:** the exact same initial explanation plus v0.7 verification annotations, without any prose change or model call.
- **C:** that initial explanation, one independent observer review, then one revision with observer feedback only.
- **D:** the same initial explanation and reused independent observer review, then one separate revision with both observer feedback and the original deterministic findings.

The observer never receives deterministic verdicts or case expectations. C/D share the same observer output because its inputs are identical. Every main/observer/revision receives the same original factual evidence for its case. Revision instructions require evidence-based acceptance, qualification or rejection of objections, not automatic obedience. Original, feedback, each revision and verifier findings are kept separately. C/D revision resolutions are self-reports, not grades.

One complete case costs four unique calls (initial, observer, C revision, D revision). Per-condition dependency counts are A=1, B=1 plus local verification, C=3, D=3; shared calls must not be double-counted in the study total. B cannot improve its explanation by definition. **D versus B also includes a revision step**, so without a verifier-plus-revision-only arm this design cannot identify the observer-only causal contribution. No fifth condition is added.

### Model inputs, limits and reproducibility

Use existing `muse-spark-1.3` at the configured Meta chat-completions endpoint, temperature 0.2, completion budget 8,000 (reasoning included), HTTP timeout 60s; no seed or sampling overrides. Exact role prompts and schemas are in `observer_experiment.py` and are frozen in the private preflight protocol before inference. Initial output uses existing `Interpretation`; observer feedback is a small bounded objection schema with numerical/economic/causal/evidentiary categories and error/unsupported/omission/alternative types. Zero objections are valid. Revision extends `Interpretation` with an objection-ID decision list. It is not a new analysis loop.

Context construction whitelists source portfolio rows, NAV, signed sensitivities, dated synthetic current market levels and mathematical conventions. Daily/scenario cases add authoritative calculations and explicit shocks; case 08 adds two rate-only calculations, with the first also mapped as `scenario` for v0.7. Case 06 has no daily/scenario directional priming. No historical narratives, market commentary, preset economic descriptions, previous reports or earlier experimental outputs are supplied. The model sees only the current user question, factual context and applicable original/feedback records. Expectations and grading notes are never serialized into model inputs. Source data and context hashes are recorded. The single generic adapter correction permits root-level evidence IDs on the observer schema; it preserves allowlist checks and existing application behavior.

Hard bounds: maximum ten cases / 40 unique calls / 1,800 wall seconds / 600,000 reported total tokens, and stop after three consecutive failed inference stages. No retries, prompt optimization, recursive discussion or fabrication. Initial failure leaves B/C/D unavailable; observer failure leaves C/D unavailable; either revision can fail independently. Every failure and incomplete condition must be reported.

### Predefined evaluation criteria (human review)

1. **Financial correctness:** flag a material numeric/sign/attribution error against engine evidence; valid rounded values within v0.7 tolerances are not errors. Separately note misleading prose/mapping disagreement.
2. **Unsupported conclusions:** flag material claims of adequacy, causal identification, observed events or risk magnitudes not established by the supplied data. Conditional possibilities explicitly labeled unknown are not errors.
3. **Coverage:** Complete / Partial / Not applicable against the case-specific economic distinctions below; no reward for length, confidence or citation count.
4. **Correction:** count initial material issues or required omissions actually repaired by C/D, not merely objections acknowledged.
5. **Regression:** record a newly material error, unsupported conclusion or removal of a correct required distinction after revision. Inspect observer errors and justified rejections separately.
6. **Efficiency:** record calls, input/output/total tokens and seconds, including failures and shared-call accounting. No automated LLM judge or aggregate quality score. Counts over ten cases are descriptive, not reliability estimates.

Financial correctness and unsupported conclusions are reviewed separately from deterministic mapping verdicts, because mappings can omit or misrepresent prose. Economic/causal judgments use the predefined distinctions and source calculations, never observer agreement as ground truth. Revisions are compared with the shared original to distinguish repairs from added verbosity.

## Ten predefined cases

### 01

**Question:** Explain the portfolio's illustrative daily loss. What are the principal contributors and offsets, and what economic interpretation is warranted?

**Factual inputs:** common portfolio/current levels/conventions plus `daily` evidence.

**Expected quantitative relationships:** `{"credit": -407250, "daily_total": -560770, "equity": -506000, "fx": -60000, "rates": 412480}`.

**Economic distinctions:** Rates offset losses but do not establish portfolio profit; Economic interpretation is conditional on synthetic moves.

**Common incorrect interpretations:** Negative rates attribution; Rate gain equated with total gain.

**Not established:** True economic cause or calibrated probability.

### 02

**Question:** Does the daily portfolio loss mean the government-rate hedge failed? Explain what the Treasury holdings and swaps contributed and what the aggregate result tells us.

**Factual inputs:** common portfolio/current levels/conventions plus `daily` evidence.

**Expected quantitative relationships:** `{"all_rates": 412480, "daily_total": -560770, "pay_fixed_rates": -96000, "receive_fixed_rates": 224000, "treasury_cash_rates": 145280}`.

**Economic distinctions:** Successful directional contribution differs from full loss offset or an optimal hedge; Government-rate P&L includes credit-bond rate legs.

**Common incorrect interpretations:** Treasury hedge lost as yields fell; Calling hedge undersized or failed without an objective.

**Not established:** Optimal hedge size or hedging mandate.

### 03

**Question:** Under the supplied joint stress, explain high-yield credit's spread contribution, rate contribution and net result. What does that reveal about this portfolio?

**Factual inputs:** common portfolio/current levels/conventions plus `scenario` evidence; supplied hypothetical shocks `{"equity_pct": -15, "fx_pct": -5, "hy_bp": 250, "ig_bp": 75, "rates_bp": -50}`.

**Expected quantitative relationships:** `{"hy_net": -872500, "hy_rates": 240000, "hy_spread": -1112500, "portfolio_total": -3347000}`.

**Economic distinctions:** HY net is not spread-only P&L; Rate gains do not remove default or spread risk.

**Common incorrect interpretations:** Calling -872500 the HY spread loss; CS01 interpreted as default-loss estimate.

**Not established:** Default losses or executable liquidation cost.

### 04

**Question:** Interpret the portfolio's signed DV01 and CS01. Explain the derivative exposures relative to their marked values and give a non-overlapping account of rate sensitivity.

**Factual inputs:** common portfolio/current levels/conventions plus `daily` evidence.

**Expected quantitative relationships:** `{"credit_bond_dv01": 17400, "cs01": 15950, "dv01": 51560, "hy_cs01": 4450, "ig_cs01": 11500, "pay_fixed_notional": 30000000, "receive_fixed_notional": 40000000, "swap_net_dv01": 16000, "treasury_dv01": 18160}`.

**Economic distinctions:** Signed first-order sensitivities differ from marks/notionals and actual losses; Asset-class and instrument groups must be disjoint when added.

**Common incorrect interpretations:** CS01 second-order; Adding overlapping DV01 groups; Inferring risk from net derivative mark alone.

**Not established:** Margin requirement, convexity or default loss.

### 05

**Question:** Given the cash balance and derivative positions, is this portfolio's liquidity buffer adequate during severe stress? Explain the basis and limits of any conclusion.

**Factual inputs:** common portfolio/current levels/conventions plus `daily` evidence.

**Expected quantitative relationships:** `{"cash_mark": 6000000, "nav": 100000000, "swap_gross_reference_notional": 70000000}`.

**Economic distinctions:** Cash mark is not known unencumbered liquidity; Notional alone does not establish margin need; Adequacy is unknown.

**Common incorrect interpretations:** Cash is insufficient or adequate without contractual and timing data; Treating gross notional as cash due.

**Not established:** Funding shortfall or adequacy without CSA/netting, collateral, facilities and timing.

### 06

**Question:** During a severe financial liquidity crisis, how might US Treasury yields behave, and why? Discuss plausible financial mechanisms, implications for this portfolio and evidence that would distinguish explanations.

**Factual inputs:** common portfolio/current levels/conventions plus `portfolio` evidence.

**Expected quantitative relationships:** `{"net_dv01": 51560}`.

**Economic distinctions:** Safety demand can support Treasury prices and reduce yields; Cash demand and liquidation can depress Treasury prices and increase yields; Dominance/coexistence depends on conditions; no identified cause.

**Common incorrect interpretations:** Treasury yields must decline in every crisis; Rising yields alone establish the mechanism.

**Not established:** Dominant mechanism or causal probability without depth, funding, flow and policy evidence.

### 07

**Question:** Interpret the supplied joint rate-and-credit stress. Explain the interactions for the credit baskets and the overall portfolio, including the major model limitations.

**Factual inputs:** common portfolio/current levels/conventions plus `scenario` evidence; supplied hypothetical shocks `{"equity_pct": 0, "fx_pct": 0, "hy_bp": 500, "ig_bp": 125, "rates_bp": -50}`.

**Expected quantitative relationships:** `{"credit": -3662500, "hy_net": -1985000, "ig_net": -807500, "rates": 2578000, "total": -1084500}`.

**Economic distinctions:** Lower government yields can coincide with spread losses exceeding rate gains; Linear spread sensitivity is not default modeling.

**Common incorrect interpretations:** Rate rally guarantees credit bond gain; Replacing spread shocks with government-yield changes.

**Not established:** Event probability or full crisis severity.

### 08

**Question:** What do the two supplied rate-only calculations reveal about this portfolio, and what do they leave unanswered about its behavior in broader economic stress?

**Factual inputs:** common portfolio/current levels/conventions plus `rate_comparisons` evidence.

**Expected quantitative relationships:** `{"difference": -5156000, "minus50_rates_total": 2578000, "plus50_rates_total": -2578000}`.

**Economic distinctions:** Symmetry is a first-order model property; Rate-only outcomes are not complete inflation or recession scenarios.

**Common incorrect interpretations:** Treating rate-only gain as a forecast; Ignoring credit/equity/FX co-moves.

**Not established:** Joint market response, convexity or calibrated hedge effectiveness.

### 09

**Question:** Estimate this portfolio's counterparty and jump-to-default losses from the supplied snapshot. What can actually be established, and what information is missing?

**Factual inputs:** common portfolio/current levels/conventions plus `daily` evidence.

**Expected quantitative relationships:** `{"cash_mark": 6000000, "cs01": 15950}`.

**Economic distinctions:** Spread sensitivity does not quantify default jumps; Derivative marks/notionals do not establish net counterparty exposure; Losses are not established rather than zero.

**Common incorrect interpretations:** Invented default/counterparty loss estimates; Assuming no modeled loss proves no risk.

**Not established:** Loss amount without issuer/recovery, counterparty/netting, collateral and exposure data.

### 10

**Question:** What causal conclusions, if any, can be drawn from the supplied synthetic daily market moves? Discuss plausible explanations, discriminating evidence and implications for the portfolio without treating co-movement as identification.

**Factual inputs:** common portfolio/current levels/conventions plus `daily` evidence.

**Expected quantitative relationships:** `{"daily_total": -560770, "equity_shock": -2.2, "fx_shock": -0.6, "hy_shock": 45, "ig_shock": 18, "rates_shock": -8}`.

**Economic distinctions:** Growth/discount-rate, liquidity and positioning explanations need not be uniquely separable; Descriptive co-movement is not causal identification.

**Common incorrect interpretations:** Stating a real current crisis or a proven causal driver; Inventing macro observations.

**Not established:** True cause, calibrated historical replay or causal probabilities.

## Results — one frozen live run

All ten cases and all four conditions completed. There were **40 successful unique model calls**, no failed/truncated inference, no retries and no incomplete cases. Execution was **2026-10-28 14:36:54–14:43:25 UTC (07:36:54–07:43:25 PDT)**; measured wall time **391.364 seconds**. Raw originals, independent feedback, C/D revisions, original/revised mapping checks, contexts, usage and timings remain in ignored `research/runs/observer-v08-20261028/`, with 0700 directory / 0600 files. No authentication headers or credentials are recorded.

The immutable preflight `protocol.json` contains the ten expectations, prompts, schemas, source hashes, limits and initial settings; canonical JSON SHA-256 is `1a9cc93fe7eaec2127d012bad98a3ad699ef2c48ef2c8eabfe0cd43977be186a`. The source Git base was `ce789293083f25ba9cf331b7240373604a1020a3` plus this research implementation and the one-line generic reference-validation correction. After execution, every recorded source hash still matched: **no prompt, schema, case or setting optimization occurred during the run**. All ten original-response identities, factual contexts, shared independent feedback and B/D annotation associations were checked against the records. Expectations/grading keys were absent from model contexts; B's explanation remained unchanged.

### Per-case manual results

`F/U` means presence of a material financial error / unsupported material conclusion, with 1=yes and 0=no. Financial errors include misleading financial interpretation, not just arithmetic. A and B share these prose assessments because B only annotates. Coverage is judged against the predefined distinctions. The categories are manually assessed descriptive labels, not an automated score. `V`, `X`, `NC` are **mapped** Verified, Contradicted and Not checked, not judgments of all prose.

| Case | A/B F/U | C F/U | D F/U | Economic coverage A/B → C,D | B mappings | Observer / material result |
| --- | --- | --- | --- | --- | --- | --- |
| 01 attribution | 0/0 | 0/0 | 0/0 | Complete → Complete | 3 V | No objections; no material revision. Daily amounts/signs correct. |
| 02 hedge | 0/0 | 0/0 | 0/0 | Complete → Complete | 3 V | No objections. Summary's listed summands omit credit-rate contribution, though body acknowledges it; ambiguity persists. |
| 03 HY attribution | 0/0 | 0/0 | 0/0 | Complete → Complete | 3 V | No objections. HY rates/spreads/net correct. Equity-like beta/diversification phrasing merits qualification, not a clear material error under this conditional stress reading. |
| 04 sensitivities | 0/0 | 0/0 | 0/0 | Partial → Partial | 3 V | No objections. Correct signed DV01/CS01 and swap mark/notional distinction, but requested disjoint Treasury/swap/credit DV01 account is incomplete. |
| 05 liquidity | 1/1 | 0/0 | 0/0 | Partial → Complete | 2 V | One justified objection repairs MTM-as-cash-cover reasoning in both revisions. F/U describe the same underlying issue, not two independent repairs. |
| 06 mechanisms | 0/0 | 0/0 | 0/0 | Complete → Complete | 2 NC | Both opposing mechanisms and diagnostic uncertainty already present. True sensitivities mapped to absent scenario period are uncheckable; mapping scope remains unrepaired. |
| 07 rates/credit | 1/0 | 0/0 | 0/0 | Complete → Complete | 3 V | Two objections: fixes benefit-to-all-duration overgeneralization; also clarifies smaller HY aggregate rate cushion. One clear material error repaired in each revision. |
| 08 rate sensitivity | 0/0 | 0/0 | 0/0 | Complete → Complete | 1 V, 1 X | Correct ±$2.578m prose; second outcome wrongly mapped to first scenario. D preserves correct prose but leaves mapping defect. No observer objection. |
| 09 missing evidence | 1/1 | 1/1 | 1/1 | Complete → Complete | 2 V | Core refusal to estimate is correct, but mark/sensitivity conflation and unsupported issuer concentration persist; observer misses both. |
| 10 ambiguous cause | 0/0 | 0/0 | 0/0 | Partial → Partial | 3 V | Correctly denies identification, but does not develop liquidity/positioning alternatives in predefined coverage. Observer misses omission. |

### Corrections beyond B, and what did not improve

**Case 05:** initial text said cash provided initial cover for variation margin and the daily loss. That comparison conflates total modeled MTM with cash demand and assumes availability/contractual cash needs not supplied. The observer challenged this specific reasoning rather than merely adding another risk list. Both C and D removed the cash-cover inference, distinguished unrealized marks from cash flow, and required netting, collateral and settlement information. Rate-derivative MTM **+$128,000** plus FX MTM **−$60,000** sums to **+$68,000**, but neither arithmetic netting nor positive marks establishes actual net cash receipt or available liquidity. The revised core analysis retained those uncertainties. B's two selected mappings had both been Verified and did not expose the problematic prose.

**Case 07:** initial text said a rally helped all duration positions. The pay-fixed swap has **−$12,000/bp DV01** and loses **$600,000** in the −50bp scenario, while the receive-fixed gains $1.4m. Both revisions explicitly restored that signed-position distinction. They also replaced the vague similar-rate-duration comparison with the smaller HY aggregate rate cushion: HY DV01 **$4,800/bp / +$240,000**, versus IG **$12,600/bp / +$630,000**. Portfolio rates +$2.578m, spread losses −$3.6625m and total −$1.0845m remained correct. Again, B's three selected mappings were all Verified, leaving the all-positions prose outside coverage.

**Misses:** observer silence did not establish correctness. Case 09's issuer-concentration assertion is unsupported by aggregate basket holdings and survived unchanged. Its sentence grouping market values with first-order spread/rate sensitivity is also financially misleading: marks are levels, not sensitivities. That is a residual financial error even though the central refusal to estimate unmeasured losses is sound. Case 04 did not supply the requested disjoint rate breakdown (**18,160 Treasury + 16,000 swaps + 17,400 credit = 51,560 USD/bp**). Case 10 gave growth/safety and unrelated-shock accounts but did not develop the liquidity/positioning alternatives in its predefined expectations. Neither revision repaired those omissions.

**Cautions separate from headline errors:** case 02's summary moves from Treasury $145k plus swaps $128k to $412k total without naming the **$139,200 credit-rate** contribution in that sentence; the body does acknowledge it, so it is not counted as an unambiguous whole-answer arithmetic error. Case 03's equity-like-beta/limited-diversification language is stronger than a single assumed co-move can establish; under a strict categorical reading it could be counted as unsupported, but it is within a conditional stress explanation. Counting that caution as an error in every condition would not change the repair comparison. Case 07 D uses rate cut loosely for a government-yield shift; no observed central-bank action is established. These notes illustrate judgment sensitivity rather than a hidden numerical grade.

### Observer quality, rejection and regressions

The observer returned **three objections in two cases**, and **no objections in eight**. Two objections were clearly justified material financial concerns (MTM/cash cover; signed duration). The third, case 07 OBJ-02, supports a useful qualification about *aggregate* DV01 and cushion size. Its assertion about durations differing materially is terminologically overconfident: aggregate DV01 also depends on position size and does not by itself establish a per-dollar/tenor duration comparison. The main revisions safely emphasized aggregate DV01 rather than claiming a proven maturity difference. This qualification is not counted as a second independent material repair in case 07.

Both revisions accepted all three objections (six acceptance decisions); there were **zero rejections**. There was no unambiguous wholly false objection followed by a correct rejection to report. Consequently, this run **does not demonstrate robust rejection of bad observer advice**, even though the instruction permits and requires it where appropriate. Observer agreement and self-reported acceptance were not used as proof of correctness; the financial changes were reviewed against source evidence.

Across the **20 revised explanations**, manual review found **no newly material financial error, unsupported conclusion or loss of a correct required distinction**. That is an observed count, not an estimated regression probability. The two material repair cases were the same in C and D; deterministic feedback did not add an observed material prose repair beyond C in this run.

### Descriptive totals and verifier coverage

| Condition | Cases with financial error | Cases with unsupported material conclusion | Complete / partial coverage | Material issue cases repaired versus A |
| --- | ---: | ---: | --- | ---: |
| A | 3 | 2 | 7 / 3 | — |
| B | 3 | 2 | 7 / 3 | 0 (annotations only) |
| C | 1 | 1 | 8 / 2 | 2 |
| D | 1 | 1 | 8 / 2 | 2 |

The financial/unsupported columns overlap in cases 05 and 09: A/B have three distinct material-issue cases (05, 07, 09), not five independent issue cases. C/D retain case 09. Coverage is case-specific and does not mean exhaustive economic completeness.

B produced **26 mapped verdicts: 23 Verified, 1 Contradicted, 2 Not checked**. Posthoc C and D checks produced the same counts; these posthoc results were not fed into another revision. This does not mean the explanations were equally good:

- Case 08's Contradicted mapping targets the first (`scenario` = −50bp) result with the second (+50bp) result's amount. The +50bp prose itself is financially correct. D did not fix that scope error, but did not let the annotation corrupt the correct prose either. There is no observer rejection involved.
- Case 06's true DV01/CS01 figures name a nonexistent scenario period; the current verifier appropriately returns Not checked, not a financial falsity verdict.
- Case 09 maps a counterparty sentence to the default target. Its Verified annotation checks only that default losses are unquantified, not semantic equivalence to a counterparty conclusion or issuer concentration. This remains a v0.7 coverage limitation.

No percentage improvement, significance claim, aggregate answer-quality score or estimated reliability is inferred from these ten hand-reviewed cases.

### Efficiency

All reported token counters are retained per call. Reasoning-token counters are included within completion tokens and must not be added twice. The study used **385,680 unique total tokens** and 391.364 seconds wall time. Summed model-call time is 390.984 seconds; local deterministic verification summed to about 0.0024 seconds. Timing is this serial run under the provider's conditions, not a throughput benchmark.

| Unique stage | Calls | Prompt tokens | Completion tokens | Total tokens | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Initial | 10 | 58,998 | 41,179 | 100,177 | 134.221 |
| Independent observer | 10 | 56,931 | 27,695 | 84,626 | 101.746 |
| C revision | 10 | 69,291 | 27,501 | 96,792 | 77.772 |
| D revision | 10 | 75,700 | 28,385 | 104,085 | 77.245 |
| **Unique study total** | **40** | **260,920** | **124,760** | **385,680** | **390.984 call seconds** |

| Condition dependency cost over ten cases | Calls including shared dependencies | Total tokens | Seconds including dependencies |
| --- | ---: | ---: | ---: |
| A | 10 | 100,177 | 134.221 |
| B | 10 + local verification | 100,177 | 134.223 |
| C | 30 | 281,595 | 313.739 |
| D | 30 + local verification | 288,888 | 313.214 |

These condition rows share initial/observer calls and **must not be summed**. Relative to B's dependency cost, D adds 20 model calls and **188,711 tokens** (about **2.88×** total tokens), with average serial dependency latency about **31.32s versus 13.42s** per case. The full four-condition study needs 40 rather than 80 calls because it reuses originals and independent observer feedback.

| Case | Unique calls | Total tokens across initial/observer/C/D | Summed call seconds |
| --- | ---: | ---: | ---: |
| 01 | 4 | 36,058 | 37.062 |
| 02 | 4 | 37,284 | 36.103 |
| 03 | 4 | 35,350 | 31.088 |
| 04 | 4 | 38,059 | 38.286 |
| 05 | 4 | 40,660 | 48.545 |
| 06 | 4 | 28,314 | 37.765 |
| 07 | 4 | 44,553 | 57.156 |
| 08 | 4 | 53,401 | 34.724 |
| 09 | 4 | 34,209 | 33.521 |
| 10 | 4 | 37,792 | 36.734 |

Case 08 includes two full calculations plus a mapped first scenario, making its factual input larger. No context-size or prompt optimization was performed after seeing that cost.

## Findings, limitations and recommendation

**Empirical answer:** observer-plus-revision repaired two material financial reasoning problems that the original deterministic annotations did not flag, while preserving most already-correct content. It did not reliably detect unsupported prose or incomplete mechanisms, and did not resolve typed-mapping scope defects. C and D had the same observed material repairs; D versus B shows a useful *feedback-and-revision bundle*, not the isolated causal value of the observer.

**Recommendation: do not integrate an always-on observer into the main Metis workflow on this evidence.** The gains are specific (MTM/cash distinction and signed-rate qualification), costs are substantial relative to local verification, and eight no-objection reviews did not imply eight complete answers. A targeted, human-requested second look is a plausible future research direction, but no observer UI or workflow routing is implemented. Simple main-prompt safeguards might address some observed errors more cheaply; that possibility was not tested or optimized here.

Limitations: ten synthetic cases, one completion per stage, same model in all roles, serial fixed order (C before D), non-blinded manual judgments, no independent economic ground truth or real crisis measurements, and a research prompt rather than the production v0.7 prompt. Output schemas and role prompts differ by stage; more context/tokens and the act of revision can affect results. There is **no verifier-plus-revision-only control**, so observer-only incremental benefit is not identified. The conservative material-error threshold and case 03 caution could be judged differently; the core repair cases and recommendation do not depend on that borderline classification. No statistical reliability, generalization, private reasoning inference or causal identification is claimed.

All feasible cases have been evaluated; no further runs are authorized by this experiment and none were added. Future work would need separately authorized, predeclared controls that distinguish observer feedback from revision alone, and explicit tests of erroneous objections and correct rejection.

## Reproduction and validation

The fixed runner is `research/observer_experiment.py`, case definitions are `research/observer-cases.json`, and exact role prompts/schemas/source hashes are archived in the private preflight. It can be reproduced from the committed source using `uv run python research/observer_experiment.py --output-dir research/runs/<new-private-directory>` with local Meta configuration. **That command was run only once for this study.** No general orchestration, automated judge or frontend feature was added.

Validation: **121 backend tests, 12 frontend tests and production build pass**. New tests cover ten-case/40-call bounds, input/feedback reuse, answer-key exclusion, observer failure without retry, reference allowlists and resolution-ID matching; they do not grade model economics. Preflight initially had a research-module import-path test collection error, corrected before live calls. Existing test-client deprecation and large-bundle warnings remain. Frontend, analytics, synthetic source data and prior research reports are unchanged. Credentials, raw inference records and generated artifacts are excluded from Git.
