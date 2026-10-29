# Meaning versus numerical evidence — bounded offline study, 2026-10-29

The narrow rules detect meaningful attribution and scope errors beyond checking correct cited numbers. **They flag 7 of 8 intended errors, miss one unfamiliar paraphrase through abstention, preserve five supported statements, retain two conditional hypotheses, and abstain on one ambiguous statement. No misleading verdict was observed in these 16 cases.** This is an in-sample coverage demonstration, not evidence of general semantic understanding, reliability or production readiness. Keep the method research-only; stop after this evaluation.

## Scope and provenance

Read the repository guidance, [research memory](RESEARCH_LOG.md), [production-verification report](financial-claim-verification.md), [evidence-grounding report](evidence-grounded-reasoning.md), and current verifier/prototype before designing this study. Previous studies already establish arithmetic/mapping boundaries; their live inference and 23 analyst probes were not repeated. No private outputs were read, copied or altered.

New artifacts:

- [Frozen 16 statements and financial rationales](meaning-alignment-cases.json).
- [Preimplementation protocol](meaning-alignment-protocol.md).
- [Research-only sentence checker](meaning_alignment.py) and [offline comparison adapter](meaning_alignment_evaluation.py).
- [Per-case outputs, evidence paths, source/input hashes and timings](meaning-alignment-results.json).
- [Boundary regression tests](test_meaning_alignment.py).

Expected interpretations were written before the checker, from signed FX conventions, contribution identities, funding horizons and default/expected-loss distinctions. Labels/rationales are stored separately and never passed to the checker. This is procedural independence from method output, **not independent adjudication**: the same analyst authored cases, expectations and rules, with no blinded review. The rules were written with all cases visible. Case15 was deliberately left outside the grammar; it is not a held-out test. Correct financial interpretations do not become proof of automated understanding simply because their labels were fixed first.

## Evidence and design

All inputs are existing synthetic data. The production snapshot supplies the daily total -$560,770 and CS01 $15,950/bp; Broad Risk-Off supplies HY net -$872,500, HY spread -$1,112,500, rates +$2,578,000 and total -$3,347,000. This study adds new statements about these facts, rather than rerunning a previous experiment.

Cases05/06/15 use **a separate snapshot** recalculated from v1.0 fixture08: EUR/USD +2%, EUR delta -$3m, FX P&L -$60k. The production FX position is long EUR, so pre-execution inspection ruled it out as the intended short-EUR evidence. The existing verifier receives this separate calculation as its daily snapshot for those cases only. These statements concern that synthetic snapshot, not production's daily FX direction. Funding cases reuse fixture07's $1.5m cash plus $0.4m drawable facility against exhaustive next-day $1.1m margin plus $0.3m other outflows. Default cases reuse fixture08's $6.4m face, 100% default and 35% recovery. These separate examples do not constitute one reconciled portfolio-wide funding/default calculation; no default loss is added to linear stress P&L.

The candidate accepts only raw **statement, citation key and a source-derived evidence catalog**. It uses whole-sentence regular-expression rules to capture subject, metric, amount, currency direction and selected scopes. It compares those fields with trusted offline calculations. No case ID, expected verdict, stance, category or human semantic mapping enters it. Rule labels and citation metadata are human-authored engineering knowledge; this is automated matching within that knowledge, not learned financial interpretation. There is no model, framework or production integration.

Only entire recognized sentence forms receive a scoped disposition. Unknown citations, additional clauses, negation outside the grammar, unfamiliar phrasing and ambiguity abstain. `Scoped match` means agreement for that complete recognized pattern and synthetic scope, never a whole-answer verification. `Mismatch` identifies incompatible attribution/value/direction. `Not established` identifies evidence insufficient for the asserted scope, not proof that the proposition is false in the real world. `Conditional hypothesis` does not verify the economic mechanism.

## Existing-method comparison

Two comparator lanes prevent conflating cited-fact checks with interpretation checks:

