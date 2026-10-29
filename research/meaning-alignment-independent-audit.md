# Independent Scientific Audit: Metis Meaning-Alignment Experiment

**Audit Date:** 2026-10-29  
**Target:** Meaning-Alignment Experiment (`research/meaning-alignment.md`, `research/meaning_alignment.py`, `research/meaning-alignment-cases.json`, `research/meaning-alignment-results.json`)  
**Repository:** Metis Portfolio Risk System  
**Auditor:** Independent Scientific Audit  

---

## 1. Executive Summary & Verdict

This audit conducted an independent scientific review of the Metis meaning-alignment experiment documented on 2026-10-29. The evaluation examined the theoretical framing, experimental design, implementation code, recorded data across all 16 cases, regression test suites, and repository provenance.

### Core Verdict
The meaning-alignment experiment is **technically reproducible and deterministically audited**, but it **does not possess scientific validity as an evaluation of financial language understanding or meaning alignment**. The reported 7/8 error detection rate is an **in-sample artifact of hand-crafted case-to-rule overfitting**. The rule implementation consists of eight bespoke regular expressions tailored to match the specific 16 test sentences authored by the same analyst. The system exhibits virtually zero generalization to natural language paraphrasing, and its apparent "abstention on ambiguous statements" is an unhandled grammar fall-through rather than epistemic detection.

### Recommendation
**Retain research only.** Do not implement the rules, do not integrate them into the Metis verifier or production pipeline, and do not authorize further validation. The experiment serves strictly as an illustrative record documenting the extreme brittleness of rigid template-matching for financial prose.

---

## 2. Scientific Validity: Independence and Case Construction

### Circularity and Lack of Independence
The protocol (`research/meaning-alignment-protocol.md`) and report (`research/meaning-alignment.md`) note "procedural independence" on the grounds that expectations were drafted prior to rule implementation. However, substantive independence is entirely absent:
1. **Same-Author Coupling:** The same analyst authored the financial statements, expected dispositions, and regular expression rules with full visibility of the test set.
2. **Template-to-Case One-to-One Correspondence:** In `research/meaning_alignment.py`, the rules do not implement a general financial grammar or semantic ontology. Instead:
   - Line 33: One regex matching Cases 01, 02, 03, 04 (`In the scenario, (HY net|HY spread-only|portfolio rates|portfolio total) P&L is <AMOUNT>.`).
   - Line 44: One regex matching Cases 05, 06 (`In the daily snapshot, (EUR|USD) appreciation causes the short-EUR position's FX P&L of <AMOUNT> in the linear model.`).
   - Line 54: One regex matching Cases 07, 08 (`Available funding of <AMOUNT> covers the specified <AMOUNT> outflows for (the next day|all future horizons).`).
   - Line 65: One regex matching Cases 09, 10 (`The (specified issuer default scenario|expected issuer default) loss is <AMOUNT>.`).
   - Lines 76, 82, 88, 94: Four individual, bespoke regexes matching verbatim the exact phrasing of Cases 11, 12, 13, and 14 respectively.
   - Lines 99: Fallback returning `Uncheckable`, which catches Cases 15 and 16.
3. **Inflation of Detection Result (7/8):**
   The metric "flagged 7 of 8 intended errors" (87.5%) is scientifically meaningless. Seven errors (02, 04, 06, 08, 10, 11, 13) were explicitly scripted into the regexes to return `Mismatch` or `Not established`. The single "missed" error (15) was intentionally left out of the grammar as a negative demonstration. Any statement diverging from the rigid templates—including minor word order changes—falls into `Uncheckable`. The 7/8 figure measures author compliance with an author-defined test suite, not detector sensitivity.
4. **Superficial Integrity Checks:**
   In `research/test_meaning_alignment.py`, `test_frozen_record_integrity_and_independent_expectations` asserts independence by checking that the string `'meaning-alignment-cases'` does not appear in `meaning_alignment.py`. Banning the file name is cosmetic when the literal phrasing of each test case is hardcoded into the regex patterns.

---

## 3. Baseline Comparison: Assumed vs. Demonstrated Limitations

The experiment compares the regex candidate against two comparator lanes: production `FinancialClaim` checks and research prototype `EvidenceClaim` checks. The report frames existing verification as limited because it verifies cited numbers while missing statement attribution. This comparison contains fundamental methodological flaws:

