# Unguided causal reasoning during a liquidity crisis

One live request and manual review, completed 2026-10-28. This tests whether the model volunteers particular mechanisms without their names being supplied in this request. It does not establish causal identification, independence from learned financial narratives, or statistical reliability. No LLM judge, scores, retries, additional cases or application features were used.

## Exact request and settings

Source snapshot: `be57a500037491c9807c71ae6785b41aeb4a1d87`. Model `muse-spark-1.3`, endpoint `https://api.meta.ai/v1/chat/completions`, `temperature=0.2`, `max_completion_tokens=8000`, HTTP timeout 60 seconds; no seed or other sampling overrides. These match the guided experiment. Execution was 12:42:32–12:42:48 UTC (05:42 PDT) on 2026-10-28. One completion passed strict structural and allowed-evidence validation on the first request.

Exact user question, with no appended instructions:

```text
During a severe financial liquidity crisis, how might US Treasury yields behave, and why? Explain the plausible mechanisms, how they could affect other financial markets, and what evidence would help distinguish between different explanations. Discuss the implications for this portfolio and identify important uncertainties.
```

Exact research-only system message:

```text
You are Metis, a financial interpretation assistant. Answer the user's question using the supplied factual context. Give a concise conclusion and an evidence-grounded public explanation, not private chain-of-thought. Return only JSON matching the supplied schema. Distinguish supplied synthetic facts, your economic interpretations, illustrative assumptions, and uncertainties. Do not invent current observations, missing measurements, sources, or evidence IDs. Numerical illustrations, if any, must be labeled hypothetical; probabilities or forecasts require evidence. Use only supplied IDs in evidence_references. Do not give trading instructions.
```

The call reused `HTTPProvider("meta").structured(ReasoningRequest(question=question), context, Interpretation, system, "financial_interpretation")`. This is the existing transport and general interpretation schema, not the application's leading causal prompt/schema. Application code was not modified. The request contained exactly two messages (system and the adapter's JSON user payload), with no history, previous responses, tools, or previous report text. The payload contained `question`, `context`, and `output_schema` as usual.

## Leakage audit and exact retained context

| Surface | Retained / excluded | Reason |
| --- | --- | --- |
| System | Neutral message above; excluded both application system prompts and the guided research instructions. | Existing causal instructions prescribe two competing hypotheses and yield anchors; ordinary financial instructions also contain risk interpretations. |
| Portfolio | All 12 original CSV rows and all 11 columns, unmodified; portfolio name, synthetic label, USD 100m NAV, and all six aggregate sensitivities. | Factual exposures are necessary to assess portfolio implications. No daily-derived P&L columns or conclusions were supplied. |
| Market | Same synthetic 2025-03-10 snapshot's current yield levels, current IG/HY spread levels and EUR/USD level, names/tenors/buckets, currency and synthetic-data label. | Preserves market levels without supplying a direction or joint daily pattern. |
| Market changes and calculations | Excluded previous levels/date, all change fields, `daily_shocks`, daily position/factor/total P&L, opening NAV/daily return, commentary and method narratives. Equity market data had only changes, so those rows were excluded. | The previous rates rally alongside weaker credit/equities would prime one branch; commentary explicitly explains it. |
| History | Excluded the entire library: facts, titles, dates, interpretations, limitations, source titles/URLs and history evidence IDs. | Even the remaining March 2020 policy-purchase fact and market-functioning source title could cue an answer. Episode selection itself is informative. |
| Scenarios | None: no assumptions, anchors, presets, labels, shock bounds, hypothetical results, or guided A/B cases. | Opposite rate signs or named stress conditions would supply the contrast being tested. |
| Schema | Existing `Interpretation`: `summary`, `principal_risk_observations`, `economic_interpretation`, `historical_analogies`, `potential_vulnerabilities`, `assumptions_and_uncertainties`, `evidence_references`. | No mechanism names, exactly-two requirement, directional enums, examples, or proposed shocks. The generic `historical_analogies` field remains a format cue, not a supplied episode or mechanism. |
| Evidence IDs | Only `portfolio` and `market`, with neutral descriptions below. | No historical/scenario IDs or descriptions that could leak labels. |

This is the same underlying portfolio and current market data as the guided run, **not identical complete context**: leakage removal deliberately changes its information content. The exact context can be reconstructed at the source snapshot with the following code (using the existing analytics imports). Scalar values and row order are retained from source files:

