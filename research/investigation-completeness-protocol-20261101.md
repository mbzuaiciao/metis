# Live investigation completeness: preregistered baseline protocol (2026-11-01)

**Status: ready to run, NOT executed.** The assistant's current execution environment does not have the user's Meta API credentials and cannot call Muse Spark. Do not interpret any of the earlier 4/6 deterministic routing illustrations as model results.

## Hypothesis and scope
Can the existing Metis Muse Spark investigation surface the decision-relevant questions in six frozen synthetic portfolio scenarios, without a separate checklist? This is the *baseline only*. No candidate intervention, production changes, agent orchestration, or second-model reviewer is implemented. The earlier deterministic vulnerabilityGuide probe concerns UI topic routing, not reasoning capability.

## Inputs and isolation
- Frozen study file: `research/investigation-completeness-cases-20261101.json`; six distinct questions and analyst-authored target questions.
- Runner: `research/investigation_completeness_live_20261101.py`.
- Same Metis `assemble_context(Shocks())`, `ReasoningRequest` with empty history and `HTTPProvider("meta").interpret` as existing production. The six inquiries are variations on the same synthetic portfolio; not statistically independent market observations.
- Required settings `muse-spark-1.3`, existing `META_INFERENCE_PARAMETERS` (low reasoning effort, 8,000 completion budget, temperature 0.2), 60-second HTTP provider timeout. One call per case, in case ID order; max six requests; **stop on first failure; zero retries**.
- Only the case question and existing context enter inference. The required questions and prohibited overclaims stay in the JSON case file, never in the request payload. Model responses, token counters, latency, and input hash are saved under ignored `research/runs/`; never commit private outputs or credentials. No demo fallback.
- Run locally from root with Metis credentials configured in `.env`:

```sh
METIS_PROVIDER=meta METIS_MODEL=muse-spark-1.3 uv run python research/investigation_completeness_live_20261101.py
```

## Scoring, performed AFTER outputs are frozen

For each case and each `required_questions`, human reviewer marks:
- **Present**: investigation or uncertainty makes an intelligible, specific request or qualification sufficient to address the stated issue anywhere in the *complete* response, including vulnerability and uncertainty fields.
- **Missing**: no meaningful mention.
- **Ambiguous**: generic topic named without sufficiently identifying the required inquiry; report separately, not counted as present.

For each `unjustified_conclusions`, mark whether the complete answer **asserts** that forbidden conclusion without relevant evidence, rather than just discussing it as a possibility or warning against it.

Record individual case judgments, supporting excerpts, and disagreements; do not reduce to a headline percentage alone. Main descriptive outputs: number of present/ambiguous/missing required items, distribution across cases, number of unjustified conclusions, schema failures, call/usage/latency totals. Zero failures does not establish reliability. Acknowledge same-author rubric and case construction, no blinded evaluation, no held-out sampling.

## Follow-on intervention (separate decision, not part of baseline)

After reviewing baseline omissions, decide whether a fixed independent *question-completeness* checklist is warranted. For a proper comparison, keep the six originals frozen; do not quietly adjust cases or prompts. A checklist applied offline to saved output tests detection, not whether a model's rewritten answer improves. If asking Muse Spark to revise, preserve the original and record an extra-call control to separate benefit of re-reading from checklist guidance; otherwise make no causal claim. Do not send the hidden answer-key questions to the model under the guise of verification.

## Stopping rule

Stop after six baseline live attempts or first failure, whichever comes first. A null or negative result is informative; no feature integration by default. Never automatically resume or rerun. Follow AGENTS.md: append a dated research-log entry only after actual execution and scored results; mark unavailable fields explicitly.