1. **Cited facts:** unchanged production `FinancialClaim` checks compare the correctly cited numerical quantity; unchanged prototype `EvidenceClaim` fact checks compare an available scalar path. These mappings are analyst supplied, not automatically extracted. The fact prototype cannot aggregate HY rows through its scalar-path interface, so 01/02 are Uncheckable there. Production's fixed vocabulary cannot check supplemental funding/default calculations, so 07–10 are Uncheckable there. In funding/default fact rows, the scalar basis is explicitly cash $1.5m or issuer face $6.4m, not the derived $1.9m/$4.16m sentence amount; those results test evidence availability/equality only. The result records preserve these paths/values.
2. **Human interpretation mappings:** where supported, run the unchanged prototype's definitive/conditional category checks. For 07/08, both mappings assert funding adequacy; its horizon remains the supplied next-day horizon because there is no separate assertion-scope field. For 09/10 both assert default-scenario equality, because there is no expected-loss vocabulary. These lossy mappings support the narrower conclusion while original wording remains unchecked. On 11/13 the prototype already records missing concentration/causal evidence; on 12/14 its analyst-supplied conditional stance is retained. Separately, faithful human production mappings of 02 as spread P&L and 04 as total P&L are both Contradicted. These demonstrate that correct human semantic remapping already enables the arithmetic verifier to catch those errors.

Unsupported cases are **Uncheckable, not failures or incorrect verdicts**. Existing `Verified`/`Supported` outputs below apply only to mappings; every actual returned baseline result retains original wording `Not checked`. No baseline falsely claims to verify prose. Lossy mapping examples demonstrate a boundary, not an implementation defect.

| ID | Expected financial interpretation | Production cited fact | Prototype scalar fact | Prototype human conclusion | Candidate |
| --- | --- | --- | --- | --- | --- |
| 01 | Supported HY net loss | Verified | Uncheckable | Uncheckable | Scoped match |
| 02 | Error: net called spread-only | Verified | Uncheckable | Uncheckable | Mismatch |
| 03 | Supported rates contribution | Verified | Supported fact | Uncheckable | Scoped match |
| 04 | Error: rates called portfolio total | Verified | Supported fact | Uncheckable | Mismatch |
| 05 | Supported EUR direction and short-EUR loss | Verified | Supported fact | Uncheckable | Scoped match |
| 06 | Error: same loss called USD appreciation | Verified | Supported fact | Uncheckable | Mismatch |
| 07 | Supported next-day funding coverage | Uncheckable | Supported basis fact | Supported scoped conclusion | Scoped match |
| 08 | Error: next-day evidence extended to all horizons | Uncheckable | Supported basis fact | Supported narrower conclusion | Not established |
| 09 | Supported specified default loss | Uncheckable | Supported basis fact | Supported scoped conclusion | Scoped match |
| 10 | Error: scenario loss called expected loss | Uncheckable | Supported basis fact | Supported narrower conclusion | Not established |
| 11 | Unsupported concentration from CS01 | Verified | Supported fact | Not established | Not established |
| 12 | Conditional concentration hypothesis | Verified | Supported fact | Conditional hypothesis | Conditional hypothesis |
| 13 | Unsupported causal conclusion from P&L | Verified | Supported fact | Not established | Not established |
| 14 | Conditional liquidation hypothesis | Verified | Supported fact | Conditional hypothesis | Conditional hypothesis |
| 15 | Error: USD-strength paraphrase | Verified | Supported fact | Uncheckable | Uncheckable — missed error |
| 16 | Ambiguous “hedge worked” | Verified | Supported fact | Uncheckable | Uncheckable |

Production cited-fact results: **12 Verified, 4 Uncheckable**. Prototype scalar results: **14 Supported fact, 2 Uncheckable**. Prototype human-conclusion results: **4 Supported scoped conclusion, 2 Not established, 2 Conditional hypothesis, 8 Uncheckable**. The separate literal human diagnostics for 02/04 return **2 Contradicted**. These are coverage counts for different mappings, not comparable accuracy scores. No unsupported baseline row is counted as an error.

Candidate results: **5 Scoped match, 3 Mismatch, 4 Not established, 2 Conditional hypothesis, 2 Uncheckable**. The eight expected errors are 02/04/06/08/10/11/13/15; seven flagged, one missed. No supported/conditional/ambiguous case is flagged, and no erroneous sentence gets Scoped match. Neither conditional hypothesis is promoted to a supported conclusion. Two total abstentions include the missed error and the correctly unresolved ambiguity.

Relative to correct cited-number checks, all seven flags expose interpretation problems those number checks leave unassessed. Relative to the **human interpretation** comparator lanes, 02/04 are already caught by faithful production mappings and 11/13 are already gated by the prototype. The clearest additional pattern-based checks are therefore **06 currency direction, 08 funding horizon extension and 10 default-scenario versus expected-loss scope**. All involve correct numerical evidence. The candidate also removes the need to supply human semantic labels on its recognized patterns. That is a limited incremental capability, not proof of broad financial language understanding.

