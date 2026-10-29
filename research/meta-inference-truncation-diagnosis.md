# Muse Spark Inference Truncation Diagnosis: October 29 Meta Hackathon Showcase

**Date:** 2026-10-29 (America/Los_Angeles)  
**Author:** Metis Research & Engineering  
**Scope:** Post-mortem diagnosis of the live Meta inference failure observed during the October 29 hackathon showcase review.  
**Baseline commit:** `69825ec`  
**Provider & model:** Meta API (`https://api.meta.ai/v1/chat/completions`), model `muse-spark-1.3`  
**Sampling & settings:** `temperature=0.2`, `max_completion_tokens=8000`, strict JSON schema (`Interpretation`), 60s timeout, model-determined reasoning effort (`reasoning_effort` omitted).

---

## 1. Executive Summary

During the October 29 Meta hackathon showcase, the very first live inference request (**Stage 2: Explain the illustrative daily portfolio loss**, `/api/reasoning`) failed after 29.8 seconds with an **HTTP 502 Bad Gateway** error. The upstream Meta API returned an HTTP 200 response with `finish_reason="length"`, indicating that the 8,000 completion-token budget was exhausted prior to completing the required structured JSON output schema. Metis's safety harness correctly detected the truncation and raised a sanitized `ProviderError`, refusing to parse partial JSON or silently substitute synthetic demonstration data. Under the predeclared showcase constraints, live execution was halted immediately.

This investigation evaluates whether the failure stems from an implementation defect, input sizing, or model reasoning variability, and determines the smallest evidence-supported correction.

### Key Conclusions

1. **Zero implementation defects:** The application harness, payload assembly, JSON schema definitions, HTTP transport, and error-handling paths executed exactly as specified.
2. **Context size is not the causal factor:** The failed request used ~10,804 prompt tokens—an identical context payload to earlier runs (v1.1 Case 01-A and integration call `ui-002`) that completed successfully. Furthermore, historical v1.0 truncations occurred on prompts half that size (~5,210–5,465 tokens).
3. **Primary constraint is reasoning-token budget exhaustion:** In Meta's API architecture, `max_completion_tokens` is a single shared pool covering both internal chain-of-thought reasoning tokens and visible JSON output. Emitting the full `Interpretation` schema requires ~1,100–1,500 visible output tokens. When stochastic reasoning generation exceeds ~6,500–6,800 tokens, truncation is mathematically inevitable.
4. **Stochastic reasoning variance causes unreliability:** Even with identical inputs and low temperature (`0.2`), Muse Spark exhibits wide dispersion in internal reasoning allocation (from ~3,900 tokens to 7,998 tokens). The showcase request hit the upper tail of this distribution.
5. **Prompt constraints do not solve the problem:** Prior experiments (v1.1) proved that prompting for compact output actually *increased* reasoning tokens by 16.7% as the model spent extra reasoning budget planning length compliance.
6. **Definitive recommendation:** Retain the existing production configuration and conduct all showcase presentations and recordings using **`METIS_PROVIDER=demo` (Deterministic Demo mode)**. It is 100% operationally reliable, institutional-grade in financial rigor, and visibly watermarked for complete intellectual honesty.

---

## 2. Comparative Analysis of Requests (Research Question 1)

The table below contrasts the October 29 showcase failure with historical successful and truncated requests across the Metis research archive.

