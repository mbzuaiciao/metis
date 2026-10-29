# Portfolio investigation review — 2026-10-29

**Judgment:** Metis has a credible hackathon proposition: explain a portfolio loss, challenge an economic explanation, then calculate the consequences of different assumptions. An experienced institutional PM can understand the initial attribution. Continuing the investigation requires too much manual reconciliation of question scope, scenario results and missing evidence. The three priorities below concern financial interpretation and decision usefulness, not styling.

This is a source/workflow review against the current application and documented demonstrations, after reading `AGENTS.md`, `README.md` and the research log. No new browser session, PM usability study or live inference was performed; usability effects below are judgments and proposed acceptance criteria, not measured outcomes. Current validation: 150 backend/research tests and 16 frontend tests pass. Historical model findings are taken from the linked reports, not regenerated. No hackathon rules or judging criteria were assumed.

The completed meaning-alignment artifacts remain unchanged. The supplied [independent audit](meaning-alignment-independent-audit.md) was preserved, fact-checked and committed with a dated qualification addendum and research-log entry in `ee3289a`. Its unmeasured near-zero real-world recall claims are not adopted as findings. Narrow template coverage does not establish semantic understanding or ambiguity detection.

## What already works

**What happened?** Overview directly reconciles the synthetic daily loss of **$560,770** to rates **+$412,480**, spreads **−$407,250**, equities **−$506,000** and FX **−$60,000**. Largest net position gain/loss and expandable factor legs are available without visiting all six pages. This is useful attribution; a rates gain is correctly distinguished from portfolio profitability.

**Why might it have happened?** The direct daily-investigation action, executive summary, captured calculations and expandable mechanisms form a usable starting point. Live/demo badges and explicit mapping-only verification boundaries are strengths. A growth scare remains an explanation to examine, not an identified cause; cited numbers cannot validate the narrative.

**Different scenarios?** Independent Shocks and Causal Exploration already support editable assumptions and deterministic consequences. Causal proposals require acceptance; edits invalidate results. This separation is the most compelling demonstration of financial judgment in the product.

**What next?** Stage4 already provides missing-data guides and calculation links. The weakness is specificity and continuity, not the absence of a checklist. Funding, default and liquidity losses cannot be ranked from the supplied sensitivities; lack of a hedge mandate also prevents a claim of optimal sizing.

## 1. A follow-up can silently change the investigation's financial scope

**Consequence:** after explaining the daily loss, “Which positions drove that?” goes through the generic composer with the currently selected hypothetical stress shocks. The preceding daily summary is included in history, but its calculation scope is not inherited. If scenario controls changed, the follow-up can refer to yet another shock set. A PM must resolve what “that” means; this can mislead even when every number is correct.

**Evidence:** [request construction](../frontend/src/investigation.ts), lines16–28, selects daily only for explicit `focus="daily"`; generic questions select the current scenario and replay the last three question/summary pairs. [App](../frontend/src/App.tsx), lines1410–1427, defaults `ask` to generic question. The sidebar shows current scenario controls (lines1294–1335), while answers correctly retain original calculations (lines1137–1175). Existing tests establish snapshot preservation, not follow-up scope continuity.

**Smallest improvement:** give the composer an explicit “Continue this investigation” target that defaults to the selected/latest answer's captured daily or scenario shocks. Show that scope beside the send action; make switching to the current stress a deliberate choice. Limit replayed history to that investigation. Reuse the existing request contract and engine; no prose inference or new verifier is needed.

**How to know:** an offline request/state test should show that a daily follow-up still sends daily shocks after stress edits, and a captured-scenario follow-up retains its original shocks until the user switches. In a short scripted walkthrough, the reviewer should identify the outgoing scope without opening JSON or navigating away. This is the single highest-value next change.

## 2. The strongest scenario comparison is dispersed beneath explanation and controls

**Consequence:** the interesting PM question is why the same yield move can produce very different portfolio outcomes. Independent Shocks displays one scenario at a time; Causal Exploration has two cards, but each places five factor narratives and editable assumptions ahead of its calculated attribution. The user must assemble the comparison by reading through both cards or transferring results back to another mode.