1. **Category Error (Prose Parser vs. Structured Data Validator):**
   Metis's production verifier (`backend/metis/verification/claims.py`) was never designed to parse natural language strings. It validates structured metadata payloads extracted upstream. By design, the production verifier returns `original_wording_status: "Not checked"`. Benchmarking an end-to-end regex parser against a backend numeric validator on raw text creates an artificial baseline handicap.
2. **Existing Verification Already Catches the Underlying Financial Errors:**
   When structured claims faithful to the semantic assertions are provided (tested in `production_human_literal_diagnostic`), existing Metis verification detects the errors:
   - **Case 02:** When mapped to `metric="credit_pnl"` (spread P&L), production verification returns `Contradicted`.
   - **Case 04:** When mapped to `metric="total_pnl_usd"`, production verification returns `Contradicted`.
   - **Cases 11 & 13:** The prototype `evidence_grounding.py` already gates unproven concentration and causation, returning `Not established`.
   - **Cases 12 & 14:** The prototype correctly identifies conditional hypotheses (`Conditional hypothesis`).
3. **True Incremental Value of Candidate:**
   The only incremental mechanism demonstrated is slot extraction from eight rigid sentence frames, bypassing manual mapping for those eight frames. The underlying verification logic (checking arithmetic or flagging missing evidence) is identical to what Metis already implemented.

---

## 4. Case-by-Case Error Analysis (All 16 Cases)

| Case ID | Statement Text | Expected | Candidate Verdict | Actual Mechanism in `meaning_alignment.py` | Scientific Assessment |
|---|---|---|---|---|---|
| **01** | HY net P&L is -$872,500 | Supported | Scoped match | Slots `label='HY net'`, matches `e['hy_net']` | In-sample template match. |
| **02** | HY spread-only P&L is -$872,500 | Error | Mismatch | Slots `label='HY spread-only'`, mismatch with cited `hy_net` | In-sample template match. Production verifier catches this if mapped as credit P&L. |
| **03** | Portfolio rates P&L is +$2,578,000 | Supported | Scoped match | Slots `label='portfolio rates'`, matches `scenario_rates` | In-sample template match. |
| **04** | Portfolio total P&L is +$2,578,000 | Error | Mismatch | Slots `label='portfolio total'`, mismatch with cited `scenario_rates` | In-sample template match. Production verifier catches this if mapped as total P&L. |
| **05** | EUR appreciation causes short-EUR loss of -$60,000 in linear model | Supported | Scoped match | Matches regex 44; checks `currency=='EUR'` and linear shock signs | In-sample template match. Allows word "causes" solely because author included it in regex. |
| **06** | USD appreciation causes short-EUR loss of -$60,000 in linear model | Error | Mismatch | Matches regex 44; `currency=='USD'` triggers mismatch | In-sample template match on binary currency flag. |
| **07** | Funding of $1.9m covers $1.4m outflows for next day | Supported | Scoped match | Matches regex 54; checks `scope=='the next day'` and literal horizon string match | Rigid string comparison against `e['horizon']`. |
| **08** | Funding of $1.9m covers $1.4m outflows for all future horizons | Error | Not established | Matches regex 54; `scope!='the next day'` triggers `Not established` | Binary slot-filling check (`the next day` vs `all future horizons`). |
| **09** | Specified issuer default scenario loss is $4,160,000 | Supported | Scoped match | Matches regex 65; `scope=='specified issuer default scenario'` | Binary slot-filling check. |
| **10** | Expected issuer default loss is $4,160,000 | Error | Not established | Matches regex 65; `scope=='expected issuer default'` triggers `Not established` | Binary slot-filling check. |
| **11** | CS01 proves concentration exceeds limits | Error | Not established | Matches bespoke regex 76 verbatim; returns hardcoded `Not established` | Verbatim sentence trigger; zero semantic parsing. |
| **12** | If look-through reveals breach, CS01 could coexist... | Conditional | Conditional hypothesis | Matches bespoke regex 82 verbatim; returns hardcoded `Conditional hypothesis` | Verbatim sentence trigger. |
| **13** | Daily P&L proves forced liquidation caused moves | Error | Not established | Matches bespoke regex 88 verbatim; returns hardcoded `Not established` | Verbatim sentence trigger; zero causal parsing. |
| **14** | If funding pressure drove sales, P&L could be consistent... | Conditional | Conditional hypothesis | Matches bespoke regex 94 verbatim; returns hardcoded `Conditional hypothesis` | Verbatim sentence trigger. |
| **15** | Short-EUR book dropped $60,000 as greenback strengthened | Error | Uncheckable (Missed) | Falls through all regexes to line 99 fallback | **Critical vulnerability.** Illustrates that all non-identical phrasing fails. |
| **16** | With rates P&L of +$2,578,000, the hedge worked | Unresolved | Uncheckable | Falls through all regexes to line 99 fallback | **Misleading interpretation.** Abstention is due to syntax miss, not ambiguity detection. |