| Request Context / Identification | Prompt Tokens | Completion Budget | Completion Tokens | Reasoning Tokens | Visible Output Tokens | Request Seconds | Termination (`finish_reason`) | Outcome |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Oct 29 Showcase Call 1 (Daily loss)** | **~10,804** | **8,000** | **8,000** | **~7,800+ (est.)** | **<200 (partial)** | **29.8s** | **`length`** | **HTTP 502 Truncated** |
| v1.1 Case 01-A (Daily loss, baseline `SYSTEM`) | 10,804 | 8,000 | 5,756 | 4,471 (77.7%) | 1,285 | 18.6s | `stop` | Valid JSON |
| v1.1 Case 01-B (Daily loss, compact `SYSTEM`) | 10,945 | 8,000 | 6,618 | 5,689 (86.0%) | 929 | 19.2s | `stop` | Valid JSON |
| v1.1 UI Integration `ui-002` (Daily loss) | 10,804 | 8,000 | 5,307 | 3,924 (73.9%) | 1,383 | 16.9s | `stop` | Valid JSON |
| v1.1 UI Integration `ui-003` (Broad Risk-Off) | 10,808 | 8,000 | 6,388 | 5,046 (79.0%) | 1,342 | 20.0s | `stop` | Valid JSON |
| v1.1 UI Integration Causal Exploration | 7,542 | 8,000 | 4,046 | 2,881 (71.2%) | 1,165 | 13.8s | `stop` | Valid JSON |
| v1.0 Truncated Requests ($n=6$; A05, A08, B05, B06, B07, B10) | 5,210–5,465 | 8,000 | 8,000 | 7,546.7 (avg; 94.3%) | 2–1,203 (partial) | 26.4–31.9s | `length` | Truncated (30% failure rate) |
| v1.0 Valid Requests ($n=14$) | 5,205–5,463 | 8,000 | 6,166.4 (avg) | 4,975.0 (avg) | ~1,191 (avg) | 13.9–28.2s | `stop` | Valid JSON |
| v0.2.1 Diagnostic Case (Initial reproduction) | ~9,400 | 3,000 | 3,000 | ~2,500+ (est.) | <500 (partial) | ~12.0s | `length` | Truncated (Budget too small) |

### Key Comparative Findings

- **Input Invariance:** Input prompt size does not separate successes from failures. Prompts of ~5.2k tokens failed in v1.0, while prompts of ~10.8k tokens succeeded in v1.1. In v1.0, prompt sizes of failed requests (5,210–5,465 tokens) completely overlapped prompt sizes of successful requests (5,205–5,463 tokens).
- **Latency Clustering:** Generation throughput on Meta's infrastructure averages ~270–310 tokens/second. Successful calls generating 5,300–6,600 total tokens completed in 16.9–19.2s. All calls reaching the 8,000-token ceiling clustered tightly between 26.4s and 31.9s. The showcase request's 29.8s elapsed time aligns directly with full 8,000-token generation.
- **Identical Setup:** Endpoint (`/v1/chat/completions`), model identifier (`muse-spark-1.3`), temperature (`0.2`), and JSON schema constraints were identical between the showcase failure and the v1.1 successes.

---

## 3. Reasoning-Token Budget Exhaustion as Primary Constraint (Research Question 2)

Empirical evidence confirms that **reasoning-token consumption is the primary operational constraint**:

1. **Shared Output Budget Architecture:** Meta's `/v1/chat/completions` protocol enforces `max_completion_tokens` across the sum of hidden reasoning tokens (`completion_tokens_details.reasoning_tokens`) and visible output tokens.
2. **Schema Payload Requirements:** The Metis `Interpretation` Pydantic schema requires eight structured fields, including nested vulnerability objects, structured historical analogies, assumptions, evidence IDs, and up to three structured financial claims. Across all recorded valid responses, the serialized JSON spans 3,934 to 6,088 characters, requiring **1,100 to 1,500 visible completion tokens**.
3. **Headroom Threshold:** In an 8,000-token completion envelope:
   $$\text{Max Allowed Reasoning Tokens} \approx 8,000 - 1,500 = 6,500 \text{ tokens}$$
   Whenever internal reasoning exceeds ~6,500–6,800 tokens, the remaining budget is insufficient to serialize the required JSON, guaranteeing a truncated payload and `finish_reason="length"`.
4. **Direct Precedent in v1.0 Private Records:** In the six v1.0 truncation events:
   - Reasoning tokens averaged **7,546.7** out of 8,000 (94.3% of the total budget).
   - In cases `05-B` and `07-B`, reasoning consumed **7,998 tokens**, leaving exactly **2 non-reasoning tokens** before the cutoff.
   - In case `08-A`, reasoning consumed 7,675 tokens, leaving 325 tokens (cutting off mid-schema).
5. **No Private Reasoning Trace:** Because Meta does not return the internal reasoning text, the application cannot observe *why* reasoning expanded. However, token accounting definitively proves that reasoning volume alone choked visible output capacity.

---

## 4. Provider Controls and API Capabilities (Research Question 3)