**Evidence:** [Scenarios rendering](../frontend/src/App.tsx), lines846–1009; [Causal Exploration](../frontend/src/CausalExploration.tsx), lines86–118. The [existing causal report](causal-exploration.md) documents accepted −50bp yield examples with totals −$29,500 and +$3,948,500: a clear demonstration that cross-asset assumptions, rather than a yield move alone, determine the outcome. Those are prior examples, not predictions or a guaranteed new model response.

**Smallest improvement:** after acceptance, show one compact A/B comparison above the mechanism cards: captured hypothesis names, accepted five shocks, total P&L and the four supplied factor contributions. Link to the existing detail rather than duplicating it. Clear this summary on edits and retain the unequal-yield warning. Display existing backend values; add no probability, causal-effect estimate or new financial calculation.

**How to know:** using existing deterministic demo outputs, a reviewer should identify which assumption/factor explains the difference and distinguish both hypothetical totals from daily P&L within 30 seconds, without changing pages. Existing acceptance/invalidation tests must still pass. The time target is proposed, not observed.

## 3. “Investigate next” still leaves the PM to translate generic concerns into a concrete request

**Consequence:** choosing what to ask a risk or operations colleague requires knowing which evidence gap could change a conclusion. Today the first model concern opens by default, but its full rationale is nested; the visible consequence/data list comes from headline keywords, and each concern links to the same complete position table. This can lend prominence to model ordering and generic analyst framing without establishing the concern or a loss ranking.

**Evidence:** [InvestigationFindings](../frontend/src/InvestigationEvidence.tsx), lines149–197, explicitly disclaims ranking but opens item0 and nests the original concern. [Topic guides](../frontend/src/investigation.ts), lines59–103, request broad categories of data. The [recorded reliability study](inference-reliability.md) reports unsupported hedge-undersizing and default-magnitude language despite correct totals. The completed [meaning-alignment study](meaning-alignment.md) does not provide a general semantic remedy.

**Smallest improvement:** for one selected concern, expose a short analyst-authored next-question card beside the unchanged model text: what the calculation establishes, what remains unknown, and the specific first data request. For funding: “Rates contribution is measured; cash adequacy is unknown. Obtain next-day margin obligations, CSA/netting/collateral terms and drawable liquidity before judging coverage.” Link directly to cash and swap rows in the captured evidence. Label selection as investigation priority, not quantified risk rank. Reuse existing guides; do not automatically certify the model's concern or add a workflow system.

**How to know:** a PM should state the precise first information request and explain why $6m cash or swap notionals alone cannot answer it, without opening the full context. A concern unsupported by contractual evidence must remain unestablished even when its numerical mapping is Verified. Assess this with a scripted offline review, not an automated semantic score.

## Recommendation and stopping point

**Do only priority1 next: bind follow-ups to an explicitly visible captured investigation scope.** It addresses a concrete path to financially misleading interpretation and makes the existing four-stage story coherent without new analytics or inference machinery. Priorities2/3 remain alternatives for later consideration. No recommendation was implemented, no production/frontend code or verification semantics changed, and this review is intentionally uncommitted. Stop after the review.

## 2026-10-29 finalization status

This report is a preserved **pre-correction review**, not a claim that all three shortcomings remain present. Priority1 was implemented in `69825ec8aed0348cb6ba89c158c5558a33f882c6`: UI follow-ups use backend-owned captured evidence and investigation-specific history, with explicit scope labels and fresh daily/scenario actions. Current validation passes159 backend/research tests and20 frontend tests plus the production build; these are later engineering checks, not replacements for the original review's observations or historical test counts. The [scope audit and verification addendum](investigation-scope-audit.md) document the tested guarantees and limitations. Priorities2/3 remain unimplemented recommendations. The user now authorizes committing this historical review; the earlier instruction to leave it uncommitted described its original stopping point.