### Critical Case Observations
1. **The Case 15 Paraphrase Failure:**
   The report treats Case 15 as an isolated "missed error due to unfamiliar paraphrase." In reality, Case 15 is the only sentence that tests general phrasing. Its failure demonstrates that the method's real-world recall on unconstrained natural language is approximately 0%.
2. **The Case 16 Ambiguity Fallacy:**
   The report claims the system "abstains on ambiguous statement... correctly unresolved ambiguity." This is an invalid post-hoc attribution. The system has no logic for hedge objectives, effectiveness, or lexical ambiguity. Case 16 returned `Uncheckable` solely because it did not match any regex template. Conflating unhandled syntax exceptions with calibrated epistemic uncertainty is scientifically misleading.
3. **Causality Inconsistency (Case 05 vs. Case 13):**
   Case 13 rejects "P&L proves forced liquidation caused the market moves" because a linear P&L calculation cannot establish causation. Yet Case 05 explicitly accepts "EUR appreciation causes the short-EUR position's FX P&L... in the linear model" as a `Scoped match`. The engine does not distinguish factor attribution from economic causation; it merely executes hardcoded string branchings.
4. **Stale Metadata in Rationales:**
   As noted in `RESEARCH_LOG.md` (2026-10-29 entry), the frozen rationales for Cases 05, 06, and 15 refer to EUR/USD +1%, whereas the actual fixture uses +2% with -$3m delta producing -$60,000. While this does not alter the arithmetic sign, it highlights the hand-edited, unblinded nature of the fixture construction.

---

## 5. Generalization: Verified Findings vs. Unsupported Claims

### Verified Findings
1. **Deterministic Execution:** The regex rules run entirely offline with zero model calls, zero token consumption, and sub-millisecond execution latency (~0.9ms for 16 cases).
2. **Mechanical Consistency:** When a sentence matches one of the predefined templates, slot-filling logic accurately checks captured numeric tokens against dictionary values in the synthetic evidence catalog.
3. **Boundary Integrity:** Non-matching sentences, missing citations, or altered numeric values reliably abstain or return `Mismatch` rather than asserting whole-answer verification.

### Unsupported Claims
1. **"Meaning Alignment" / "Financial Language Understanding":**
   Unsupported. The system performs template slot matching, not linguistic parsing, semantic interpretation, or meaning representation.
2. **"General Error Detection (7/8)":**
   Unsupported. The detection rate reflects memorized templates, not empirical performance across financial prose.
3. **"Ambiguity Detection":**
   Unsupported. The candidate cannot discern ambiguous financial claims; it merely defaults to `Uncheckable` when syntax fails to match.
4. **Production Viability:**
   Unsupported. Muse Spark and other LLMs output varied, complex syntax that would trigger `Uncheckable` across virtually all responses, rendering the checker useless in production.

---

## 6. Reproducibility and Repository Provenance

1. **Test Suite Execution:**
   Pytest suite executed cleanly: `PYTHONPATH=backend:research .venv/bin/python -m pytest -q tests research/test_meaning_alignment.py` resulted in **150 passed in 2.85s** (145 backend tests + 5 research boundary tests), with the known Starlette deprecation warning.
2. **Results Reproduction:**
   Independent re-execution of `meaning_alignment_evaluation.py` confirmed that all summary metrics, per-case candidate outputs, baseline comparator outputs, evidence catalogs, and SHA-256 source and context hashes match `research/meaning-alignment-results.json` identically.
3. **Git Provenance:**
   The evaluation artifact is cleanly tracked under commit `36c18cd83065013e5ef6ada95e7832f10681db2a` on branch `main`.

---

## 7. Smallest Corrective Experiment Needed

If the Metis research team wished to rigorously measure the viability of deterministic sentence-level checking for meaning alignment, the following minimal experiment would be required:

