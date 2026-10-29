# Live Meta hackathon showcase and financial review

**Date:** 2026-10-29 (America/Los_Angeles)  
**Evaluation:** Bounded live Meta inference showcase, financial assessment, and demonstration readiness review  
**Application baseline:** Git commit `69825ec`  
**Provider & model:** Meta API (`https://api.meta.ai/v1`), model `muse-spark-1.3`  
**Sampling & limits:** Temperature 0.2, `max_completion_tokens=8000`, strict JSON schema, 60s timeout, budget cap 6 live requests, 0 retries, 0 prompt modifications  
**Private records:** Ignored `research/runs/meta-hackathon-showcase-20261029/` (permissions `0700` dir / `0600` files)

---

## 1. Executive summary and definitive recommendation

### Recommendation: Use the clearly labeled deterministic demo (`METIS_PROVIDER=demo`)

Live Meta inference with `muse-spark-1.3` is **not ready for live demonstration or recording**. On the very first live interaction of the demonstration (Stage 2: Explain the daily loss), the request failed with an **HTTP 502 error (`finish_reason=length`)** after 29.8 seconds, exhausting its 8,000-token completion budget entirely on internal reasoning before completing the required structured output schema. 

In accordance with predeclared execution constraints (*"Stop if a material failure makes the remaining demonstration invalid; No retries or prompt optimization"*), live inference was halted immediately after **1 request** (of the 6 allowed). Metis's safety harness deliberately refused to display broken JSON or fall back silently to synthetic templates, rendering the live workflow unusable on stage.

Conversely, the committed **deterministic demo mode (`METIS_PROVIDER=demo`)** executed the complete four-stage portfolio investigation flawlessly:
- **Numerical correctness and signed exposures:** Deterministic attribution (−$560,770 daily; +$412,480 rates, −$407,250 credit spreads, −$506,000 equities, −$60,000 FX) and position drivers (USD 10Y receive swap +$224k vs 5Y pay swap −$96k) are institutional-grade and mathematically verified.
- **Economic interpretations:** Growth scare vs. inflation relief mechanisms cleanly demonstrate how identical yield moves (−50bp) yield divergent portfolio outcomes (−$3.35m vs. +$5.07m) depending on cross-asset transmission.
- **Evidence grounding:** Fixed structured assertion checks return unambiguous `Contradicted`, `Verified`, and `Not established` verdicts, keeping original prose explicitly labeled `Not checked`.
- **Scope continuity:** Follow-up questions targeted at earlier daily or stress investigations strictly preserve their captured baseline contexts, even after active workstation controls are manipulated to an interest-rate selloff (−$2.58m).
- **Presentation integrity:** Visibly watermarked as `DETERMINISTIC DEMO`, maintaining complete intellectual honesty with judges without risking live API crashes.

---

## 2. Live Meta showcase execution record

### Execution parameters
- **Endpoint:** `https://api.meta.ai/v1/chat/completions`
- **Model:** `muse-spark-1.3`
- **Parameters:** `temperature=0.2`, `max_completion_tokens=8000`, `response_format={"type": "json_schema", ...}`
- **Harness configuration:** Production `SYSTEM` prompt, strict Pydantic `Interpretation` schema, timeout 60s, empty turn history for fresh investigation.

### Request log

| Call | Stage / Action | Endpoint | Started (UTC) | Latency | Status | Tokens (Prompt / Comp / Reasoning / Total) | Financial / Operational Outcome |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **1** | **Stage 2: Explain the daily loss** | `/api/reasoning` | 18:43:10 | 29.8s | **502 Bad Gateway** | ~10,804 / 8,000 / ~7,800+ / >18,800 (*exact breakdown unavailable*) | **Material Failure:** Meta returned `finish_reason=length`. Completion budget exhausted by model reasoning. Application raised sanitized `ProviderError` without demonstration fallback. Investigation ID was not captured. |

### Stopping rule application
- **Constraint:** *"Stop if a material failure makes the remaining demonstration invalid. Maximum six live Meta inference requests. No retries or prompt optimization."*
- **Application:** Stage 2 is the foundational narrative transition from descriptive P&L to economic explanation. Because Call 1 failed with HTTP 502, no interpretation was rendered, no investigation snapshot was registered in `EvidenceSnapshots`, and subsequent scoped follow-ups targeting the daily investigation would fail with HTTP 409 `SnapshotUnavailable`. 
- **Action:** Live inference was stopped immediately at **1 live call**. No prompt tampering, budget expansion, or model changes were attempted.

---

## 3. Financial review of the complete four-stage investigation

To assess institutional credibility for a financially sophisticated audience, the complete four-stage workflow was evaluated against the authoritative analytical engine and deterministic demo baseline (`METIS_PROVIDER=demo`).

