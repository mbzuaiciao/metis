# Historical macro context and hypothesis generation: September 13, 2022

**Completed November 3, 2026 (America/Los_Angeles).** One historical case, two successful live Meta requests, no retries. Added context made the sampled answer more event-specific, but **did not demonstrate a substantive improvement in economic mechanism reasoning**: the answer without news already proposed the principal channels. This is an inconclusive incremental-benefit result, not evidence that historical context is generally unnecessary.

## Question and design

Does historically grounded macro context produce more economically informative portfolio hypotheses than financial observations alone? Hypothesis generation is the objective; neither P&L consistency nor contemporaneous reporting identifies a cause.

The [pre-inference protocol](historical-macro-20220913-protocol.md) specifies the five qualitative criteria and stopping rule. [Source inputs](historical-macro-20220913-inputs.json), [frozen preparation](historical-macro-20220913-prepared.json), [runner](historical_macro_context.py) and [telemetry](historical-macro-20220913-telemetry.json) preserve reproducibility. Base revision `6b17068b446f9a2896184068aa8485a093642879` already contains merged PR #3; it was inspected read-only.

A receives synthetic positions, market moves, mapping assumptions and calculated P&L, with no date, event description, news text, URLs or macro narrative. B adds only a sourced `macro_context` object. System instructions, question, schema, evidence-ID catalog, financial inputs and inference settings are identical; no history passes between calls. Actual outgoing requests were compared after removing this one object, including the serialized user payload. Both financial inputs hash to `9c6361de0b9437664d3ce14cebc80205cb934c4468fcbb0f18212c07f19cb363`.

## Historical evidence and mapping assumptions