### Minimal Out-of-Sample Evaluation Protocol
- **Objective:** Measure out-of-sample coverage (recall) and accuracy of template-based checking on real, model-generated financial text.
- **Data Source:** Sample 30 factual/causal sentences directly from archived historical model responses (`research/runs/observer-v08-20261028/` or `research/runs/evidence-grounded-v10-20261028/`), curated by an evaluator blinded to `meaning_alignment.py`.
- **Condition A (Candidate):** Run `meaning_alignment.py` on the 30 natural sentences.
- **Condition B (Baseline):** Run standard `FinancialClaim` extraction on the same 30 sentences.
- **Metrics:** Coverage rate (percentage of sentences parsed into a definitive verdict vs. `Uncheckable`), Precision on flagged errors, Recall on actual financial errors, and False Flag rate.
- **Stopping Rule:** Single offline pass over 30 sentences, 0 LLM calls, 0 compute cost.
- **Expected Outcome:** Condition A coverage is expected to fall below 10%, formally refuting the hypothesis that narrow regex templates can serve as an automated meaning verifier.

*(Note: Per user instructions, this corrective experiment is specified for scientific clarity only and must not be implemented.)*

---

## 8. Final Audit Recommendation

**Recommendation: Retain research only.**

1. **Do not integrate into production:** The current implementation would reject virtually 100% of real LLM outputs as `Uncheckable`, providing zero production utility while adding maintenance overhead.
2. **Do not conduct further validation or corrective experiments:** Metis's design principles (`AGENTS.md`, `RESEARCH_LOG.md`) prioritize bounded deterministic calculations over complex or brittle linguistic wrappers. Existing verification already verifies structured assertions with clear scope limits.
3. **Preserve report and code as negative evidence:** `research/meaning-alignment.md` and `meaning_alignment.py` should remain in the repository as a historical record demonstrating why handcrafted syntactic templates cannot solve semantic meaning alignment in AI-assisted financial systems.

---

## 2026-10-29 preservation and factual-verification addendum

This addendum records a repository review of the supplied audit before its first commit. The audit text above is preserved verbatim; its author/independence and historical execution time of 2.85s are source assertions, not independently authenticated by this review. No new financial cases or paraphrase experiment were run.

**Confirmed:** source inspection finds eight `re.fullmatch` rules and an unconditional unmatched-grammar `Uncheckable` fallback. The case/rule coupling, same-author visible-case design, absence of a held-out sample, and inability to attribute case16 abstention to ambiguity recognition are valid limitations. A replay of exactly the existing 16 cases reproduces all saved candidate/comparator outputs, evidence catalog, summary and source/context hashes, excluding volatile timings/timestamp/Git revision; archived bytes remain unchanged. The 7/8 count is descriptive in-sample coverage, not an estimated detector sensitivity. Faithful human production mappings contradict 02/04; the existing prototype gates 11/13 and retains manually supplied conditional stances for 12/14. All 150 tests currently pass in 2.78s with the existing Starlette/httpx warning. The completed experiment is tracked in commit `36c18cd83065013e5ef6ada95e7832f10681db2a`. No live inference was used.

**Qualifications/disagreements:**

- “Approximately 0%” real-world recall, “virtually 100%” rejection of real LLM outputs, and “zero production utility” are not measured by these 16 authored cases. The lone out-of-grammar error demonstrates a coverage miss, not a population estimate. Captured numeric tokens and label alternatives can vary within a rule, so “all non-identical phrasing fails” is too broad; arbitrary paraphrase support remains unestablished.
- The audit's section3 calls the underlying logic identical to existing checks. Arithmetic/missing-evidence ideas overlap, but existing interfaces do not represent the tested assertion-horizon extension or expected-loss scope, and the candidate explicitly checks currency direction. These are narrow hand-written additions, not evidence of general semantic understanding. The original report already separates the analyst mapping lanes and identifies these limits; baseline `Verified` verdicts never certify prose.
- Case05 explicitly scopes its FX explanation to the deterministic linear model; case13 asserts an identified macroeconomic cause of market moves. Accepting model-factor attribution while declining that macro-causal inference is not itself a financial inconsistency. Neither establishes causal language understanding.
- The saved ~0.9ms candidate total is a one-process microtiming, not a verified performance guarantee. “Zero compute cost” is not established: offline execution uses local CPU; monetary cost was not measured. No standard natural-language `FinancialClaim` extraction system exists in the current verifier, so the proposed future comparator requires definition and is not an existing capability.
- The frozen FX rationales' +1% references were already corrected by a dated finalization note: actual fixture08 uses +2% and -$3m delta. Preserve both provenance and findings. No rules, frozen cases, original outputs or historical report were changed in this review.

**Disposition:** preserve the audit as a critical interpretation, with the above factual bounds. Retain research-only status. Its proposed 30-sentence experiment and expected coverage are unexecuted proposals, not authorization or results. This verification does not expand the experiment, establish scientific reliability, or authorize production integration.