## Execution, cost and failures

Exactly one financial evaluation, 16 cases; no inference attempts, no retries, no post-result rule tuning, no additional financial cases. **Model/endpoint/settings: not applicable. Model calls: 0. Inference tokens: 0. Inference latency: not applicable.** No credentials loaded or private reasoning inspected. Local results are synthetic statements/rule outputs, not private model responses, and can be versioned outside ignored `research/runs/`.

Measured local evaluation loop: **0.015485s** including result construction and input hashing; excludes imports, evidence assembly, output serialization and interpreter startup. Within that loop the 36 actual existing-method function calls total **0.001061s**, and 16 candidate calls total **0.000899s**. Unsupported adapter rows return without calling a method. These one-process microtimings include cold regex compilation and are not production latency or speed comparisons. The shell command took approximately 0.482s including startup. No inference usage is unknown; monetary cost and production throughput were not measured.

No evaluation case raised an exception. Pre-execution input inspection corrected the FX evidence source and retained the actual supplied funding-horizon description, before the financial evaluation. A new boundary-test assertion initially failed because it banned the English word `expected`, which legitimately appears in “expected issuer default”; it was replaced by an explicit checker-signature assertion. **149 passed / 1 failed initially; final 150 passed in 3.08s**, including all 145 existing backend tests and five research boundary tests. No checker, case, expectation or evaluation result changed after execution. Existing Starlette/httpx deprecation warning remains. Frontend/build checks were not run because no frontend or production files changed.

Command: `PYTHONPATH=backend:research .venv/bin/python -m pytest -q tests research/test_meaning_alignment.py`. Tests cover full-sentence coverage, added unsupported clauses/negation, unknown/wrong citations, changed evidence, conditional wrong numbers, horizon/FX boundaries, and frozen source hashes. They do not rerun the 16-case evaluation. The results retain exact source hashes and the canonical context hash; historical reports and private records remain unchanged.

## Interpretation and decision

**Observation:** targeted sentence rules catch seven meaningful errors without an observed false flag or false support in this hand-authored set, while preserving scoped positives and conditional language. **Interpretation:** automatic extraction of a few explicit semantic distinctions can add value beyond verifying an evidence amount. **Hypothesis:** more varied real output might benefit from similar bounded checks; this study does not test that hypothesis.

The negative result matters: one ordinary financial paraphrase already defeats coverage. Fixed currency assumptions support only short EUR with EUR/USD rising. There is no arbitrary negation, discourse/coreference, temporal reconciliation, omitted-claim detection, hedge-objective extraction or general causal analysis. New equivalent wording generally abstains. Malformed/untrusted evidence catalogs are outside this trusted offline adapter; this is not a hardened public verifier. Synthetic contractual completeness, enforceability and economic plausibility are not independently established. One author and visible cases favor the rules; seven detections cannot estimate reliability, causality or real-world false-positive rates. Whole-sentence matching reduces misleading partial support but cannot establish completeness outside its finite grammar.

**Engineering decision:** retain the prototype as research evidence only. The bounded study answers “can a narrow rule detect this class of mismatch?” positively for selected patterns. It does not justify a general semantic-verification claim or integration. No production/frontend change, new framework, fine-tuning, infrastructure or live LLM inference was made. Stop here; any broader semantic-model evaluation or product integration requires a separate authorized task.

## 2026-10-29 finalization review and provenance correction

The user explicitly requested reproduction of the completed experiment before committing it. One offline replay of the same 16 cases reproduced every candidate and comparator output, summary, evidence catalog, source hash and context hash. Volatile execution timestamp, Git revision and timings were excluded from equality checks. The archived results file was hash-checked before and after and was not overwritten. No new cases, changed rules or LLM calls were added. The finalization test run passed all 150 tests in 2.88s, with the same existing Starlette/httpx warning.

**Documentation correction:** the frozen rationales for cases05/06/15 refer to EUR/USD +1%; the actual reused fixture08 input, archived catalog and report's evidence description correctly use **+2% with -$3m EUR delta**, producing -$60,000. The +1% references are stale oracle explanatory metadata from before source inspection, not the executed inputs. Positive EUR/USD still means EUR appreciation, so this correction changes neither statement, expected interpretation nor verdict. Preserve the original case/rationale file and archived output (which copies those rationales) to retain frozen hashes and provenance. This dated note supersedes only those three percentage references; it does not revise the financial findings.
