# Metis

An institutional portfolio risk workstation with deterministic analytics and an independent financial interpretation harness. Runs locally with React / TypeScript / Vite, Tailwind CSS, Plotly.js, AG Grid Community, Python 3.12, FastAPI, NumPy and pandas. No database, trading, deployment infrastructure or agent framework. The v0.7 bounded financial claim checks extend AI Reasoning while preserving the six pages, four-stage workflow, Causal Exploration, financial analytics and live integration.

## Hackathon showcase: competing explanations

Metis's [three-minute causal-exploration showcase](research/meta-hackathon-causal-showcase-3min.md) starts on **Overview → Explore competing explanations**. It compares alternative economic explanations for the same hypothetical yield movement. The analyst accepts illustrative assumptions before the deterministic engine calculates both scenarios side by side; live model output is labeled **LIVE META** and fixed templates are labeled **DETERMINISTIC DEMO**. These are not calibrated forecasts or identified causes. The historical [longer demonstration plan](research/meta-hackathon-demo-plan.md) remains available.

**Live inference status (v0.2.1):** a live interpretation was verified with `muse-spark-1.3` at `https://api.meta.ai/v1/chat/completions` using locally configured credentials. This is Meta's Muse Spark model, not a Llama model. The returned interpretation passed all seven field definitions and the allowed evidence-ID check. No API key, sensitive context or full upstream response body was logged or saved. This verifies the harness; the browser workflow was not rerun for this correction. Demo mode still runs without credentials.

## Run locally