```python
frame = load_positions()
data = workstation()
market = load_json("market")
context = {
    "portfolio": {
        "portfolio_name": data["portfolio_name"], "data_kind": data["data_kind"],
        "nav_usd": data["nav_usd"], "positions": frame.to_dict(orient="records"),
        "exposures": data["exposures"],
    },
    "market": {
        "as_of": market["as_of"], "label": market["label"],
        "base_currency": market["base_currency"],
        "yields": [{"tenor": r["tenor"], "current_pct": r["current_pct"]}
                   for r in market["yields"]],
        "credit": [{k: r[k] for k in ["name", "bucket", "level_bp"]}
                   for r in market["credit"]],
        "fx": [{"name": r["name"], "level": r["level"]} for r in market["fx"]],
    },
    "conventions": {
        "units": "USD. Yield and spread changes in basis points; equity and EUR/USD changes in percent.",
        "rates_pnl": "-dv01_usd_per_bp * rates_bp",
        "credit_pnl": "-cs01_usd_per_bp * applicable_ig_or_hy_bp",
        "equity_pnl": "equity_delta_usd * equity_pct / 100",
        "fx_pnl": "fx_delta_usd * fx_pct / 100",
        "aggregation": "Sum the position factor contributions for portfolio P&L. Government-rate changes apply in parallel to all rate-sensitive positions; credit bonds have separate government-rate and spread contributions. First-order approximation.",
    },
    "evidence": [
        {"id": "portfolio", "description": "Synthetic position marks, reference notionals and deterministic USD sensitivities"},
        {"id": "market", "description": "Dated synthetic market levels; not real-time observations"},
    ],
}
```

Current levels retained were 2Y/5Y/10Y/30Y yields 3.97/4.10/4.24/4.54%, IG/HY spreads 118/365bp and EUR/USD 1.075. The API's strict schema constrained evidence IDs to `portfolio`/`market`; it supplied no economic descriptions beyond the generic field names. All source positions/sensitivities were checked unchanged.

Manual inspection covered the complete captured request body, including the system message, serialized context and both appearances of the output schema. A preflight/final-body phrase scan additionally checked explicit target mechanisms and named historical episodes; this scan is a safeguard, not proof of semantic neutrality. No explicit target mechanism was found. Residual cues remain: the question supplies a liquidity-crisis topic and asks for plural explanations, the format asks for risks/analogies, and real instrument names include cash, collateral, swaps and FX hedges. Standard sensitivity formulas also make direction-to-P&L arithmetic available. These are not supplied buying/selling mechanisms, but this is not a cue-free or pretraining-free test.

Private inputs, preflight audit, exact request body, response, metadata and numerical checks are in ignored `research/runs/unguided-causal-20261028T124232Z/` (0700 directory, 0600 files). No headers or credentials were recorded. Canonical request-body SHA-256: `2634a9ed448506e241e7dd1be34ec8388ba5d054cd36eefa51be70a6b1de6e3d`; context SHA-256: `15e00b6289de181b6d3048793d16f373758ba94258619dd7889ee85e43927a4d` (sorted-key compact JSON, UTF-8, `ensure_ascii=False`). Usage: 2,558 prompt tokens, 3,613 completion tokens, 6,171 total; 2,148 reasoning tokens were reported within completion usage, not an exposed reasoning trace.

## Faithful response summary and manual assessment

The response volunteered both Treasury demand for safety with easier-policy expectations, and Treasury sales to obtain cash during leverage unwinds and constrained intermediation. It described a phase-dependent path, cross-asset losses, basis risk and missing diagnostics. It did not name actual historical episodes: its `historical_analogies` were generic archetypes, not sourced empirical evidence.

| Criterion | Observed response | Assessment of what was supplied versus volunteered |
| --- | --- | --- |
| Demand for safety | Treasury buying and policy-rate expectations can lower yields, supporting long duration. | The economic channels were volunteered; neither was in the question, system, schema, or retained facts. Positive DV01 and its arithmetic were supplied. |
| Demand for cash | Dash-for-cash, margin calls, leveraged cash-futures/swap unwinds and intermediation limits can force Treasury sales and temporarily raise yields. | Target mechanism volunteered. Instrument facts such as swaps and cash/collateral were retained, but no liquidation narrative, margin requirement or dealer information was supplied. |
| Dominance | Described initial risk-off, acute deleveraging and subsequent policy-response phases; yield direction depends on which pressures prevail. | Recognized competing pressures and time variation. This is a plausible conditional narrative, not a tested sequence or an operational dominance threshold. |
| Credit, equity and portfolio | Wider credit spreads and weaker equities can coincide with rates losses; a rate rally helps duration in isolation. Cash bonds and swaps can diverge; USD funding stress can affect long EUR. | Consistent with supplied net long DV01, CS01, equity/FX delta and separate rate/spread conventions. Neither joint behavior nor basis losses are estimated by those sensitivities. |
| Discriminating evidence | Suggested depth/bid-ask, fails/auction tails, repo and bill/OIS spreads, cash-futures basis, swap spreads, real yields/breakevens, FX basis and joint market moves. | Specific diagnostics volunteered, not supplied in a checklist. They require unavailable data and interpretation; their co-movement alone would not identify a cause. |
| Uncertainty | Explicitly called yield direction/persistence ambiguous, highlighted phase/policy dependence, correlations, unavailable funding information and model omissions. | Appropriate caution; no measured probability or identified prevailing mechanism. |

