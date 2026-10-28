# Metis v0.1

An institutional portfolio risk workstation with deterministic analytics and an independent financial interpretation harness. Runs locally with React / TypeScript / Vite, Tailwind CSS, Plotly.js, AG Grid Community, Python 3.12, FastAPI, NumPy and pandas. No database, trading, deployment infrastructure or agent framework.

## Run locally

Prerequisites: [uv](https://docs.astral.sh/uv/getting-started/installation/) and Node.js 22.12+ (or a current supported Node release), with npm.

From the repository root:

```sh
uv sync --locked
cp .env.example .env
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
```

The production preview also proxies `/api` to the local backend. This is a local development application, not a production deployment recipe. FastAPI documentation is at `http://127.0.0.1:8000/docs`.

## Workstation pages

- **Overview:** closing NAV, daily P&L, allocation by signed net marked value, factor attribution, exposures and a market brief.
- **Portfolio:** 12 synthetic positions with sorting, column filters, full-table search, marks, notionals and daily P&L. Scroll horizontally for all columns on narrower screens.
- **Market Monitor:** dated illustrative yield levels and curve movement, IG/HY spreads, equity and FX changes, economic commentary and three sourced historical descriptions.
- **Risk Analytics:** signed DV01, CS01, equity/FX delta, position and factor attribution, and conventions.
- **Scenario Analysis:** four predefined scenarios; adjustable rates, IG/HY spreads, equity and EUR/USD shocks; live backend calculation and position/factor attribution. Controls persist across navigation; pending results are hidden to prevent displaying stale calculations.
- **Metis AI Reasoning:** questions and follow-ups, structured conclusions, principal risks, economic interpretation, historical analogies, vulnerabilities, uncertainties and evidence references. Each answer records its original context and mode. The current scenario is included in every request. Conversations and scenario state last for the browser session and reset on reload.

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

`backend/metis/reasoning/harness.py` is independent of FastAPI and the frontend. `reason(ReasoningRequest(...))` retrieves portfolio exposures, the selected market snapshot, deterministic daily and scenario P&L, curated history and evidence IDs. It invokes a small `Provider.interpret` interface and returns a validated structured interpretation plus the exact context and an inspectable list of backend context operations.

The four context operations are application-driven retrieval/calculation steps, **not autonomous model-requested tool calls**. There is no planning loop. The model interprets calculations rather than providing financial calculations to the UI. Context inspection is available below each answer. The prompt requests concise explanations, not private chain-of-thought. Live output is validated structurally and evidence IDs must belong to the supplied context; this does not guarantee economic correctness or verify each prose claim.

### Deterministic demo

```dotenv
METIS_PROVIDER=demo
```

No model call is made. A small set of question themes selects fixed economic explanations populated with actual backend calculations, selected shocks, and historical references. This is useful for end-to-end demos, not evidence of LLM reasoning capability. Demo responses are labeled prominently and do not constitute general question answering. Follow-up history is sent to live providers; the demo does not reason over it.

### Meta-compatible / Llama endpoint

```dotenv
METIS_PROVIDER=meta
METIS_MODEL=<your-endpoint-model-id>
METIS_META_BASE_URL=https://<your-inference-host>/v1
METIS_META_API_KEY=<your-key>
```

The adapter calls `POST <base>/chat/completions` with bearer authentication, system/user messages and a JSON-output schema in the prompt. Use a Meta/Llama model served behind an **OpenAI-compatible Chat Completions endpoint**. This is a transport adapter, not a guarantee that every Meta-hosted or Llama-serving API uses that protocol. The endpoint/model must support producing the requested JSON. No specific model ID or host is assumed. A local HTTP endpoint is allowed for development; remote endpoints require HTTPS.

### Anthropic Claude

```dotenv
METIS_PROVIDER=anthropic
METIS_MODEL=<your-accessible-claude-model-id>
ANTHROPIC_API_KEY=<your-key>
```

Calls `https://api.anthropic.com/v1/messages` with `x-api-key`, API version `2023-06-01`, system instructions and bounded conversation history. See the [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages/create). Choose a model ID available to your account; none is hardcoded.

Restart the backend after editing `.env`. Keep keys server-side. Explicit live mode with missing configuration, an upstream error, malformed JSON, truncation or unknown evidence IDs returns an error; it never silently falls back to demo. Upstream error bodies are not exposed. Live requests transmit the assembled application context and up to three prior question/summary pairs to the configured provider. This version is intended for its synthetic data.

### Use without the web UI

From the repository root, with `uv sync` complete:

```sh
uv run python - <<'PY'
import json
from dotenv import load_dotenv
from metis.analytics.engine import Shocks
from metis.reasoning.harness import ReasoningRequest, reason

load_dotenv()
result = reason(ReasoningRequest(
    question="Why can falling Treasury yields coexist with portfolio losses?",
    shocks=Shocks(rates_bp=-50, ig_bp=75, hy_bp=250, equity_pct=-15, fx_pct=-5),
))
print(json.dumps(result, indent=2))
PY
```

## API surface

- `GET /api/health`: readiness and version.
- `GET /api/workstation`: consistent positions, NAV, exposures, daily attribution, market, presets and historical library.
- `POST /api/scenario`: a shock object (`rates_bp`, `ig_bp`, `hy_bp`, `equity_pct`, `fx_pct`); returns total, factor, asset-class and position P&L. Omitted shocks default to zero; extra fields and nonfinite/out-of-range values are rejected.
- `POST /api/reasoning`: `{question, shocks, history?}`; returns mode/model, structured interpretation, supporting evidence, original context and context operations. No streaming or persistence.

## Validation and limitations

The automated suite covers portfolio loading, aggregation, signs/units, accounting reconciliation, factor/position/asset-class attribution, zero and preset stresses, superposition, validation boundaries, demo context consistency, full API workflows, and mocked request/response contracts for Meta-compatible and Anthropic endpoints. Mock tests do not assess model quality.

Implementation validation: **20 pytest tests pass** and **`npm run build` succeeds**. Browser smoke checks cover all six pages, grid filtering/sorting, preset selection, customized shocks and scenario-to-reasoning context consistency. No browser warnings/errors were observed. No model credentials were configured, so **neither live provider was invoked**. pytest currently reports an upstream Starlette/httpx test-client deprecation warning. Vite reports a large bundle warning because Plotly and AG Grid are included; acceptable for this local v0.1.

There is no authentication, persistence, real-time data, optimizer, probability model, historical backtest, production security boundary or deployment support. Scenario and chat state reset on refresh. The harness provides structured explanations, not independently verified financial advice or a complete institutional risk model.

## Smallest next step for a Meta hackathon demo

Configure one accessible Llama model endpoint, run the same falling-yields question and broad risk-off scenario through it, inspect the captured context and evidence references, and rehearse a short Overview → Scenario Analysis → Metis AI walkthrough. This turns the existing deterministic workflow into a live reasoning demonstration without adding infrastructure.