Prerequisites: [uv](https://docs.astral.sh/uv/getting-started/installation/) and Node.js 22.12+ (or a current supported Node release), with npm.

From the repository root:

```sh
uv sync --locked
cp -n .env.example .env  # Keep any existing local provider credentials.
uv run uvicorn metis.api.app:app --host 127.0.0.1 --port 8000 --reload
```

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open the Local URL printed by Vite (normally `http://127.0.0.1:5173`). Vite proxies `/api` to `127.0.0.1:8000`; keep both processes running. Both bind to loopback. No credentials are needed for the default deterministic demo. Stop each process with Ctrl+C.

```sh
# From the repository root
uv run pytest -q

# From frontend/
npm run build
npm run preview

# Focused frontend workflow/presentation tests (Node 22.12+)
npm test
```

The production preview also proxies `/api` to the local backend. This is a local development application, not a production deployment recipe. FastAPI documentation is at `http://127.0.0.1:8000/docs`.

## v0.4 investigation walkthrough

Keep the backend and frontend running using the commands above. The four-stage strip navigates within the existing six pages:

1. **What happened?** Open Overview to see the **−$560,770** illustrative daily loss for **2025-03-10**, rates **+$412,480**, credit spreads **−$407,250**, equities **−$506,000** and FX **−$60,000**. The principal-position panel selects the largest net loss and gain from backend values. Expand **Inspect position contributions and signed DV01** to compare separate rate/spread/equity/FX legs, net position P&L, signed DV01/CS01, marks and reference notionals. Portfolio totals come from the backend; the frontend does not recalculate them.
2. **Why did it happen?** Select **2 · Explain the daily loss**. This opens Metis AI Reasoning and immediately invokes the configured provider with the daily snapshot shocks. It leaves the separately selected stress scenario unchanged. The response shows its **LIVE META** or **DETERMINISTIC DEMO** label, original calculated evidence and a separate model interpretation. Expand economic explanations, principal observations and historical references as needed. Provider/validation errors remain visible and do not become demo answers.
3. **What could happen next?** Select **3 · Explore a hypothetical scenario**, choose Broad Risk-Off or adjust the existing shocks, then select **Interpret this scenario with Metis**. Scenario P&L and its factor contributions are labeled hypothetical, separate from daily P&L. The question captures the selected calculated shocks. Newest answers appear first; each answer retains the exact returned evidence after later scenario edits. Request state survives navigation and duplicate clicks are blocked while inference is active.
4. **What deserves investigation?** Select stage 4 or open the vulnerability section in an answer. Each model-identified vulnerability separates the model's text, available captured evidence and a topic-specific **analyst checklist** of missing information, with a link that opens the position calculations. The checklist uses simple headline keywords; it is neither a verified mapping of every model claim nor an estimate of liquidity, margin, default or correlation losses. Read the model's own assumptions/uncertainties alongside it.

Daily/scenario investigation actions start fresh, without replaying previous answers. Explicit free-form follow-ups use the selected investigation’s captured backend context and send only that investigation’s bounded conversation history. Context inspection remains available. Data is synthetic, historical episodes are qualitative references, stress results are not forecasts, and a positive rates contribution does not mean positive total portfolio P&L. There are no new pages, financial instruments, data pipelines, providers or automated model judges. The v0.3 ablation remains stopped; this iteration only verifies the application workflow.

v0.4 verification: **61 backend tests and 6 focused frontend tests pass**, and the production frontend build succeeds. Browser checks verified both daily-loss and Broad Risk-Off live interpretations using `muse-spark-1.3`, explicit live labels, calculation links, vulnerability checklists and stage navigation. After changing the current rate shock from −50bp to −45bp, the current stress became −$3,604,800 while the earlier answer retained its original −$3,347,000 calculation and the daily answer retained −$560,770. No browser warnings/errors were observed. Backend analytics, data, reasoning/provider code and the response contract are unchanged. Existing bundle-size and upstream test-client deprecation warnings remain. Model claims still require manual review; topic checklists do not validate or quantify missing risks.

## v0.5 financial judgment and investigation priorities

The executive conclusion now precedes the calculation tables. The prompt requests two sentences (at most 75 words): the leading economic risk, its mechanism, the hedge contribution versus total result, and a material uncertainty. This is prompt guidance, not a new schema constraint. Summaries longer than 480 characters display an explicitly labeled literal excerpt with the complete, unchanged model summary available on expansion. The question, detailed economics, observations, history and original evidence remain expandable; live/demo labels and provider errors remain visible.

Measured factor losses appear first, sorted by their supplied backend P&L, followed by offsets and the unchanged portfolio total. Model observations are labeled as claims to check, and unquantified vulnerabilities retain model order without a numerical ranking. Missing evidence prevents reliable comparison of funding, liquidity, counterparty and default loss magnitudes. Prompt guidance addresses HY net versus spread P&L, overlapping DV01 views, rates gains versus portfolio profit, and first-order CS01; it does not verify or silently correct model claims.

Stage 4 separates **Concern**, **Why it matters**, **Available evidence**, and **Next investigation**. Each concern retains the full original model rationale and proposed analysis on expansion. Separate, conditional analyst guides suggest concrete missing data (CSA/netting and collateral balances, margin sensitivity and available liquidity; issuer concentrations/ratings/recoveries; or market depth, execution costs and liquidation horizons). They assert neither a shortfall nor a loss estimate. Checklist selection uses short headline keywords; ambiguous long headings use a general evidence guide. A topic guide is not a verified association with every claim in the original text.

Validation: 63 backend tests and 9 frontend tests pass; production build succeeds. Live daily-loss and Broad Risk-Off requests both succeeded through the workstation using `muse-spark-1.3` at `https://api.meta.ai/v1/chat/completions`, with two-sentence conclusions and explicit LIVE META labels. Scenario observations correctly distinguished HY net from spread-only losses, first-order CS01, and the positive rates contribution from the negative portfolio total. Expandable historical details and credit/funding checklists were checked in the browser. An initial daily response placed an ordering preamble ahead of its topic; the prompt was clarified and long ambiguous headings now use a general evidence guide. These checks verify two application requests, not general model reliability. Deterministic analytics, financial data, response schema, provider settings and context assembly are unchanged. The ablation remains stopped. Historical analogies and numerical claims still require human review; prompt guidance cannot guarantee correctness or consistent prioritization.

## v0.6 Causal Exploration

Open **Scenario Analysis → Causal Exploration**. Independent Shocks preserves the existing sliders and presets. Causal Exploration instead asks how two possible economic mechanisms could produce the same initial government-yield movement with different credit, equity and FX consequences.

1. In Demo, choose **Recession fears**, **Inflation relief**, or **Liquidity and funding stress** for each hypothesis. Live Meta mode also accepts free-form hypotheses. Review the shared hypothetical yield move (default −50bp).
2. Select **Generate competing mechanisms**. The configured Meta model returns two structured hypotheses with transmission mechanisms, all five factor directions/rationales, alternatives, discriminating evidence, uncertainty and illustrative shocks. Responses show LIVE META or DETERMINISTIC DEMO explicitly. Supplied synthetic facts and original historical references remain inspectable; history is qualitative, not a calibrated causal estimate.
3. Review/edit both shock sets. Proposals do not execute automatically. Select **Accept reviewed shocks & calculate both** to invoke the existing scenario endpoint. Edits clear both old results. A warning identifies comparisons in which edited yield assumptions differ.
4. Compare the calculated factor/position P&L. **Use accepted A/B shocks in Independent Shocks** transfers those inputs to the existing scenario and AI investigation workflow. Captured causal results and edits survive mode/page switches within the session; reload clears them. Changing hypothesis controls affects only the next generation, never relabels an earlier answer.

`POST /api/causal-exploration` reuses the existing Meta adapter, sampling parameters and safe failure diagnostics with a bounded schema for exactly two mechanisms. It validates required factors, engine bounds, direction/shock sign consistency, the shared yield anchor and evidence IDs. These are contract checks, not proof of economic correctness. Live errors remain explicit without substitution. Demo supports the three named hypotheses with labeled fixed templates; custom hypotheses require Meta. No new provider, financial engine, top-level page, market feed or causal discovery framework is introduced.

Two live requests with `muse-spark-1.3` succeeded, covering recession, inflation relief, liquidity stress and a custom supply-normalization hypothesis. The first pair held yields at −50bp and produced deterministic totals of **−$29,500** versus **+$3,948,500** under its accepted cross-asset assumptions. Editing recession equities from −6% to −8% changed its result to **−$489,500**, reproduced exactly in Independent Shocks. Read the [focused manual review](research/causal-exploration.md) for assumptions, the second example and an underdeveloped forced-selling/rising-yield alternative in the liquidity explanation. These examples demonstrate conditional synthesis and workflow integrity, not causal identification, calibrated forecasts or general model reliability.

Validation: **73 backend tests, 12 frontend tests and production build pass**. The new focused checks cover the mechanism contract, alternative hypotheses and numerical identity; causal coherence is assessed manually. The financial analytics/data and v0.3 ablation remain unchanged. Existing bundle-size and test-client deprecation warnings remain.

## v0.7 bounded financial claim verification

Open **Metis AI Reasoning → Structured assertion checks · three reproducible examples**. No model is required: the mapped hedge-loss premises are **Contradicted**, the mapped positive-rate-contribution/negative-total premises are **Verified**, and the unsupported funding-shortfall assertion is **Not established**. Original prose remains **Not checked** in every case. Each shows its mapped premises, backend paths/values, original statement and missing information.

New live/demo interpretations can submit up to three `financial_claims` using an explicit interface. The backend checks numbers/signs for P&L and DV01/CS01, selected hedge-versus-total premises, exhaustive/disjoint DV01 decompositions, and whether funding/margin/liquidity/default losses are quantified. Unknown types/targets/metrics/precision are **Not checked**. Unmeasured risk is not automatically zero. Valid evidence IDs or model confidence do not establish correctness.

**Coverage matters:** verdicts apply to structured mappings, not arbitrary financial prose or semantic agreement between a sentence and its mapping. Original wording, omitted statements, economic explanations, causal narratives and hedge optimality remain **Not checked**. The original response and structured fields remain accessible, without silent rewriting. Claims can be omitted or mismapped; a correct mapped number cannot certify the surrounding sentence.

`POST /api/verify-claims` accepts claims plus optional scenario shocks, never caller-defined truth/calculations. `GET /api/verification-demo` returns the fixed examples. Normal reasoning checks its captured backend calculation context. Tolerances are fixed absolute values: 0.01 USD (or USD/bp) for `exact`, 0.5 for integer `whole`, and 5,000 USD for P&L declared to 0.01 million USD; unsupported precision is not accepted. No relative tolerance, prose extraction, second LLM or automated judge is used.

See the [bounded verification scope and manual review](research/financial-claim-verification.md), including an initial live kind-label coverage miss, an explicitly reported truncation, the compact-response correction, and known semantic coverage limits. The final live daily interpretation returned three valid mappings, all verified against the calculations. A separate live Causal Exploration request and accepted-scenario calculation also succeeded. Validation: **115 backend tests, 12 frontend tests and production build pass**, with existing deprecation and bundle-size warnings. These checks demonstrate limited functionality, not general financial reasoning reliability.

## Workstation pages

- **Overview:** closing NAV, daily P&L, allocation by signed net marked value, factor attribution, exposures and a market brief.
- **Portfolio:** 12 synthetic positions with sorting, column filters, full-table search, marks, notionals and daily P&L. Scroll horizontally for all columns on narrower screens.
- **Market Monitor:** dated illustrative yield levels and curve movement, IG/HY spreads, equity and FX changes, economic commentary and three sourced historical descriptions.
- **Risk Analytics:** signed DV01, CS01, equity/FX delta, position and factor attribution, and conventions.
- **Scenario Analysis:** four predefined scenarios; adjustable rates, IG/HY spreads, equity and EUR/USD shocks; live backend calculation and position/factor attribution. Controls persist across navigation; pending results are hidden to prevent displaying stale calculations.
- **Metis AI Reasoning:** questions and follow-ups, structured conclusions, principal risks, economic interpretation, historical analogies, vulnerabilities, uncertainties and evidence references. Each answer records its original context and mode. New stress investigations capture the current scenario; follow-ups retain the selected investigation’s original context. Conversations and scenario state last for the browser session and reset on reload.

## Follow-up calculation scope

Each successful investigation returns a backend-owned `investigation_id` and a `daily` or `scenario` scope. Answers show the captured market date, portfolio/NAV and shock assumptions. The follow-up composer defaults to that investigation and offers a selector (or **Continue this investigation** on an earlier answer) to resume an older one. Only the last three question/summary pairs from the selected investigation are replayed. Edits to current scenario controls, pending calculations and failures in those controls do not replace or block captured evidence.

To change scope, use **Start new daily investigation**, **Start new investigation of current stress**, or **Interpret this scenario with Metis**. These actions capture a new backend context and start with empty history. Merely mentioning different assumptions in a follow-up does not apply them; explicitly start a new investigation. Previous answers and calculations remain unchanged. The sidebar labels current controls as inputs for new investigations.

`POST /api/reasoning` accepts either a new investigation (`question`, `shocks`, optional `investigation_scope`, default `scenario`) or a follow-up (`question`, `investigation_id`, bounded `history`). Explicit daily scope uses the backend's daily shocks. Follow-ups accept no replacement shocks, scope or caller-supplied calculations: the backend reuses its full captured portfolio, market, daily/scenario results, alternatives, historical context and conventions. The existing provider adapter and verifier operate against that snapshot; engine and verification rules are unchanged.

Snapshots are held only in memory in the existing local backend, with a maximum of 128 new investigations per process (oldest evicted first). They are not durable sessions; browser reload clears conversation state, and backend restart/eviction invalidates references. Missing snapshots or changed provider mode/model return an explicit 409 asking for a new investigation, with no current-context substitution. Normal provider failures remain 502 with no demo fallback. Evidence-only snapshots retain the existing no-history boundary. This is for the existing single-process loopback workstation, not distributed hosting, authentication or persistent storage. No live inference was run to validate this correction.

## Data and single source of truth

`backend/metis/data/` contains the only position, market, historical and preset inputs. All pages load `/api/workstation`; custom scenarios and reasoning use the same analytics functions. The frontend does not calculate financial P&L.

| File | Contents |
| --- | --- |
| `positions.csv` | 12 USD-valued positions across government bonds, swaps, IG/HY credit, equities, FX and cash |
| `market.json` | One **synthetic** close dated 2025-03-10 and comparison dated 2025-03-07; dates are example labels, not claims about actual closes |
| `scenarios.json` | Four **illustrative**, uncalibrated stress assumptions |
| `history.json` | Sourced qualitative historical facts, separate portfolio interpretations and limitations |

No portfolio mark, exposure, yield, spread, equity move or FX level is live or an actual historical observation. The opening NAV is reconstructed from closing marks and modeled daily P&L; there is no independent historical valuation series.

The historical library references [Federal Reserve History on the Great Recession](https://www.federalreservehistory.org/essays/great-recession-of-200709), the [March 23, 2020 market-functioning statement](https://www.federalreserve.gov/newsevents/pressreleases/monetary20200323a.htm), and the [December 14, 2022 inflation and policy statement](https://www.federalreserve.gov/newsevents/pressreleases/monetary20221214a.htm). Historical facts are qualitative context. Portfolio analogies are economic interpretation. Scenarios do not replay these episodes.

## Financial conventions

All sensitivities and P&L are in USD; basis point shocks are entered as `50`, not `0.005`. Percent shocks are entered as `-15`, not `-0.15`.

```text
Rates P&L  = −DV01 × government yield shock in bp
Credit P&L = −CS01 × applicable IG or HY spread shock in bp
Equity P&L = equity USD delta × equity shock in % / 100
FX P&L     = FX USD delta × EUR/USD shock in % / 100
```

- Positive DV01 / CS01 means a gain for a 1bp decline. Pay-fixed swap DV01 is negative; receive-fixed is positive. Credit bonds have both government-rate sensitivity and spread sensitivity, so the two components are added.
- Swap marks are signed NAV contributions. Notional is reference size, not NAV or P&L sensitivity. Swaps use supplied DV01; no attempt is made to infer duration from their net marks.
- Positive FX delta means long EUR / short USD. A 1% EUR/USD rise on the $10m FX delta produces $100,000. The forward's $2m signed mark contributes to NAV independently. Interest-rate sensitivity of the FX forward is omitted.
- Hedged credit and equity baskets have zero residual FX exposure by assumption. All equities receive the same shock (unit beta). Government yields move in parallel, including the rate component of European credit; country/curve basis is omitted.
- Closing NAV is the sum of signed marks: **$100,000,000**. Daily modeled P&L is **−$560,770**. Opening NAV is **$100,560,770**, so opening NAV + daily P&L = closing NAV. The daily return uses opening NAV; scenario percentages use current closing NAV.
- Allocation charts use **net marked value**, not gross notional or risk allocation. The derivative asset class nets to $3m despite materially larger risk exposure.
- Calculations round each position's factor contribution to cents before aggregation; the UI normally displays whole dollars. This is a reporting convention, not a claim of pricing accuracy.

### Reference calculations

| Calculation | USD |
| --- | ---: |
| Aggregate DV01, per bp fall | 51,560 |
| Aggregate CS01, per bp fall | 15,950 |
| IG / HY CS01, per bp fall | 11,500 / 4,450 |
| Equity / FX delta | 23,000,000 / 10,000,000 |
| Daily rates contribution (−8bp) | +412,480 |
| Daily credit contribution (+18bp IG, +45bp HY) | −407,250 |
| Daily equities (−2.2%) | −506,000 |
| Daily FX (−0.6%) | −60,000 |
| Rate rally (−50bp, other shocks zero) | +2,578,000 |
| Rate selloff (+50bp, other shocks zero) | −2,578,000 |
| Credit widening (+50bp IG, +150bp HY) | −1,242,500 |
| Broad risk-off (−50bp rates, +75bp IG, +250bp HY, −15% equities, −5% FX) | −3,347,000 |

No convexity, optionality, curve/key-rate risk, spread-rate basis, default jumps, carry, cash interest, transaction costs, margin requirements, hedge slippage or funding/liquidity losses are modeled. Sensitivities are fixed inputs, not recalibrated. Large stress results are particularly approximate. Input bounds only constrain the demonstration UI; they are not calibrated risk limits.

## Reasoning harness and providers

`backend/metis/reasoning/harness.py` is independent of FastAPI and the frontend. `reason(ReasoningRequest(...))` retrieves portfolio exposures, the selected market snapshot, deterministic daily and scenario P&L, curated history and evidence IDs. Context also includes compact deterministic comparisons for the four existing scenario presets, referenced by `[alternatives]`. It invokes a small `Provider.interpret` interface and returns a validated structured interpretation plus the exact context and an inspectable list of backend context operations.

The v0.2 prompt uses the existing response fields for an executive assessment, ranked exposures, interacting economic drivers, applicable historical patterns, vulnerabilities under alternative regimes, and material uncertainty. It explicitly distinguishes the dated synthetic daily snapshot from hypothetical stresses. A rate-only selloff is not described as a fully modeled inflation shock. Numerical comparisons come from the backend, not model arithmetic. Responses remain subject to human review; structural validation does not establish financial accuracy.

The four context operations are application-driven retrieval/calculation steps, **not autonomous model-requested tool calls**. There is no planning loop. The model interprets calculations rather than providing financial calculations to the UI. Context inspection is available below each answer. The prompt requests concise explanations, not private chain-of-thought. Live output is validated structurally and evidence IDs must belong to the supplied context; this does not guarantee economic correctness or verify each prose claim.

### Deterministic demo

```dotenv
METIS_PROVIDER=demo
```

No model call is made. A small set of question themes selects fixed economic explanations populated with actual backend calculations, selected shocks, and historical references. This is useful for end-to-end demos, not evidence of LLM reasoning capability. Demo responses are labeled prominently and do not constitute general question answering. Follow-up history is sent to live providers; the demo does not reason over it.

### Meta Model API / compatible Llama endpoint

```dotenv
METIS_PROVIDER=meta
METIS_MODEL=<your-endpoint-model-id>
METIS_META_BASE_URL=https://<your-inference-host>/v1
METIS_META_API_KEY=<your-key>
```

The adapter calls `POST <base>/chat/completions` with bearer authentication and system/user messages. It sends the existing interpretation schema in API-level `response_format` with `type=json_schema` and `strict=true`, including an enum of the current evidence IDs. Local Pydantic field validation and the evidence allowlist remain authoritative. Meta documents this configuration for Muse Spark in its [structured-output guide](https://dev.meta.ai/docs/structured-output). The verified configuration is `METIS_MODEL=muse-spark-1.3` and `METIS_META_BASE_URL=https://api.meta.ai/v1`; the key is supplied locally via `METIS_META_API_KEY`.

Other Meta/Llama models require a compatible **Chat Completions endpoint with JSON-schema output support**. No specific host or model is hardcoded. Unsupported schema configurations fail visibly; there is no downgrade to prompt-only JSON or demo output. Do not append `/chat/completions` to the base URL. Local HTTP is allowed for development; remote endpoints require HTTPS. Embedded credentials, query parameters and fragments are rejected.

Set `METIS_PROVIDER=meta` and all three variables above in the server environment or a root `.env` copied from `.env.example`, then restart the backend. A missing variable is identified by name without exposing its value. Successful responses display **LIVE META · model ID** in the existing interface; demo responses display **DETERMINISTIC DEMO**. The live badge indicates which transport returned the response, not that its financial claims are verified. Authentication/access errors, wrong endpoints/models, quota errors, timeouts and malformed structured output produce actionable errors without a demo fallback or upstream response-body disclosure.

#### v0.2.1 structured-output diagnosis

The original failure was reproduced live: HTTP 200, `finish_reason=length`, and a partial 1,761-character JSON string without a Markdown fence. The 3,000-token limit exhausted the completion budget; it was not an authentication or envelope failure. Meta's [reasoning documentation](https://dev.meta.ai/docs/reasoning) explains that reasoning consumes the output budget as well as visible text. The adapter now uses `max_completion_tokens=8000` plus the supported API-level JSON schema. A subsequent live broad risk-off request completed and validated successfully.

Errors distinguish `[truncated]`, `[markdown_wrapped_json]`, `[invalid_json]`, `[schema_validation]`, `[unknown_evidence]`, unexpected response envelopes/completion reasons, empty content and refusals. Schema diagnostics contain only known application field names and validation error types, never model values, unknown field names, raw Pydantic errors or upstream bodies. HTTP 400 with a recognized schema parameter or `invalid_json_schema` code is labeled `[structured_output_configuration]`; other 400s are `[request_rejected]` without guessing their cause. No partial JSON repair, fence stripping, missing-field synthesis or automatic format downgrade is performed.

### Anthropic Claude

```dotenv
METIS_PROVIDER=anthropic
METIS_MODEL=<your-accessible-claude-model-id>
ANTHROPIC_API_KEY=<your-key>
```

Calls `https://api.anthropic.com/v1/messages` with `x-api-key`, API version `2023-06-01`, system instructions and bounded conversation history. See the [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages/create). Choose a model ID available to your account; none is hardcoded.

Restart the backend after editing `.env`. Keep keys server-side. Explicit live mode with missing configuration, an upstream error, malformed JSON, truncation or unknown evidence IDs returns an error; it never silently falls back to demo. Upstream error bodies are not exposed. New live investigations transmit the assembled application context; follow-ups transmit the captured context and up to three prior question/summary pairs from that investigation to its configured provider. This version is intended for its synthetic data.

### Use without the web UI

From the repository root, with `uv sync` complete:

```sh
uv run python - <<'PY'
import json
from dotenv import load_dotenv
from metis.analytics.engine import Shocks, load_json
from metis.reasoning.harness import ReasoningRequest, reason

load_dotenv()
preset = next(s for s in load_json("scenarios") if s["id"] == "risk-off")
result = reason(ReasoningRequest(
    question="Given the portfolio's exposures, current market conditions, and relevant historical patterns, what are its principal risks, and why?",
    shocks=Shocks(**preset["shocks"]),
))
print(json.dumps(result, indent=2))
PY
```

### One reasoning demonstration

1. Review the portfolio and the **2025-03-10 illustrative snapshot** in Overview / Market Monitor. This is the current application snapshot, not today's market data.
2. In Scenario Analysis, select **Broad risk-off**: −50bp rates, +75bp IG spreads, +250bp HY spreads, −15% equities, −5% EUR/USD.
3. Select **Interpret this scenario with Metis**, then choose the first suggested question (the exact question in the Python example above).
4. Inspect the response's mode badge, economic explanation, historical references, uncertainties and saved context. The selected scenario should show **−$3,347,000**, with rates **+$2,578,000**, credit **−$1,975,000**, equities **−$3,450,000**, and FX **−$500,000**. These are hypothetical stress results; the dated daily loss remains **−$560,770**.

**Illustrative demo interpretation — not a live model response:** A Treasury rally can signal weaker growth rather than improving conditions for all assets. Duration gains can be outweighed by spread and equity losses: the broad risk-off stress loses $3.347m despite a $2.578m rate gain. The sourced 2008 description motivates a credit/equity risk analogy; March 2020 motivates scrutiny of liquidity and margin needs. The 2022 inflation regime offers a contrasting risk: rates can rise while risky assets also weaken. The existing rate-only selloff loses $2.578m with other factors held constant; it does not quantify a combined inflation shock. Default jumps, funding, curve basis and nonlinearity remain outside the calculation. Historical comparisons are qualitative, not claims about how this synthetic portfolio performed in those episodes.

This walkthrough runs in demo mode without credentials, or through the configured live provider. The v0.2.1 live harness check used this question and scenario and validated the structured result. The illustrative paragraph above remains a demonstration example, not a transcript of the live response.

## API surface

- `GET /api/health`: readiness and version.
- `GET /api/workstation`: consistent positions, NAV, exposures, daily attribution, market, presets and historical library.
- `POST /api/scenario`: a shock object (`rates_bp`, `ig_bp`, `hy_bp`, `equity_pct`, `fx_pct`); returns total, factor, asset-class and position P&L. Omitted shocks default to zero; extra fields and nonfinite/out-of-range values are rejected.
- `POST /api/reasoning`: `{question, shocks, history?, context_mode?}`; returns mode/model, context mode, available token usage, structured interpretation, supporting evidence, original context and context operations. No streaming or conversation persistence.

## Validation and limitations

### v0.3 paired financial reasoning ablation

The existing request accepts `context_mode="full"` (default, Condition A) or `context_mode="evidence_only"` (Condition B). The workstation keeps its existing full-context behavior. Evidence-only requests require empty conversation history, preventing earlier narrative answers from leaking back into the comparison.

Condition B omits only `market.commentary`, each historical entry's `interpretation`, and the broad risk-off alternative's causal `description` ("Growth shock"). All portfolio marks/exposures, daily and scenario calculations, market observations, financial conventions, historical facts, source references, limitations and evidence IDs remain identical. Technical descriptions of the other scenario assumptions remain. Neither the question nor the system prompt, model, response schema or sampling settings changes between conditions.

Run the fixed Broad Risk-Off comparison with the configured live Meta provider:

```sh
uv run python -m metis.reasoning.ablation
# Optional fresh output location; existing directories are never overwritten:
uv run python -m metis.reasoning.ablation --output-dir research/runs/my-paired-run
```

The command calls Full Context then Evidence Only, once each, without chat history or automatic retries. It freezes the provider configuration for both calls and uses the existing `temperature=0.2`, `max_completion_tokens=8000` and strict JSON schema. It saves private local `manifest.json`, `full.json` and `evidence_only.json` files under the ignored `research/runs/` directory. Records include the question, model, shocks, actual contexts, validated structured responses, available token counters and sanitized execution errors. The manifest captures the system prompt, response schema, evidence IDs, code/data hashes, numerical-input fingerprint and execution order. No API keys, raw HTTP bodies or private reasoning text are saved. The CLI prints only completion metadata and exits nonzero if either call fails; missing credentials never produce a substitute demo result. Token usage is reported by the provider, with `null` when unavailable.

Tests verify exact context differences, unchanged quantities/facts/sources, identical non-context wire parameters, no cross-condition history, usage filtering, and recorded configuration failures. See [the reviewed comparison](research/financial-reasoning-ablation.md) for the paired observations and assessment. Raw outputs stay local and are not committed.

v0.3 validation: **60 tests pass**, the frontend production build succeeds, and both live `muse-spark-1.3` conditions completed with valid structured responses. Both recovered the central risk conclusion; Evidence Only contained a net-versus-spread HY loss labeling error. This single pair does not establish an overall quality difference. Existing test-client deprecation and frontend bundle-size warnings remain non-blocking.

This is a reproducible procedure, not deterministic regeneration or a benchmark: one stochastic sample per condition cannot establish a causal effect. The unchanged system prompt already suggests risk channels and recession/inflation contrasts, and the selected historical episodes and "risk-off" label are cues in both conditions. Shorter context, run order and server-side nondeterminism are additional confounders. No automated judge or model self-assessment is used.

The automated suite covers portfolio loading, aggregation, signs/units, accounting reconciliation, factor/position/asset-class attribution, zero and preset stresses, superposition, validation boundaries, demo context consistency, full API workflows, and mocked request/response contracts for Meta-compatible and Anthropic endpoints. Mock tests do not assess model quality.

v0.2.1 validation: **56 pytest tests pass** and **`npm run build` succeeds**. The unchanged deterministic analytics tests pass. Tests cover broad risk-off context, alternative-scenario calculations, provider configuration and HTTP/network failures, API-level JSON-schema request configuration, actual truncation shape, Markdown wrappers, missing/wrong/extra fields, field constraints, invalid evidence IDs and unexpected response envelopes. Private fixture content is excluded from errors and captured logs. One corrected live Muse Spark response validated all seven fields, eight principal observations, three historical analogies and eight allowed evidence references; its selected scenario P&L remained −$3,347,000. Live Anthropic inference remains untested. The earlier v0.1 browser smoke checks covered all six pages; this patch changes no interface or analytics code and does not add a browser verification claim. pytest still reports an upstream Starlette/httpx test-client deprecation warning, and Vite reports the existing large bundle warning.

There is no authentication, persistence, real-time data, optimizer, probability model, historical backtest, production security boundary or deployment support. Scenario and chat state reset on refresh. The harness provides structured explanations, not independently verified financial advice or a complete institutional risk model.

## Smallest next step for a Meta hackathon demo

Restart the backend with the local Meta configuration and rehearse the existing Overview → Scenario Analysis → Metis AI walkthrough, checking the LIVE META badge and saved evidence context. No additional infrastructure is needed.

## Historical hypothesis investigation · September 13, 2022

Open **Metis AI Reasoning → Investigate September 13, 2022 · US CPI surprise**. The existing provider receives the prepared historical observations, same-day CPI backdrop, synthetic fixed holdings/exposures and backend partial-factor P&L together. Meta must return exactly three hypotheses, each with an economic mechanism, market implications, portfolio implications and proposed distinguishing evidence. Demo mode uses explicitly labeled deterministic templates. Follow-ups retain this captured historical context independently of stress controls.

The three-question interface remains **What happened? / What might explain it? / How can we investigate?** Historical inputs reuse [the completed research](research/historical-macro-context-20220913.md); the March 2025 illustrative dataset and risk engine are unchanged. The sourced IG OAS change is 0bp and HY is +18bp. Explicit mappings apply these US indices to the four existing IG/HY cash-bond baskets, with the European baskets labeled as cross-region proxies. The estimated hypothetical P&L includes all four modeled factors; it is not an exact historical portfolio valuation. Previously captured partial-factor investigations retain their original evidence and labels. Synthetic current holdings, parallel 10Y rates and S&P mappings are assumptions, not historical portfolio observations. No automatic retrieval, hypothesis validation or new provider is added.

See [implementation validation and live-call findings](research/historical-hypothesis-implementation-20261103.md) for examples, file inventory and limitations. Raw application responses remain local under ignored `research/runs/`.

Credit correction: [verified sources, position mapping, CS01 reconciliation and validation](research/historical-credit-pnl-correction-20261103.md). Credit-spread P&L is −$80,100 and total estimated hypothetical P&L is −$1,496,577.20; the engine and non-credit legs are unchanged.
