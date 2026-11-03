# Historical hypothesis implementation · 2026-11-03

## Scope and implementation decision

Implement the September 13, 2022 CPI investigation within the existing AI Reasoning workflow. Reuse the original sourced inputs from `2b75a7c`; do not repeat the completed macro/no-macro comparison. This is product integration validation, not a new comparative reasoning study or causal test. No retrieval, automated hypothesis validation, risk-engine changes, new provider or dependencies.

The historical start sends positions, signed exposures, engine P&L, observed market movements and same-day macro context together through the existing Meta adapter. A historical response subclass requires exactly three hypotheses and adds required portfolio implications to the existing mechanism, market-consistency, uncertainty and proposed-evidence fields. The prompt asks for economically distinct drivers, mechanism transmission, position-level relevance and evidence that would weaken each explanation; hypotheses may overlap. Schema compliance does not establish semantic distinctness or causal truth. Existing provider settings and daily/stress prompts remain unchanged.

Captured historical evidence and provider identity survive follow-ups. Caller shocks cannot replace historical source inputs. This case has no structured financial claims because existing verifier periods do not represent historical partial-factor coverage; numerical/hypothesis validation has not been added. Demo templates remain explicitly labeled and separate from model findings.

## Data and presentation

The production JSON is a byte-identical copy of `research/historical-macro-20220913-inputs.json`. It retains BLS original-release and Reuters contemporaneous reporting provenance, missing-spread statuses, source clocks and all five proxy-mapping assumptions. Current synthetic holdings are distinct from historical observations. Original research artifacts and March 2025 data are preserved.

Historical observations: 10Y +5.37bp, 2Y +17.24bp, reported S&P 500 −4.32%, EUR/USD −1.46%. The unchanged engine applies the documented 10Y parallel and common-equity proxies to synthetic fixed positions: rates −$276,877.20, equities −$993,600, FX −$146,000; partial-factor total −$1,416,477.20. Unknown IG/HY spread contributions use engine zero placeholders solely to omit those factors. Complete historical P&L remains unknown; this is neither an actual portfolio replay nor a calibrated backtest.

The three-question layout remains intact. What happened shows the date, observed moves, supplied macro facts/source links, computed attribution and missing-data warning. What might explain it shows three mechanisms, market/portfolio implications and uncertainties. How can we investigate lists proposed comparisons and additional distinguishing evidence. Supporting calculations, position detail, references and context remain expandable. Spread contributions display Unavailable, including in detail tables; total/position labels identify partial-factor coverage. A date on the global market strip distinguishes the unchanged March 2025 workstation snapshot from the historical answer. No hypothesis checks are automatically performed.

## One live Meta integration check

**Protocol:** one case, one application `/api/reasoning` start with historical scope, no conversation history, no retries or demo substitution. Explicit purpose: check the newly integrated joint context, exact-three schema and hypothesis quality in the intended workflow, not replicate the earlier comparison. Criteria: all three input groups delivered; exactly three distinct economic mechanisms; connections to observed moves and supplied positions/contributions; proposed distinguishing evidence; honest omissions and conditional language. Manual inspection, no model judge.

**Settings/telemetry:** `muse-spark-1.3`, existing Meta endpoint `https://api.meta.ai/v1/chat/completions`, temperature 0.2, `max_completion_tokens=8000`, `reasoning_effort=low`, strict JSON schema, 60-second HTTP timeout. Request began 2026-11-03 06:33:07 PST (14:33:07 UTC). One successful application HTTP 200 response, accepted by the adapter's completed-response and schema checks. Latency **23.724278 seconds**. Provider usage: **10,609 prompt + 2,805 completion = 13,414 total tokens**, including **1,146 reasoning tokens** within completion. Hosted weights/revision, seed, monetary cost and separate network/model latency are unavailable. Private request, application response and telemetry: ignored `research/runs/historical-product-20261103/`, directory 0700 / files 0600. No private responses are included here.

**Observed hypotheses (analyst paraphrases, not raw model output):**