### Numerical checks

All explicit input levels, NAV/exposures, the DV01 decomposition, and the rounded arithmetic illustrations checked out. The disjoint decomposition was 16,000 + 2,160 + 28,000 − 12,000 + 17,400 = **51,560 USD/bp**; credit-bond DV01 was correctly included rather than added twice. IG/HY CS01 11,500/4,450 sum to 15,950 USD/bp. Equity/FX delta were correctly 23m/10m USD, and 6m cash equals 6% of NAV. The model did not repeat the prior HY net-versus-spread attribution error or describe CS01 as second-order.

The following are checks of **model-volunteered hypothetical component illustrations**, not additional experimental cases or analyst-supplied prompts:

| Illustration | Model's rounded P&L | Exact existing-engine component |
| --- | ---: | ---: |
| Parallel rates +50bp | about −$2.58m | −$2,578,000 |
| IG spreads +100bp | −$1.15m | −$1,150,000 |
| HY spreads +300bp | about −$1.34m | −$1,335,000 |
| Equities −10% | −$2.3m | −$2,300,000 |

These match `calculate(load_positions(), Shocks(...))` factor/bucket outputs under the supplied first-order conventions. The model did not assert a combined scenario total or FX shock; none is attributed to it. A parallel rate shock affects all rate-sensitive positions, not a Treasury-specific basis dislocation. These arithmetic checks do not verify actual crisis outcomes.

**Unsupported claims and omissions:** the response calls the USD 6m cash position a limited buffer against stress demands. Its size is factual, but adequacy is unsupported without unencumbered-cash information, contractual collateral/margin terms, timing, netting and funding access. The phase sequence and customary cross-market relationships are interpretations, not observations in this dataset. Generic historical archetypes offer no empirical validation. The explanation does not specify a test that separates confounded flows from policy/expectation changes or quantify a dominance threshold, funding shortfall, liquidity loss or basis exposure. No numerical inconsistency was found; these limits concern economic judgment and identification.

## Comparison with the guided experiment

Both target mechanisms appeared in this unguided response without their names, yield signs, dealer constraints, margin calls or candidate diagnostics in the request. Thus neither target **required explicit naming in this particular completion**. This does not prove they would appear reliably or that a missing mechanism elsewhere requires prompting.

The guided response was organized around a supplied A/B contrast, fixed shocks and an explicit evidence checklist. This response instead volunteered a time/phase narrative, money-market hoarding, cash-versus-swap divergence and its own numerical illustrations. Basis unwinds and policy expectations already appeared in the guided response, so they are elaborations rather than wholly new discoveries. Money-market hoarding and the fuller phase sequence are relevant additional details, but remain untested. Conversely, the guided response explicitly offered inflation surprises and Treasury supply/term-premia repricing as alternative causes; those were not developed here as distinct alternatives. Real-yield/breakeven diagnostics are not a complete substitute for explaining them.

Only model, portfolio/current levels and inference settings are held constant. Question, system instructions, schema, token count and other context differ. Historical/daily directional evidence was removed to prevent leakage. There is one stochastic completion in each experiment, so **differences do not establish a causal effect of prompting**, and length/reference count is not a quality measure. The guided comparison's fixed-scenario totals are not comparable to these independently chosen arithmetic illustrations as a model-performance metric.

## Limits, implications and stop

This response demonstrates that the model can retrieve and synthesize both financial mechanisms without explicit mechanism labels in the current request, and apply supplied sensitivities correctly in these examples. It does not reveal the model's internal reasoning, separate learned narratives from novel inference, identify an actual cause, or measure reliability. Financial input/format cues and model pretraining remain, and no external crisis measurements were supplied.

Any future research, if separately authorized, should distinguish retrieval/synthesis from identification and keep non-question context/format controlled with predeclared human criteria. No further inference was run here. Stopped after **one successful unguided response and manual analysis**, without adapting the prompt to the answer. Application, analytics, frontend and prior reports are unchanged. Validation: **73 backend tests, 12 frontend tests and production build pass**; existing test-client deprecation and large-bundle warnings remain. No new tests were added for this report-only change. Raw private records and credentials are excluded from Git.