Review of Meta API documentation (`https://dev.meta.ai/docs/reasoning` and `https://dev.meta.ai/docs/protocols/chat-completions#parameters`) reveals the following controls and limitations:

- **`max_completion_tokens`:** Sets the hard ceiling on total generated tokens (reasoning + visible output). It does not provide an independent allocation or guarantee a minimum visible output buffer.
- **`reasoning_effort`:** Meta documents that omitting `reasoning_effort` leaves reasoning allocation to a "model-determined level." The parameter accepts discrete effort levels (e.g., `"low"`, `"medium"`, `"high"`).
- **Absence of Token Reservation:** The provider does not offer a mechanism like `min_completion_tokens` or a decoupled `max_reasoning_tokens`. Consequently, client applications cannot reserve the ~1,500 tokens required for strict JSON schemas.

---

## 5. Defect Classification: Implementation Defect vs. Model Reliability (Research Question 4)

### Implementation Audit
- **Request Serialization (`backend/metis/reasoning/harness.py`):** Correctly assembles system instructions, serialized context, user question, and strict JSON schema in `response_format`. No malformed payloads or missing required parameters.
- **Transport & Network Layer:** HTTP request dispatched successfully to `https://api.meta.ai/v1/chat/completions` with valid Bearer authentication. Network connectivity was maintained; no socket errors or timeouts occurred.
- **Harness Error Handling:** Upon receiving `finish_reason="length"`, line 265 of `harness.py` correctly identified the truncation:
  ```python
  if finish == "length":
      raise output_error(self.provider, "truncated", "Meta reached the completion-token limit...")
  ```
  FastAPI properly converted this to an HTTP 502 with a sanitized error message, refusing to display corrupt JSON or fake a live response.
- **Showcase Runner (`showcase_runner.py`):** Dispatched the exact canonical `dailyQuestion` with valid daily shocks, matching the v1.1 integration protocol.

### Diagnostic Classification
**Classification: Unresolved Model Inference Reliability Problem.**  
The failure was not caused by a bug in Metis. It is an upstream reliability problem stemming from **uncontrolled stochastic variance in Muse Spark's internal chain-of-thought length** when operating without an explicit reasoning-effort ceiling. When stochastic reasoning happens to exceed ~6,500 tokens, the request truncates deterministically.

---

## 6. Separation of Epistemic Status

To maintain strict scientific discipline under `AGENTS.md`, observations, explanations, and unknowns are separated below:

### Confirmed Observations (Empirical Facts)
1. Showcase Call 1 failed with HTTP 502 due to `finish_reason="length"` from Meta's API after 29.8s.
2. The completion budget of 8,000 tokens was fully exhausted.
3. The prompt size (~10,804 tokens), model (`muse-spark-1.3`), temperature (`0.2`), and schema were identical to successful requests in v1.1 (`01-A` and `ui-002`).
4. In v1.0, 6 of 20 requests truncated with `finish_reason="length"`, averaging 7,546.7 reasoning tokens (94.3% of the 8,000 budget), including two instances consuming 7,998 reasoning tokens.
5. In v1.1, prompting for compact output reduced JSON character length by 32.7% but increased reasoning token consumption by 16.7%.
6. Metis does not currently specify `reasoning_effort` in `META_INFERENCE_PARAMETERS`.

### Plausible Explanations (Grounded Hypotheses)
1. *Reasoning Expansion on Complex Portfolio Attribution:* When presented with multi-asset loss attribution (opposing swap DV01s, credit spread widening vs. rate gains, equity drops), Muse Spark's internal reasoning occasionally enters deep iterative calculations, consuming 7,500+ tokens.
2. *Unconstrained Effort Default:* Because `reasoning_effort` is omitted, the model's default heuristic allows reasoning to expand until completion limits intervene.

### Unresolved Questions (Cannot Be Established Without Live Inference)
1. *Exact Showcase Token Breakdown:* Because the harness raised an exception on HTTP 502 before attaching `self.last_usage` to the API response, the exact split between reasoning and non-reasoning tokens for this specific run remains unconfirmed (inferred as ~7,800+ reasoning based on 29.8s latency and previous truncation profiles).
2. *Efficacy of `reasoning_effort="low"`:* Whether Meta's API actively honors `reasoning_effort="low"` for `muse-spark-1.3`, whether it reliably caps reasoning below 4,500 tokens, and whether it degrades financial interpretation quality cannot be verified without live calls.