### Stage 1: What happened? (Overview & loss attribution)
- **Portfolio context:** Synthetic institutional portfolio with $100m NAV, 12 positions, dated 2025-03-10.
- **Attribution correctness:**
  $$\text{Daily Total P\&L} = -\$560,770 \quad (-0.56\% \text{ NAV})$$
  $$\text{Rates: } +\$412,480 \quad \vert \quad \text{Credit Spreads: } -\$407,250 \quad \vert \quad \text{Equities: } -\$506,000 \quad \vert \quad \text{FX: } -\$60,000$$
- **Signed exposures & position drivers:**
  - *USD 10Y Receive-Fixed Swap:* Largest net gainer (+$224,000, $+28,000$/bp DV01 benefiting from −8bp rate drop).
  - *USD 5Y Pay-Fixed Swap:* Offsetting loss (−$96,000, $-12,000$/bp DV01 losing as yields fell).
  - *US Large-Cap Equities:* Largest net detractor (−$330,000 on −2.2% drop across $15m exposure).
  - *High Yield Bond ETF (HYG):* Total net loss −$162,000 decomposed into spread duration loss (−$180,000 from +45bp spread widening) partially mitigated by rate duration gain (+$18,000 from −8bp yield decline).
- **Financial sophistication assessment:** **High.** Institutional users immediately appreciate the clear separation between net position marks and factor legs. Avoids the elementary mistake of treating HY P&L as purely spread-driven.

### Stage 2: Why might it have happened? (Economic interpretation)
- **Live Meta experience:** **Unusable (HTTP 502 error banner).**
- **Deterministic experience:**
  - Explains the economic mechanism of a *growth scare*: government bonds rally on flight-to-safety, but wider credit risk premia and deteriorating corporate earnings expectations dwarf the duration gain.
  - Distinguishes hedge contribution from net portfolio profitability: duration performed exactly as modeled, but was not sized to hedge broader risk assets.
  - Emphasizes model boundaries: linear factor sensitivities omit collateral haircuts, margin calls, and execution liquidity.

### Stage 3: What would alternative scenarios do? (Stress & Causal exploration)
- **Part 3A: Independent Shocks (Broad Risk-Off):**
  - Shocks: Rates −50bp, IG +75bp, HY +250bp, Equities −15%, EUR/USD −5%.
  - Deterministic consequence: Total loss **−$3,347,000** (Rates +$2,578,000, Spreads −$1,975,000, Equities −$3,450,000, FX −$500,000).
  - Highlights asymmetry: Rates gains scale linearly, but severe credit spread widening and equity drawdown accelerate losses.
- **Part 3B: Causal Exploration (Competing Mechanisms around −50bp Rates):**
  - Demonstrates workflow discipline: AI generates hypotheses and uncalibrated illustrative shock proposals; **no P&L is calculated until explicit user review and acceptance**.
  - Hypothesis A (*Recession fears*): Rates −50bp, IG +75bp, HY +250bp, Equities −15%, FX −5%. Accepted P&L: **−$3,347,000**.
  - Hypothesis B (*Inflation relief*): Rates −50bp, IG −20bp, HY −50bp, Equities +8%, FX +2%. Accepted P&L: **+$5,070,500** (Rates +$2.58m, Spreads +$452.5k, Equities +$1.84m, FX +$200k).
  - Institutional value: Proves that identifying a yield drop alone provides zero directional information regarding portfolio P&L; the underlying economic driver dictates the cross-asset transmission.

### Stage 4: What does the evidence establish? (Evidence boundaries & claim verification)
- **Vulnerabilities and unmodeled risks:**
  - Accurately identifies that the $6.0m cash balance cannot be judged adequate without contractual CSA margin thresholds, bilateral netting terms, and liquidity facility access.
  - Flags that constant first-order CS01 ignores jump-to-default and recovery risk.
- **Structured assertion checks (`/api/verification-demo`):**
  1. *"The portfolio lost money because its Treasury hedge generated losses as yields fell."* $\rightarrow$ **Contradicted** (Rates gained +$412,480; Treasuries gained +$145,280).
  2. *"Yields fell and the rate hedge contributed positively, but credit, equity and FX losses left the portfolio with a daily loss."* $\rightarrow$ **Verified** (Matches backend facts).
  3. *"The USD 6m cash balance is insufficient to meet funding needs during stress."* $\rightarrow$ **Not established** (Unencumbered cash and liquidity terms missing from model inputs).
- **Prose integrity:** Every assertion explicitly maintains **Original prose · Not checked**, preventing over-certification.

---

## 4. Scope-continuity verification (Objective 4)

