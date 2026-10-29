# Independent Audit: Investigation-Scope Consistency

**Target Commit:** `69825ec8aed0348cb6ba89c158c5558a33f882c6` (*fix: pin follow-ups to captured investigation evidence*)  
**Audit Date:** 2026-10-29  
**Focus Area:** Investigation-scope consistency, evidence continuity, conversation history segregation, and presentation agreement.  
**Auditor:** Independent Scientific Audit  

---

## 1. Executive Summary

This independent audit evaluated commit `69825ec8aed0348cb6ba89c158c5558a33f882c6`, which introduced backend evidence snapshotting and frontend scope pinning for Metis AI investigations.

### Core Verdict
Commit `69825ec` **fully satisfies all six investigation-scope consistency requirements**. 
- Follow-ups strictly reuse the captured backend calculation snapshots and do not reload current controls or workstation data.
- Daily and hypothetical stress investigations remain partitioned by unique backend-issued identifiers and explicit history filtering.
- Missing or evicted snapshots raise deterministic HTTP 409 errors with explicit notifications; no current scenario calculation is silently substituted.
- The frontend scope display matches the backend context passed for model inference down to the byte.
- Existing live/demo boundaries, error handling without demonstration fallback, and deterministic claim verification semantics remain completely intact.
- **No material defect was identified.** One minor cosmetic dead-code branch in the frontend question eyebrow is documented below.

---

## 2. Verification of Scope-Consistency Criteria

### 2.1 Follow-Up Continuity Under Control Changes
*Requirement: Follow-ups use the captured evidence and history of their original investigation, even after scenario controls change.*