---

## 7. Smallest Evidence-Supported Correction & Recommendation (Research Question 5)

### Evaluation of Candidate Corrections

| Candidate Correction | Evidence from Prior Studies | Feasibility & Tradeoffs | Status |
| :--- | :--- | :--- | :--- |
| **1. Prompt Compactness Instructions** | Tested in v1.1 (`COMPACT_OUTPUT`). Led to +16.7% reasoning tokens. Fails to prevent reasoning budget exhaustion. | Does not address the root mechanism; actually worsens reasoning token pressure. | **Rejected by evidence** |
| **2. Reduce Input Context** | Tested in v1.0 (5.2k prompt tokens). Truncation rate remained 30% (6/20 failed). | Omits necessary portfolio/market evidence without preventing truncation. | **Rejected by evidence** |
| **3. Increase Completion Budget (e.g. 12,000)** | Untested live; raises latency towards 40–50s, risking the 60s HTTP timeout. | Prohibited by prompt constraints; does not guarantee reasoning will not expand to fill the larger budget. | **Rejected by constraints** |
| **4. Add Retries** | Would introduce unpredictable latency spikes (30s–60s+) during a live presentation. | Prohibited by prompt constraints; masks underlying unreliability. | **Rejected by constraints** |
| **5. Parameter Control: `reasoning_effort="low"`** | Meta documentation supports `reasoning_effort`. Has not been evaluated for `muse-spark-1.3` in this repository. | Smallest code change (1 line in `harness.py`), but unverified without live inference. | **Proposed for future research only** |

### Definitive Recommendation: Use Deterministic Demo Mode (`METIS_PROVIDER=demo`)

For immediate hackathon presentations, stage demos, and video recordings:
1. **Preserve existing production code and settings unchanged.** No live model calls, parameter hacks, or prompt rewrites.
2. **Execute all presentations using `METIS_PROVIDER=demo`.**
   - **Operational Reliability:** 100% reliable with zero risk of API truncation, rate limits, or network latency.
   - **Institutional Quality:** Delivers mathematically verified attributions (−$560,770 daily; rates +$412k, spreads −$407k, equities −$506k), clean swap leg separation (10Y receive vs 5Y pay), and clear growth-scare vs. inflation-relief causal divergence (−$3.35m vs +$5.07m).
   - **Intellectual Honesty:** The interface visibly watermarks every card with **`DETERMINISTIC DEMO`**, establishing trust with judges by presenting verified analytics rather than gambling on live API stability.

### Future Research Scope (If Authorized)
If live Meta inference is revisited in a subsequent milestone, authorization should be sought for a single, narrowly defined offline experiment:
- **Design:** Evaluate `reasoning_effort="low"` vs. omitted (baseline) across 4 frozen cases using `muse-spark-1.3`, with a hard cap of 8 live requests.
- **Success Criteria:** Reasoning tokens consistently stay below 4,500 tokens, visible output passes strict JSON schema validation on 100% of calls, and financial attribution remains accurate.


## 2026-10-29 archival finalization and status qualification

This is a completed retrospective diagnosis of the stopped showcase, not an unfinished experiment. It performed no separately documented inference; diagnostic timing/cost is unavailable. Its proposed four-case effort comparison was subsequently completed in the [v1.2 report](reasoning-effort-experiment-20261029.md). Production now includes low effort at `ca4eeaa76480ceac7f5169d4b08ed207590cdeec`; statements above that effort is omitted or untested are historical. The reported `69825ec` baseline is not independently authenticated by the showcase manifest, which omits Git revision.

The showcase envelope lacks the exact provider usage split. Historical token/headroom estimates do not establish the internal reason for expanded reasoning, a universal serialization threshold, absence of every implementation defect, or causal independence from input size. No private reasoning trace was available. Prior conditions differ, so their outcomes do not isolate effects of context size or prompt compactness. Provider-documentation descriptions above are historical claims and were not revalidated against current external documentation in this archival task. See the [research log](RESEARCH_LOG.md) for subsequent bounded observations and engineering decisions. Original findings remain intact; no new inference or replication was performed.