The [original BLS release](https://www.bls.gov/news.release/archives/cpi_09132022.htm), published September 13 at 08:30 EDT, reports August headline CPI +0.1% month-on-month seasonally adjusted / +8.3% year-on-year unadjusted, and core +0.6% / +6.3%. Shelter, food and medical care contributed despite cheaper gasoline. The [Reuters wrap](https://www.marketscreener.com/news/latest/Stocks-tumble-dollar-rallies-as-soaring-U-S-inflation-implies-an-aggressive-Fed-41765172/), published 16:53 EDT, supplies the headline monthly consensus of −0.1% and describes expectations shifting toward more aggressive Fed tightening, with recession concerns. B uses only information available by that evening, not the subsequent policy decision. Consensus is a survey expectation, distinct from BLS measurements.

| Actual observation | September 12 reference | September 13 | Engine use |
| --- | --- | --- | --- |
| US 10Y Treasury yield | 3.362%, late Monday | 3.4157%, last quoted | **+5.37bp** = percentage-point difference × 100 |
| US 2Y Treasury yield | 3.571%, preceding session | 3.7434%, last quoted | +17.24bp retained as evidence; engine has no tenor-specific shock |
| S&P 500 | Prior cash close | 3,932.69 points, −177.72 points, reported **−4.32%** | Use reported rounded return |
| EUR/USD, USD per EUR | Prior-session daily-change reference; exact level unavailable | 0.9971, reported **−1.46%** | Use reported rounded return; do not reconstruct an exact prior level |
| IG/HY spread changes | Unavailable | Unavailable | Omit; engine zero placeholders are not observations |

All numerical market rows above come from that Reuters wrap. Treasury/FX quote clocks and exact FX reference-fix convention are unavailable; these are late quotes/daily reported changes, not synchronized official closes. Sources were retrieved November 3, 2026. We deliberately use the rounded equity/FX returns rather than imply extra precision. The equity prior close can be derived as 4,110.41 points from the reported point change, but is not separately sourced here.

The [IG](https://fred.stlouisfed.org/series/BAMLC0A0CM) and [HY](https://fred.stlouisfed.org/series/BAMLH0A0HYM2) FRED series notes now limit history to three years beginning April 2026. No reliable 2022 pair was retrieved; this does not mean historical spreads were unchanged or that no other source exists. Treasury's historical table was also inaccessible through the browser research tool; the accessible Reuters observations were retained. No paid data or dependency was added.

**Illustrative mappings:** the 10Y change is applied in parallel to all signed DV01, including swaps and US/European credit. The observed +17.24bp front-end move shows that this is not the actual curve. The S&P return is applied to both the US and hedged ex-US equity baskets; the latter is not an observed ex-US return. EUR/USD is applied to the long-EUR delta without historical forward-point revaluation. Positions and sensitivities are today's existing synthetic fixture, not actual September 2022 holdings. These assumptions are identical in A/B.

## Hypothetical portfolio calculation

The unchanged engine applies `−DV01 × yield_bp`, `−CS01 × spread_bp`, and `delta × percentage / 100`, rounding each position/factor to cents before aggregation. Synthetic reference NAV is $100m. Net DV01 is +$51,560/bp, IG/HY CS01 +$11,500/+$4,450 per bp, equity delta +$23m and EUR/USD delta +$10m.

| Factor | Calculated contribution |
| --- | ---: |
| Rates | −$276,877.20 |
| Credit spreads | Omitted / unknown; engine placeholder $0.00 |
| Equity | −$993,600.00 |
| FX | −$146,000.00 |
| **Partial-factor total** | **−$1,416,477.20 (−1.4164772% of synthetic reference NAV)** |

Positive yields correctly produce a loss on net positive DV01. Receive-fixed swap rates contribution is −$150,360; pay-fixed is +$64,440. Credit holdings still have rates losses within the rates factor; only their spread contribution is omitted. The total is neither observed portfolio P&L nor a full historical replay. Original March 2025 daily P&L remains −$560,770 and Broad Risk-Off remains −$3,347,000.

## Live inference and preserved records

Meta `muse-spark-1.3`, endpoint `https://api.meta.ai/v1/chat/completions`; temperature 0.2, 8,000 completion tokens including reasoning, low reasoning effort, 60s timeout, no seed, empty history. Existing `HTTPProvider.structured` is reused with a small research-only schema requiring two or three hypotheses and the five requested fields. No production prompt or schema was changed. Exact hosted weights/revision and monetary cost are unavailable.

Execution was 07:07:50–07:08:20 PST (14:07:50–14:08:20 UTC), A then B. Both returned HTTP 200, `finish_reason=stop`, and valid schema/evidence IDs.

| Condition | Hypotheses | Prompt tokens | Completion tokens (reasoning included) | Reasoning tokens | Request latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| A: financial data only | 3 | 5,136 | 1,230 | 630 | 16.867541s |
| B: additional macro context | 2 | 5,499 | 960 | 525 | 13.118768s |
| Total | 5 | 10,635 | 2,190 | 1,155 | 29.986309s summed |

Reported total tokens: **12,825**; elapsed run loop 29.989411s. No execution, truncation, schema or evidence-ID failures; no retries or fallback. These times/lengths are descriptive, not a performance or quality benchmark.

Exact outgoing JSON, exact response-body bytes, parsed outputs, status, usage, timestamps and hashes remain in ignored `research/runs/historical-macro-20220913-20261103/` (directory 0700, every file 0600). Parsed content was checked against the original response bodies. The committed telemetry contains no response prose. Raw-body SHA-256: A `4f7fd85df20e4508cbfbffb3b035beedd89ee4dd048d1a086707b4f2a7b4a1b1`; B `1ee523d24fe825696ac53d9edbc080cdb771bfc435d84038f559d017bea21023`.

## Hypotheses: reviewed paraphrases of actual outputs

These are analyst summaries, not exact model quotations. Original wording, including qualifications and weaknesses, is preserved privately.

| Condition / hypothesis | Proposed mechanism | Market connection | Portfolio implication | Uncertainty / competing explanation |
| --- | --- | --- | --- | --- |
| A1: Near-term policy tightening | Higher expected policy rates raise discount rates and support USD through relative yields. | Larger 2Y than 10Y rise; equities and EUR/USD fall. | Equity loss dominates; rates and long-EUR also lose, with correct rounded contributions. | Co-movement is not causation; missing spreads and the parallel approximation limit inference. |
| A2: Risk aversion and USD demand | Risk-premium repricing and dollar-liquidity demand pressure risky assets; rate expectations outweigh Treasury haven demand. | Equity/EUR declines with rising yields fit several interacting channels. | Correct rounded partial total; additional spread losses would be conditional on actual widening. | Missing spreads and ex-US proxy prevent distinguishing this from inflation-related repricing. |
| A3: Tightening and growth concerns | Persistent tightening compresses multiples and weakens the earnings outlook. | Bear-flattening and equity losses are consistent with this interpretation. | Long duration and $23m equity delta are exposed; payer swap offsets part of duration loss. | No macro facts supplied; one-rate mapping cannot represent the full curve. |
| B1: CPI-linked policy repricing | Inflation news raises expected policy rates, discount rates and earnings concerns. | Front-end-led yield rise and equity/EUR declines align with the release narrative. | Same correct rounded factor losses; payer swap partly offsets. | Release timing and reporting are consistent, but other drivers and unknown spreads remain. |
| B2: Recession concern and de-risking | Risk reduction and USD haven demand transmit recession concerns to equity/FX prices. | Equity weakness/USD strength fit; rising Treasury yields complicate a pure haven story. | Correct deltas/partial total; any spread widening could add losses. | Missing spreads prevent separating equity/FX selling from an additional credit channel. |

## Comparison and findings

| Predeclared criterion | Observation in this pair |
| --- | --- |
| Historical specificity | B ties repricing to CPI and a reassessment of Fed policy expectations. A infers plausible tightening/inflation channels without supplied news. Specific anchoring improves, but repeating supplied facts alone earns no mechanism credit. |
| Economic mechanism | Both articulate discount-rate, earnings, relative-yield and risk-aversion channels. B adds an event trigger, but no materially new transmission channel or discriminating prediction. A's third hypothesis overlaps its first. |
| Cross-asset coherence | Both reconcile higher rates with equity losses and USD strength; both recognize omitted spreads. B clearly notes the tension between higher yields and a simple Treasury haven story; A already addresses the competing forces. No measured overall coherence gain. |
| Portfolio relevance | Both reproduce selected contributions, long-EUR direction, long duration/equities and payer offsets correctly. No new exposure insight in B; engine-provided arithmetic is not evidence of model calculation skill. |
| Uncertainty | Both withhold causal certainty and flag missing credit evidence. B supplies no test identifying which channel dominates. A has more proxy discussion, but neither solves identification. |

**Grounding qualifications:** B describes core inflation as exceeding expectations, although its supplied consensus concerns headline CPI only. The direction of a core surprise is not established by the frozen evidence; this is added unsupported specificity within this prompt, not a demonstrated historically false claim. A asserts that the 10Y proxy understates front-end exposure. It understates the applied move for the known positive-DV01 2Y position, but a claim about aggregate curve exposure needs key-rate sensitivities and other tenors. A's inferred deterioration in growth expectations is a hypothesis, not a measured expectation. Neither issue changes the checked supplied P&L. Neither output establishes spread widening.

**Interpretation:** context supplied a more grounded event anchor; it did not show a material gain in mechanisms, portfolio relevance or uncertainty handling in these samples. B's unsupported core-surprise phrasing cautions against treating historical detail as automatic grounding. Fewer hypotheses in B is permitted by the common instructions and is not itself better or worse.

## Validation, limitations and decision

164 backend/research tests passed in 3.09s, including unchanged portfolio/scenario calculations, historical sign/units, source references, identical financial projection and absence of date/event clues in A. An existing Starlette/httpx deprecation warning remains. Offline post-run checks verified actual wire projection equality, matching model/settings/schema, byte-body hashes, parsed-output equality, permissions and the ignored archive boundary. Git review confirms no engine, production data, UI, provider or dependency changes. Frontend/build were not run because no frontend files changed.

This is one selected episode and one stochastic sample per condition, fixed order, non-blinded analyst review, shared pretrained knowledge, an unpinned hosted model and no causal control for extra input length. Date removal cannot prevent event recognition from the distinctive numerical pattern. Missing spread data, rounded late quotes, asynchronous markets and global proxy mappings limit historical fidelity. B does not receive the actual subsequent Fed outcome. Structural validation and selected numeric review do not verify all prose, causal truth or general reliability.

**Decision:** stop after the two calls. No demonstrated substantive incremental benefit in this pair; no production retrieval integration justified. Preserve the existing system and all prior experiment records. A broader claim would need a separately authorized study; none is launched here.

Offline reproduction: `.venv/bin/python research/historical_macro_context.py` checks prepared hashes/contexts without inference. Tests: `.venv/bin/python -m pytest tests research/test_meaning_alignment.py research/test_historical_macro_context.py`. The `--live` path documents how requests were made, but refuses to overwrite this run; it is not authorization for further inference. Local branch/commit only, no push or merge.
