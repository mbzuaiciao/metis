# September 13, 2022 credit-spread P&L correction · 2026-11-03

Focused correction from integration commit `1114a87`, implemented on `codex/historical-credit-pnl`. No experiment, inference, new pricing engine, retrieval service or dependencies. Prior research observations, findings, private responses and the original experiment inputs remain preserved; the production historical dataset is updated separately.

## Verified observations and units

On 2026-11-03, directly inspected the two user-supplied historical tables and FRED's series definitions/units:

| Series | September 12 | September 13 | Conversion and change |
| --- | ---: | ---: | --- |
| [ICE BofA US Corporate Index OAS, BAMLC0A0CM](https://equibles.com/economicdata/bamlc0a0cm/history/11) | 1.46% | 1.46% | 146 → 146bp; 0bp |
| [ICE BofA US High Yield Index OAS, BAMLH0A0HYM2](https://equibles.com/economicdata/bamlh0a0hym2/history/11) | 4.50% | 4.68% | 450 → 468bp; +18bp |

The tables label units Percent: one percentage point is 100bp, so the HY change is 0.18 percentage points × 100 = 18bp, not a relative 4% return and not 0.18bp. IG zero is a measured index difference at published precision, not the earlier omission placeholder. Production records retain both percent and bp levels, changes, dates, source links, verification date and conventions.

[FRED Corporate series notes](https://fred.stlouisfed.org/series/BAMLC0A0CM) identify investment-grade, US dollar domestic corporate debt; [FRED High Yield notes](https://fred.stlouisfed.org/series/BAMLH0A0HYM2) identify below-investment-grade US dollar corporate debt. These are daily close, aggregate option-adjusted spreads relative to a Treasury curve. FRED currently limits history to three years and does not provide these 2022 rows; Equibles supplies the historical pair. This verifies the displayed secondary-source observations and primary series definition/units, not an independently retrieved ICE historical file. Retrieved vintage and rounded observations are not certified original-vintage releases; exact publication times and quote clocks are unavailable. Observation dates do not establish availability by the macro-context cutoff. No inference of individual bond prices, exact basket OAS or European spread observations.

## Explicit instrument mapping and unchanged methodology

The portfolio contains four **long cash-bond baskets**, with positive marks/notionals and positive signed CS01, each explicitly classified IG or HY in `positions.csv`. It contains no credit shorts or CDS. Rates swaps have DV01 but no CS01 and receive no spread proxy. No sensitivities or instrument definitions are invented or changed.

| Position | Instrument/classification | Mark / reference notional | CS01, USD/bp | Historical proxy | Spread change | Credit P&L | Existing rates P&L | Net credit-position P&L |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| IG-US | Long US IG cash-bond basket | $14,000,000 | +6,300 | US Corporate OAS | 0bp | $0 | −$37,590 | −$37,590 |
| IG-EU | Long European IG cash-bond basket, FX hedged | $8,000,000 | +5,200 | US Corporate OAS, cross-region proxy | 0bp | $0 | −$30,072 | −$30,072 |
| HY-US | Long US HY cash-bond basket | $7,000,000 | +2,450 | US High Yield OAS | +18bp | −$44,100 | −$15,036 | −$59,136 |
| HY-EU | Long European HY cash-bond basket, FX hedged | $5,000,000 | +2,000 | US High Yield OAS, cross-region proxy | +18bp | −$36,000 | −$10,740 | −$46,740 |

**Mapping decision:** same-rating US cash-bond indices are plausible broad proxies for the US baskets, not exact constituent matches. Applying those indices to the European baskets is an explicit cross-region scenario assumption, supported by the existing rating buckets/CS01 structure rather than a claim to measured European moves. Currency hedging does not remove European credit-spread risk or establish US/European spread equivalence. US indices can therefore cover all modeled spread legs **conditionally on the disclosed proxy assumptions**; actual European/basket-specific spread changes remain unobserved. No position is assigned an index merely for having a broad credit asset class: the production source lists reviewed position IDs, expected cash-basket instrument, spread bucket, series and basis. Assembly rejects changed/unreviewed CS01 exposures or mismatched instrument/bucket/series instead of silently inheriting a proxy.

Use the existing unchanged engine: `credit_pnl = −signed_CS01 × spread_change_bp`. Total IG CS01 is $11,500/bp, HY $4,450/bp; credit P&L is `−11,500 × 0 − 4,450 × 18 = −$80,100`. Positive CS01 on these longs loses on widening. Existing signed sensitivities reverse that effect for a short exposure; a test-only sign reversal verifies this without adding production shorts.

Treasury-rate contribution remains `−signed_DV01 × 5.37bp`, applied once. Because OAS is already a spread over Treasuries, neither the index level nor a second Treasury-yield change enters the credit leg. Net bond P&L is its rate leg plus its spread leg; it must not be described as spread-only P&L. No new bond valuation model, duration assumption, convexity or optionality sensitivity is introduced.

## Reconciliation and interface

| Factor | Before | After | Change |
| --- | ---: | ---: | ---: |
| Rates | −$276,877.20 | −$276,877.20 | $0 |
| Equity | −$993,600.00 | −$993,600.00 | $0 |
| FX | −$146,000.00 | −$146,000.00 | $0 |
| Credit spreads | Unmeasured; omitted | −$80,100.00 | Newly included |
| Reported hypothetical sum | −$1,416,477.20 partial | **−$1,496,577.20** | **−$80,100.00** |

The revised sum covers all four **modeled** factors under the explicit proxies. It remains an estimated hypothetical result on fixed synthetic holdings, not exact historical portfolio valuation or an actual historical NAV. Parallel 10Y rates, a US equity return applied to both baskets, fixed linear sensitivities, asynchronous source quotes, rounded observations and omitted carry/convexity/default/liquidity/funding effects remain limitations.

The original What happened / What might explain it / How can we investigate layout remains intact. Show the new credit contribution, sourced IG/HY observations and estimated hypothetical total; retain expandable position/factor detail. A captured coverage flag controls labels: prior contexts without the flag keep their partial labels and unavailable spread presentation. No saved response or snapshot is migrated or automatically regenerated. Existing follow-up machinery continues to use captured context; only explicitly started new investigations load corrected data.

Subsequent Meta requests receive the revised historical observations, mapping assumptions, position/factor P&L and coverage in the existing joint context. The exact-three schema and competing-mechanism instructions remain. Prompt changes remove the unconditional missing-credit premise and distinguish new proxy-covered cases from legacy partial contexts. Existing demo mechanisms/titles are retained; only stale coverage wording is corrected. No new hypothesis narrative is hardcoded and no Meta call is made for this correction.

## Files and validation

Changed files:

- `backend/metis/data/historical-20220913.json`: verified OAS rows/units/sources and explicit position mappings; production assumptions revised.
- `backend/metis/reasoning/historical.py`: apply IG/HY changes through existing Shocks/calculate, check mappings/units, describe coverage in context/prompt and correct stale demo coverage text.
- `frontend/src/types.ts`, `frontend/src/investigation.ts`: optional captured coverage/OAS fields, request wording and coverage-aware scope labels.
- `frontend/src/InvestigationResults.tsx`, `frontend/src/InvestigationScope.tsx`, `frontend/src/InvestigationEvidence.tsx`: sourced credit moves/contributions and estimated hypothetical total; preserve legacy partial display.
- `tests/test_historical.py`, `frontend/tests/interface.test.mjs`: numeric/source/mapping/sign/reconciliation, mocked Meta payload, new versus old captured coverage and real component rendering checks.
- `README.md`, `research/RESEARCH_LOG.md`, this report and an appended link in `research/historical-hypothesis-implementation-20261103.md`: current workflow documentation and dated correction provenance. Prior report content remains unchanged.

Validation uses `.venv/bin/python -m pytest tests research/test_historical_macro_context.py research/test_meaning_alignment.py`, `npm test` and `npm run build`. Tests compare every position's rate/equity/FX legs with the old partial calculation, reconcile new credit and net legs, reverse a test CS01 sign, reject an unreviewed instrument, confirm updated Meta wire inputs and preserve a legacy captured partial context on follow-up. Existing archival tests continue to check the original missing-credit experiment, not retrofit its findings. Real React component tests verify the three-question order, included credit values/source links and old versus new coverage labels. No new manual browser check is claimed.

Final results and timings are recorded in the research log. Engine, original positions, March market/scenario data and original experimental input/response records remain unchanged. Existing Starlette/httpx deprecation and Vite large-bundle warnings remain. **0 live model calls / 0 inference tokens**; no model/settings exercised, inference latency not applicable; offline call census, monetary cost and separate verification latency unavailable. No A/B replication, push or merge. Stop with this sourced proxy-based numerical correction and local commit.
