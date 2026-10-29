# Metis: investigate a $560,770 loss

**2026-10-29 · 5–6 minute script · current application at `69825ec`**

Opening line — **suggested presenter narration:** “Yields fell and the portfolio still lost $560,770. Metis separates the calculation, the economic explanation and the evidence we still need.”

## Setup and truth labels

Use the existing installed environment; see [README setup](../README.md#run-locally). Start these in separate terminals from the indicated directories:

```sh
# Repository root; explicitly overrides a live provider configured in .env.
PYTHONPATH=backend METIS_PROVIDER=demo .venv/bin/uvicorn metis.api.app:app --host 127.0.0.1 --port 8000
```

```sh
# frontend/
npm run dev -- --port 5173 --strictPort
```

Open `http://127.0.0.1:5173`. Both ports must be available; do not connect to an unidentified existing backend. Reload once before starting for a fresh browser conversation, then keep the backend running. The synthetic snapshot is **2025-03-10**, NAV **$100m**, 12 positions; it is not today's market.

- **Calculation:** backend deterministic result under supplied inputs; not a model's arithmetic or a forecast.
- **Demo text:** fixed application templates, visibly **DETERMINISTIC DEMO**; not actual model output.
- **Narration:** suggested presenter language below, not an application quotation.
- **Actual model output:** only a real response bearing its live provider/model badge. **None is generated or quoted in this script.** Prior Muse Spark integration is documented in the [live-workflow report](inference-reliability.md); it is not a Llama run or a new demonstration result. A fresh Meta inference demonstration requires separate authorization. Do not relabel templates as live AI.

## 1. What happened? — 45 seconds

**Actions:** select **Overview**. Point to **Daily P&L**, **Daily factor contributions**, and **Principal position drivers**. Expand **Inspect position contributions and signed DV01** only if asked.

**Expected calculations:** total **−$560,770**; rates **+$412,480**, credit spreads **−$407,250**, equities **−$506,000**, FX **−$60,000**. Largest net loss: **US large-cap equities −$330,000**; largest net gain: **USD 10Y receive-fixed swap +$224,000**.

**Narration:** “Equity and spread losses outweighed the rates gain. These are separate factor contributions; net credit-position P&L also includes a rates leg. A positive contribution does not establish that a hedge met its mandate.”

## 2. Why might it have happened? — 45 seconds

**Actions:** click **2 · Explain the daily loss** on Overview. Check **DETERMINISTIC DEMO** and **Answer scope: Daily snapshot · 2025-03-10**. Expand **Economic interpretation · why the risks interact**.

**Expected:** the captured assumptions are rates **−8bp**, IG **+18bp**, HY **+45bp**, equities **−2.2%**, EUR/USD **−0.6%**. Captured calculations remain the stage1 amounts. The fixed demo explanation discusses weaker growth, Treasury support and pressured risk assets; it is a template, not a newly discovered cause.

**Narration:** “A growth scare is one plausible explanation for yields falling while spreads widen and equities weaken. Benign inflation relief could produce different cross-asset moves. Neither the P&L nor a historical analogy identifies the actual cause.”

## 3. What would alternative scenarios do? — 2 minutes

**Actions:** select **Scenario Analysis → Independent Shocks → Broad risk-off**. Wait for recalculation. Confirm the Broad row below; click **Interpret this scenario with Metis**. Check the new **Captured stress** scope and its own calculations; the earlier daily answer is preserved. This explicit action starts a new investigation.

Then select **Scenario Analysis → Causal Exploration**. Set **Economic hypothesis A = Recession fears**, **Economic hypothesis B = Inflation relief**, **Shared government-yield move · bp = −50**. Click **Generate competing mechanisms**. These are fixed demo proposals; **no A/B P&L is calculated yet**. Inspect their assumptions, leave them unchanged, then click **Accept reviewed shocks & calculate both**. Scroll to each **Calculated consequences · accepted assumptions** block.

| Calculation | Rates / IG / HY (bp); equities / EUR/USD (%) | Rates P&L | Spread P&L | Equity P&L | FX P&L | Total P&L |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Broad risk-off / demo A | −50 / +75 / +250; −15 / −5 | +$2,578,000 | −$1,975,000 | −$3,450,000 | −$500,000 | **−$3,347,000** |
| Demo B: inflation relief | −50 / −20 / −50; +8 / +2 | +$2,578,000 | +$452,500 | +$1,840,000 | +$200,000 | **+$5,070,500** |

**Narration:** “The same assumed 50bp yield decline supports the same rates contribution. Different credit, equity and FX assumptions change the overall result. These magnitudes are uncalibrated inputs; the engine calculates consequences after review. It does not establish which hypothesis is true.”

These are **current demo-template** amounts. The earlier live study's −$29,500 / +$3,948,500 examples used different shocks and must not be substituted here. Avoid editing assumptions during the timed path: edits clear both results and require acceptance again.

## 4. What does the evidence establish? — 1 minute

**Actions:** click the top trail's **4 · What deserves investigation?** It returns to the latest stress answer's findings; causal cards do not create a new reasoning investigation. Open the first funding/counterparty concern's full text if needed and **Inspect calculations ↓**. Cash is **$6m**; the guide requests CSA/netting terms, collateral, margin requirements and available funding.

Scroll to the top of **Metis AI Reasoning** and expand **Structured assertion checks · three reproducible examples**. These are fixed analyst-authored demonstrations, not errors discovered in the current answer.

**Expected verdicts, in order:** erroneous hedge-loss premises **Contradicted**; rates-gain/portfolio-loss premises **Verified**; $6m funding-insufficiency assertion **Not established**. Every original sentence remains **Original prose · Not checked**. Do not confuse these fixed examples with an answer's separate selected structured-assertion checks.

**Closing narration:** “We can establish modeled losses and offsets. We cannot infer cash adequacy, default loss or an optimal hedge from marks and sensitivities alone. The useful next request is contractual margin and liquidity evidence. Metis checks mapped assertions; it does not certify the narrative or rank unmeasured losses.”

## Optional 30-second scope-continuity proof

After the stress investigation exists, choose **Scenario Analysis → Interest-rate selloff** in **Independent Shocks**: expected **−$2,578,000**, entirely rates, other factors zero. Return through the left **Metis AI Reasoning** navigation; do not start a new investigation. In **Continue captured investigation**, select the original daily investigation. Confirm **Follow-up scope: Daily snapshot**, type **“What does this daily calculation establish about the hedge contribution?”**, and click **Ask follow-up**. Its captured total remains **−$560,770** despite different current controls. Show the prior stress answer still has **−$3,347,000**. Do not promise novel or question-complete demo prose: the demonstration proves scope continuity, not language understanding.

## Blockers, limits and checks

- **Live Meta showcase:** this reproducible path contains no actual model inference. Existing Meta support is documented, but current credentials/access and live availability were not tested here. Never promise exact live wording, claim counts or causal shocks. Historical truncation/timeouts and unsupported economic conclusions remain material risks; a live failure must stay visible without demo substitution. No fresh live request is authorized by this plan.
- **State:** browser reload loses conversations; backend restart or FIFO eviction after128 newer investigations invalidates references with409. Start an explicit new investigation if needed. Do not restart mid-script or claim persistence.
- **Financial boundary:** synthetic data, linear first-order model, no calibrated probabilities or quantified funding/default/liquidity losses. The completed meaning-alignment rules remain research-only. No trade recommendation or causal-identification claim is part of this demonstration.
- **Verification performed:** source-checked every action label; an offline `TestClient` pass with forced demo mode confirmed the displayed daily/preset/A/B totals, explicit stress capture, optional daily follow-up and three fixed verdicts. Four deterministic-template API requests, zero live calls/tokens; no responses saved. This is a current workflow checkpoint, not a new scientific experiment. No new browser rehearsal or timed usability measurement was performed for this documentation task.
- **Repository checks:**159 backend/research tests and20 frontend tests pass; production build passes. Existing Starlette/httpx deprecation and large-chunk warnings remain. [Scope audit](investigation-scope-audit.md) and [historical portfolio review](portfolio-investigation-review.md) retain dated qualifications. Production code and past experiment records are unchanged. Stop after documentation; no feature work or push.