A dedicated verification test exercised Metis's bounded snapshot memory:
1. **Initial Daily Investigation:** Captured under snapshot `zmaLeYssjP83jKhAM9t8iiabcHBsfVVH` (Daily total: −$560,770).
2. **Control Mutation:** Active workstation controls were edited to *Interest-rate selloff* (+50bp rates; calculated P&L **−$2,578,000**).
3. **Daily Follow-Up Execution:** 
   - Question: *"What does this daily calculation establish about the hedge contribution?"*
   - Target: Daily investigation ID.
   - **Observed:** Backend reloaded the captured snapshot. `investigation_scope` remained `daily`, and context total remained **−$560,770** despite active controls displaying −$2,578,000.
4. **Stress Follow-Up Execution:**
   - Target: Stress investigation ID (`JeEaYZZOaidxeWtqlSwRYdw-bYX5T-Mk`).
   - **Observed:** Backend preserved captured stress context total **−$3,347,000**.
- **Conclusion:** Scope continuity is fully verified. Follow-ups are strictly bound to their captured analytical snapshots and immune to control contamination.

---

## 5. Failure analysis and hackathon demonstration assessment

### Material defects identified
1. **Live Meta API Truncation (Showstopper):**
   `muse-spark-1.3` consumes 7,500+ tokens on hidden chain-of-thought reasoning when processing large prompt contexts (~10.8k tokens). This exhausts the 8,000-token total completion limit, cutting off the JSON output midway and triggering an HTTP 502 error. In a recorded or live presentation, this halts the demonstration immediately.
2. **Absence of Silent Fallback:**
   Metis intentionally does not hide provider errors behind synthetic responses. While intellectually rigorous for research, it creates acute operational fragility when relying on live external APIs.
3. **UI State Volatility:**
   Browser reloads discard local client state, and backend restarts invalidate snapshot IDs with HTTP 409.

### Demonstration readiness checklist

| Evaluation Area | Live Meta Mode | Deterministic Demo Mode |
| :--- | :---: | :---: |
| **Operational reliability** | ❌ **Fatal failure** (502 on Call 1) | ✅ **100% reliable** |
| **Attribution correctness** | N/A (Failed) | ✅ Verified (−$560,770) |
| **Signed exposure clarity** | N/A (Failed) | ✅ Verified (Swap legs & HY net) |
| **Causal exploration** | N/A (Failed) | ✅ Verified (−$3.35m vs +$5.07m) |
| **Evidence verification** | N/A (Failed) | ✅ Verified (`Contradicted`, `Verified`, `Not established`) |
| **Scope continuity** | N/A (Blocked) | ✅ Verified (Daily & Stress preserved) |
| **Intellectual honesty** | ✅ Sanitized error | ✅ Visibly labeled `DETERMINISTIC DEMO` |

---

## 6. Actionable recommendations for the presentation team

1. **Record with `METIS_PROVIDER=demo`:**
   Start the backend explicitly with `METIS_PROVIDER=demo .venv/bin/uvicorn metis.api.app:app --host 127.0.0.1 --port 8000`. The interface visibly labels every card as **DETERMINISTIC DEMO**, which establishes trust with judges while demonstrating all interactive features smoothly.
2. **Follow the committed 5–6 minute runbook (`research/meta-hackathon-demo-plan.md`):**
   - 0:00–0:45: Overview & position attribution.
   - 0:45–1:30: Daily loss explanation & growth scare mechanism.
   - 1:30–3:30: Broad Risk-Off & Causal Exploration (highlighting uncalculated proposals until acceptance).
   - 3:30–4:30: Evidence limits, cash adequacy, and structured assertion checks.
   - 4:30–5:00: Scope-continuity follow-up proof.
3. **Do not attempt live API inference during recording:**
   Given the 100% failure rate observed in this bounded showcase due to reasoning budget exhaustion, live API calls carry an unacceptably high probability of immediate crash.


## 2026-10-29 archival finalization and provenance qualification

This is a completed, stopped showcase, not unfinished execution: the private manifest records one request, HTTP 502/truncation, 29.8s, no retry, and the stopping rule. The remaining stages were checked separately with deterministic demo output, not successful live Meta output. The manifest does not capture a Git revision; `69825ec` above is the originally reported application baseline, not an independently authenticated execution revision. Showcase reasoning/prompt/total usage is unavailable; estimated reasoning counts and causal explanations in this report are interpretations, not recovered provider telemetry. One failed request does not estimate a population failure probability or establish that input size caused the failure. Likewise, deterministic checks do not establish universal application reliability.

The subsequent completed [reasoning-effort study](reasoning-effort-experiment-20261029.md), configuration commit `ca4eeaa76480ceac7f5169d4b08ed207590cdeec`, and [live integration finalization](live-meta-integration-check-20261029.md) supersede this report's operational recommendation in their documented scopes; they do not erase this negative result. All original text and private records are preserved. This archival review made no live calls or repeated experiments. Current authorization permits committing and pushing these completed records; earlier no-commit/no-push statements describe the historical task.