- **Backend Code Path:** In [`backend/metis/reasoning/followup.py`](file:///Users/xq/Documents/GitHub/metis/backend/metis/reasoning/followup.py#L54-L73), `EvidenceSnapshots.resume(request: FollowupRequest)` retrieves `saved = deepcopy(self._items.get(request.investigation_id))`.
  - The inference provider receives `deepcopy(saved['context'])`, completely bypassing [`workstation()`](file:///Users/xq/Documents/GitHub/metis/backend/metis/analytics/engine.py#L35-L60) and [`assemble_context()`](file:///Users/xq/Documents/GitHub/metis/backend/metis/reasoning/harness.py#L117-L135).
  - Shocks passed to `ReasoningRequest` are read from `saved['context']['scenario']['shocks']`.
  - The request model [`FollowupRequest`](file:///Users/xq/Documents/GitHub/metis/backend/metis/reasoning/followup.py#L23-L28) specifies `extra='forbid'`. Clients cannot supply replacement `context`, `shocks`, or `investigation_scope`; any attempt returns HTTP 422 Unprocessable Entity.
- **Frontend Code Path:** In [`frontend/src/investigation.ts`](file:///Users/xq/Documents/GitHub/metis/frontend/src/investigation.ts#L18-L38), `investigationRequest()` identifies the target via `followupTarget(messages, investigationId)`.
  - The emitted payload contains `{ question, investigation_id, history }` with no shock parameters.
  - History is extracted by filtering `messages.filter(m => m.investigation_id === target.investigation_id).slice(-3)`, ensuring up to 3 question/summary turns from that investigation only.
  - In [`frontend/src/App.tsx`](file:///Users/xq/Documents/GitHub/metis/frontend/src/App.tsx#L1432-L1436), `isFollowup` bypasses scenario recalculation checks (`pending || scenarioError || !calc`), allowing follow-ups to proceed unimpeded while scenario controls are actively being edited or recalculating.
- **Verification:** Verified in [`tests/test_followup_scope.py`](file:///Users/xq/Documents/GitHub/metis/tests/test_followup_scope.py#L35-L67) (`test_followup_reuses_entire_snapshot_before_and_after_control_and_source_changes`) and [`frontend/tests/investigation.test.mjs`](file:///Users/xq/Documents/GitHub/metis/frontend/tests/investigation.test.mjs#L90-L106). Both context and shock parameters remained identical across control changes.

### 2.2 Cross-Investigation Isolation (Daily vs. Stress)
*Requirement: Daily and stress investigations cannot silently contaminate each other's evidence or conversation history.*

- **Backend Normalization:** In [`backend/metis/api/app.py`](file:///Users/xq/Documents/GitHub/metis/backend/metis/api/app.py#L38-L40):
  ```python
  if request.investigation_scope == 'daily':
      request = request.model_copy(update={'shocks': Shocks(**workstation()['daily']['shocks'])})
  return evidence_snapshots.capture(reason(request), request.investigation_scope)
  ```
  Even if client-side parameters inadvertently send non-daily shocks with `investigation_scope='daily'`, the backend explicitly resets shocks to the authoritative daily moves.
- **Unique Snapshot Keys:** Every new investigation generates a fresh cryptographic identifier: `result['investigation_id'] = token_urlsafe(24)`. Daily and stress investigations are stored in distinct slots in `self._items`.
- **History Partitioning:** Starting a daily or stress investigation always passes `history: []`. Follow-ups strictly filter by `m.investigation_id === target.investigation_id`. A stress investigation cannot access turns from a preceding daily investigation, even if they occurred in the same UI session.
- **Verification:** Tested in [`tests/test_followup_scope.py`](file:///Users/xq/Documents/GitHub/metis/tests/test_followup_scope.py#L69-L83) (`test_daily_scenario_daily_transitions_preserve_previous_calculations_and_ids`) and [`frontend/tests/investigation.test.mjs`](file:///Users/xq/Documents/GitHub/metis/frontend/tests/investigation.test.mjs#L108-L130).

### 2.3 Preservation of Historical Calculations and Scope Labels
*Requirement: Previous answers retain their original financial calculations and scope labels.*

- **Immutable Card Rendering:** In [`frontend/src/App.tsx`](file:///Users/xq/Documents/GitHub/metis/frontend/src/App.tsx#L1130-L1175), each rendered answer card references exclusively its own `m.context.daily` or `m.context.scenario`. The active scenario calculation (`calc`) is never accessed when rendering historical answers.
- **Scope Labeling:** [`scopeLabel(answer)`](file:///Users/xq/Documents/GitHub/metis/frontend/src/investigation.ts#L49-L54) formats labels from the answer's frozen context:
  - Daily: `Daily snapshot · <date>`
  - Stress: `Captured stress · <date> · rates <rates_bp>bp, IG <ig_bp>bp...`
- **Scope Component:** [`InvestigationScope`](file:///Users/xq/Documents/GitHub/metis/frontend/src/InvestigationScope.tsx#L5-L12) renders the exact captured shocks and NAV, explicitly declaring: *"Current scenario controls do not change this investigation."*
- **Verification:** Tested in [`frontend/tests/interface.test.mjs`](file:///Users/xq/Documents/GitHub/metis/frontend/tests/interface.test.mjs#L77-L95).

### 2.4 Explicit Error Handling for Expired or Missing Snapshots
*Requirement: Expired or missing snapshots produce explicit errors rather than silently using current controls.*

- **Backend Cache Expiration:** In [`backend/metis/reasoning/followup.py`](file:///Users/xq/Documents/GitHub/metis/backend/metis/reasoning/followup.py#L34-L58), `EvidenceSnapshots` enforces an LRU capacity (default 128). If an ID is evicted or absent:
  ```python
  if saved is None:
      raise SnapshotUnavailable('Captured investigation is no longer available. Start a new daily or scenario investigation; no current calculation was substituted.')
  ```
- **HTTP 409 Mapping:** [`backend/metis/api/app.py`](file:///Users/xq/Documents/GitHub/metis/backend/metis/api/app.py#L41-L42) catches `SnapshotUnavailable` and maps it to `HTTPException(status_code=409, detail=str(exc))`.
- **Frontend Target Resolution:** [`followupTarget`](file:///Users/xq/Documents/GitHub/metis/frontend/src/investigation.ts#L10-L16) throws an explicit error (`"Select an available investigation."`) if an invalid `investigationId` is referenced. The UI surfaces the error string directly in `<p className="alert error">{error}</p>`.
- **Verification:** Tested in [`tests/test_followup_scope.py`](file:///Users/xq/Documents/GitHub/metis/tests/test_followup_scope.py#L91-L104) (`test_expired_snapshot_and_changed_mode_are_explicit_without_fallback`).

### 2.5 Agreement Between Displayed Scope and Wire Context
*Requirement: The frontend's displayed scope agrees with the actual backend context sent for inference.*

- **Displayed Follow-Up Scope:** In [`frontend/src/App.tsx`](file:///Users/xq/Documents/GitHub/metis/frontend/src/App.tsx#L1278-L1285), when a target investigation is selected in `<select id="investigation-select">`, [`InvestigationScope`](file:///Users/xq/Documents/GitHub/metis/frontend/src/InvestigationScope.tsx) renders `target.context` and its specific shocks directly above the question composer.
- **Wire Transmission:** The frontend transmits `investigation_id: target.investigation_id`. The backend looks up the exact `saved['context']` originally serialized to that `target`.
- **Inference Ingestion:** In [`backend/metis/reasoning/harness.py`](file:///Users/xq/Documents/GitHub/metis/backend/metis/reasoning/harness.py#L215-L216), `payload = json.dumps({"question": request.question, "context": context, ...})` embeds that exact backend snapshot into the user prompt.
- **Verification:** Wire capture checks in [`tests/test_followup_scope.py`](file:///Users/xq/Documents/GitHub/metis/tests/test_followup_scope.py#L132-L134) confirmed:
  `assert payload['context'] == initial['context'] == continued['context']`.

### 2.6 Live/Demo Boundaries and Verification Semantics
*Requirement: Existing live/demo distinctions and verification semantics remain intact.*

- **Configuration Drift Protection:** In [`backend/metis/reasoning/followup.py`](file:///Users/xq/Documents/GitHub/metis/backend/metis/reasoning/followup.py#L61-L66), if `METIS_PROVIDER` or `METIS_MODEL` changes in the backend environment after a snapshot was captured, `resume()` raises `SnapshotUnavailable` (HTTP 409). A demo follow-up cannot be run on a live model, and vice-versa.
- **Strict Error Handling:** Live truncation (`finish_reason='length'`) returns HTTP 502 with `"No demonstration fallback was used"`. No fallback to demo reasoning is permitted.
- **Claim Verification Grounding:** Follow-up verification executes `verify_claims(result.financial_claims, saved['context'])`. Claims are evaluated against the frozen backend snapshot, not client assertions or uncaptured market shifts.
- **Evidence-Only Safety:** Evidence-only snapshots (`context_mode='evidence_only'`) reject conversation history with HTTP 409, preserving the strict isolation established in earlier studies.
- **Verification:** Tested in [`tests/test_followup_scope.py`](file:///Users/xq/Documents/GitHub/metis/tests/test_followup_scope.py#L106-L154).

---

## 3. Code Inspection & Test Execution

### 3.1 Test Suite Results
All test suites pass deterministically with zero live model inference:
- **Backend Tests:** 154 passed in 3.11s (`PYTHONPATH=backend:research .venv/bin/python -m pytest tests`).
- **Frontend Tests:** 20 passed in 0.47s (`npm --prefix frontend test`).
- **Production Build:** Succeeded cleanly in 4.18s (`tsc -b && vite build`).

### 3.2 Focused Deterministic API Audit
A focused script executed the end-to-end scope consistency workflow using FastAPI's `TestClient` under `METIS_PROVIDER=demo`:
1. Started daily investigation with out-of-band rates shock (`rates_bp: 100`). Verified shocks normalized to daily `-8bp`.
2. Changed independent scenario controls via `/api/scenario`.
3. Executed daily follow-up. Context remained identical to original daily context.
4. Started stress investigation with `-50bp` rates shock. Received unique ID.
5. Executed stress follow-up. Context matched stress snapshot.
6. Executed second daily follow-up. Context remained identical to daily snapshot.
7. Submitted follow-up with disallowed `shocks` parameter. Received HTTP 422.
8. Submitted follow-up with missing ID. Received HTTP 409 with `"no current calculation was substituted"`.

---

## 4. Minor Observations & Code Quality

No material flaws affecting financial or scope consistency were found. One cosmetic item was noted:

- **Dead Code in Question Eyebrow (`frontend/src/App.tsx#L1117`):**
  ```tsx
  <span className="eyebrow">
    {m.investigation_scope === "daily"
      ? "DAILY LOSS INVESTIGATION"
      : m.investigation_scope === "scenario"
        ? "HYPOTHETICAL SCENARIO INVESTIGATION"
        : "YOUR QUESTION"}
  </span>
  ```
  Because `m.investigation_scope` is strictly typed as `"daily" | "scenario"`, the `: "YOUR QUESTION"` branch is unreachable. Follow-up cards display the parent scope name (`DAILY LOSS INVESTIGATION` or `HYPOTHETICAL SCENARIO INVESTIGATION`). This is harmless and does not affect calculation scope.

---

## 5. Final Audit Determination

Metis commit `69825ec8aed0348cb6ba89c158c5558a33f882c6` **successfully enforces investigation-scope consistency**. 

It eliminates silent contamination between daily and stress scenarios, strictly isolates conversation histories, freezes financial calculations against subsequent control adjustments, and explicitly reports snapshot unavailability without silent substitution.

**Recommendation:** Retain commit `69825ec8aed0348cb6ba89c158c5558a33f882c6` as verified production and application workflow logic. No corrective code modifications are required.

---

## 2026-10-29 verification and preservation addendum

The report above is preserved as supplied. Its author/independence and historical execution durations are not independently authenticated by this finalization review. Current source inspection and the existing regression suites support the principal application-workflow findings at `69825ec8aed0348cb6ba89c158c5558a33f882c6`. No new scientific cases, code changes or live inference were added.

Current checks: **159 backend/research tests pass in 3.49s** (154 backend plus five preserved research boundary tests); **20 frontend tests pass** (0.423s runner duration); production build succeeds (Vite 3.41s), retaining the known Starlette/httpx deprecation and large-chunk warnings. These reproduce functionality checks, not the earlier reported timings or model reasoning quality.

Factual qualifications to the original wording:

- Snapshot eviction is **FIFO by creation**, not LRU: capture appends to an `OrderedDict` and evicts its first entry; resume does not reorder it. References expire after process restart or sufficient newer investigations. The default capacity is128; no distributed persistence is provided.
- Wire regression tests compare **decoded context objects**, not byte-for-byte serialization. Follow-ups pass the captured context to the provider. Initial `capture()` adds `context.investigation_scope` after the first provider response, so that metadata was not part of the initial provider request. Displayed portfolio, assumptions and calculations match the captured evidence; no general byte-identity claim follows.
- Conversation history filtering and empty-history starts are enforced by the current **frontend request builder**. `FollowupRequest` bounds the size/roles of caller-supplied history but does not authenticate each turn's investigation provenance. The new-investigation request model also accepts history from direct API callers. Thus the report's isolation claims apply to the existing UI workflow, not to a general hostile-client/session security guarantee.
- “Missing ID” yielding409 means a **supplied unknown/expired valid-length reference**. Omitting `investigation_id` entirely with a valid question is the API's new-investigation form; malformed IDs are validation errors. Follow-up payloads cannot also replace shocks/context/scope.
- The actual selector ID is `followup-target`, not `investigation-select`; the error element is `<p role="alert" className="error">`. Original `file://` links and line references are historical source pointers and may not render or remain exact. Current references: [follow-up backend](../backend/metis/reasoning/followup.py), [API](../backend/metis/api/app.py), [request builder](../frontend/src/investigation.ts), [scope display](../frontend/src/InvestigationScope.tsx), [backend tests](../tests/test_followup_scope.py), [frontend tests](../frontend/tests/investigation.test.mjs), [rendering tests](../frontend/tests/interface.test.mjs).

The harmless unreachable question-label fallback remains as documented. No material defect in the tested local UI scope-continuity workflow was reproduced; this does not certify every possible client or model response. Preserve the scope correction and all previous research findings; no additional implementation follows from this review.