1. **Near-term policy-path and real-yield repricing:** persistent inflation could raise policy expectations and discount rates. The response relates the larger front-end move, Treasury losses, receive-fixed IRS-R losses and pay-fixed IRS-P offset, with equity losses dominating the supplied partial result. Proposed discrimination includes policy futures around the release; little policy repricing would weaken this account.
2. **Growth, earnings and credit-risk premium repricing:** recession and earnings concerns could reduce equity valuations and increase risk premia. It connects EQ-US/EQ-DM proxy losses to long equity deltas and recognizes unmeasured CS01 exposure in all four credit baskets. Proposed evidence includes earnings revisions, recession indicators and actual IG/HY spreads; resilient earnings and tight spreads would weaken the channel.
3. **Dollar safe-haven and dovish-position unwind:** reversal of prior optimism could trigger dollar demand and de-risking. It connects FX-EUR losses to the long-EUR delta and concurrent equity weakness. Proposed evidence includes intraday timing, positioning and liquidity gauges.

**Quality observations and limitations:** the three explanations emphasize discount rates, cash flows/risk premia and flows/positioning rather than three policy paraphrases. They are conditional and overlapping, not independently validated. All identify supplied positions and signs of calculated contributions; they mostly use qualitative magnitude comparisons rather than exact dollar amounts, which the UI supplies directly. No missing spread move is presented as measured; no core consensus surprise or later policy outcome is asserted. Real-yield repricing is a hypothesis requiring real-yield data. The third explanation does not fully explain rising Treasury yields, and its proposed-check wording ambiguously groups FX-hedged credit baskets with equity legs even though those baskets have zero equity delta. This is a model wording limitation, not an engine change or established equity exposure in credit. Preserve the observed limitation without silently repairing the private response or launching further inference.

**Interpretation/decision:** this response demonstrates the intended context-to-hypotheses-to-proposed-evidence workflow. One selected completion cannot establish general quality, robustness, semantic validation or causality. Retain the small integration for interface/quality review and stop after this call. Missing spreads, asynchronous quotes, rounded FX return, unobserved prior FX quote, curve/global-equity proxies and fixed synthetic holdings bound the result.

## Changed files

- `backend/metis/data/historical-20220913.json`: unchanged research inputs copied into packaged application data.
- `backend/metis/reasoning/historical.py`: source assembly, historical schema/prompt and labeled offline templates.
- `backend/metis/reasoning/harness.py`: dispatch through existing provider/adapter and historical context operation metadata.
- `backend/metis/reasoning/followup.py`: historical investigation scope; existing snapshot machinery retained.
- `frontend/src/App.tsx`, `frontend/src/investigation.ts`, `frontend/src/types.ts`: historical entry point, request/scope plumbing, historical data and portfolio-implication types; dated global strip.
- `frontend/src/InvestigationResults.tsx`, `frontend/src/InvestigationScope.tsx`, `frontend/src/InvestigationEvidence.tsx`: historical facts/macro presentation, portfolio implications, explicit proxy/omission labels in existing sections/details.
- `tests/test_historical.py`, `frontend/tests/investigation.test.mjs`, `frontend/tests/interface.test.mjs`: joint wire-input/schema/failure checks, immutable follow-up evidence, unchanged source/results, historical routing and real-component rendering.
- `research/test_historical_macro_context.py`: verify the completed experiment's original production-harness hash at preserved commit `2b75a7c`, while comparing all frozen contexts and other source hashes. Product prompt evolution must not rewrite historical records. The unchanged historical runner's full source-fingerprint comparison still belongs to its original revision.
- `README.md`, this report, `research/RESEARCH_LOG.md`: workflow instructions, findings and validation provenance.

## Validation

Initial validation found an archival test comparing the completed experiment's harness fingerprint with evolving production code (163 passed / 1 failed). Corrected the test's provenance lookup as described above; no archived hashes, inputs, findings or runner were changed. Initial local-server binds were sandbox-restricted, then default ports were occupied; isolated demo servers on 8100/5184 enabled browser checks without disturbing existing servers.

Final test/build results and browser checks are recorded in the appended research log. Browser smoke validation uses deterministic templates; the separate single live API call checks Meta output. Browser start and follow-up create no additional inference calls. Current March daily −$560,770 and Broad Risk-Off −$3,347,000 regressions pass; engine and original data bytes are unchanged in Git. Existing Starlette/httpx deprecation and Vite bundle-size warnings remain. Deterministic/mocked call census and offline latency/cost are not tabulated. No push or merge authorized.
