# Scoped audit follow-up — 2026-10-29 (America/Los_Angeles)

Engineering validation of the H-2, H-3 and M-1 descriptions supplied in the task. No detailed Antigravity audit or exact M-1 reproduction fixture was available in the repository. This records observations against current code and the [documented verifier contract](financial-claim-verification.md), not a new financial-reasoning study.

| Finding | Disposition | Evidence |
| --- | --- | --- |
| H-2: unsupported custom causal hypotheses in Demo | Corrected | `/api/workstation` reports the configured causal mode. Demo renders two selectors containing the three supported templates, with an explicit explanation of the custom-input restriction. Request validation rejects unsupported Demo input before generation, including stale custom state. Live Meta retains free-form inputs; a mocked adapter test accepts a custom hypothesis. |
| H-3: structured checks can imply prose verification | Corrected | Answer/demo labels now say “Structured assertion checks.” Each verdict badge says “Structured assertion: …”; original prose separately remains “Not checked.” The visible scope note explicitly says semantic truth is not verified and mappings can accompany misleading sentences. A component-rendering regression uses profitable prose with a correct negative-P&L mapping and asserts both distinct labels. No verifier logic changed. |
| M-1: rising-yield verification | Not reproduced within documented scope | The three fixtures below verify exact scenario rates/total amounts and signs. All three existing `hedge_vs_total` assertions explicitly end in `yields_down`; each is correctly Contradicted for rising or unchanged yields. An unsupported `rates_loss_total_loss_yields_up` assertion is Not checked, as required for unknown labels. No composite rising-yield support is documented, so expanding that vocabulary would extend scope rather than repair a reproduced false verdict. |

## M-1 local reproduction

All unlisted shocks are zero. Existing synthetic positions, linear sensitivities and sign conventions are unchanged.

| Scenario shocks | Rates contribution | Total P&L | Number/sign results |
| --- | ---: | ---: | --- |
| Government yields +50bp | −$2,578,000 | −$2,578,000 | Verified |
| Government yields +50bp, equities +20% | −$2,578,000 | +$2,022,000 | Verified |
| All shocks zero (control) | $0 | $0 | Verified |

Each fixture additionally checks the three documented falling-yield composite assertions (Contradicted), their captured yield evidence, and the unsupported rising-yield composite label (Not checked). These observations do not establish arbitrary prose truth or cover an unavailable audit fixture. Decision: preserve deterministic verification semantics; retain focused coverage for the reported direction concern.

## Validation and limits

- `python -m pytest -q` through the repository virtual environment: **145 passed**, 3.67s reported test time.
- `npm test` in `frontend/`: **16 passed**, 0.388s reported duration. Actual TSX components are rendered with React server rendering and the existing TypeScript dependency; no new dependency or browser interaction test was added.
- `npm run build` in `frontend/`: TypeScript and Vite production build passed, 3.38s Vite build time.
- Existing Starlette/httpx deprecation and Vite bundle-size warnings remain.
- No live inference: model/endpoint/sampling settings not exercised or changed; **0 model calls, 0 inference tokens**, inference latency not applicable. Meta custom-input coverage uses a mock, not a live reliability claim. End-to-end UI latency was not measured.
- Prior completed reports, financial assumptions/data, Meta inference parameters and Anthropic integration are unchanged. No private responses or credentials are included.
