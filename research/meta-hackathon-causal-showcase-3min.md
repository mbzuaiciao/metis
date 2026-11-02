# Metis — three-minute causal-exploration showcase

**2026-11-02 · recording proposal · not an inference experiment**

## Central idea

**One market movement can have very different implications depending on why it happened.** Metis uses Meta Muse Spark to explore possible economic mechanisms; the analyst reviews the assumptions; the existing financial engine calculates portfolio outcomes. The model does not discover the true cause or calculate the P&L.

This complements—not replaces—the historical [five-to-six-minute demonstration](meta-hackathon-demo-plan.md). The new recording must be three minutes.

## Preparation and truth labels

- Use the existing local startup instructions in [README](../README.md#run-locally). Check that the chosen provider is clearly labeled in the UI.
- **LIVE META** means a real Meta Model API response. Set `METIS_PROVIDER=meta` and a valid local `METIS_MODEL`, `METIS_META_BASE_URL`, and `METIS_META_API_KEY`; never put credentials in a recording. Run one authorized preflight and inspect the actual returned hypotheses before recording. Results and latency are not predetermined.
- **DETERMINISTIC DEMO** means fixed, labeled application templates. They demonstrate the interface and scenario math, **not** actual model generation. Do not claim a demo-mode result was produced live by Meta.
- The portfolio and dated market snapshot are synthetic. Hypothetical shocks are uncalibrated, and outputs are not actual market predictions.
- **The 3-minute video should include visible evidence of a genuine Muse Spark response**, ideally in the causal workflow. If live inference fails, show that failure as a limitation rather than disguising a fixed template as live generation. A labeled demo-mode segment may be used for reproducible screen capture alongside clearly identified real Meta footage.
- The comparison is displayed **only after** clicking **Accept reviewed shocks & calculate both**. Changing an assumption clears both calculated results.

## Shot plan and suggested narration

| Time | Screen action | Narration |
| --- | --- | --- |
| 0:00–0:20 | Overview: synthetic $100m portfolio; daily loss of $560,770 and positive rates contribution | “Risk software can tell us what a portfolio lost. But the harder question is why—and what we might be missing.” |
| 0:20–0:40 | Click **Explore competing explanations**; show the two hypotheses and shared yield move | “Imagine yields fall by 50 basis points. Is that a warning about recession—or welcome inflation relief?” |
| 0:40–1:35 | In **Causal Exploration**, generate the hypotheses in LIVE META mode; show the provider badge, economic mechanisms, proposed cross-asset directions, and discriminating evidence | “Muse Spark develops different economic explanations and traces how each could affect credit, equities, and foreign exchange. It also tells us what evidence we would need to distinguish them.” |
| 1:35–2:25 | Review the proposed shocks, click **Accept reviewed shocks & calculate both**, and display the new side-by-side comparison | “An analyst reviews the assumptions before Metis calculates the consequences. The same yield move can accompany very different portfolio results because the other markets respond differently.” |
| 2:25–2:45 | Briefly open an evidence or uncertainty detail, or show existing selected claim checks | “We separate what was calculated, what the model proposed, and what remains unknown.” |
| 2:45–3:00 | Return to the comparison panel | “Metis helps analysts investigate competing explanations, not just read risk numbers.” |

**The new side-by-side totals are produced from backend results, not model arithmetic.** For the fixed **demo-mode** recession-fears and inflation-relief templates only (shared rates move −50bp), the pre-existing expected results are **−$3,347,000** and **+$5,070,500**. Do not put those numbers in the narration for a live Meta run unless its reviewed shocks actually reproduce them.

## Minimal acceptance criteria

1. Overview's shortcut opens **Scenario Analysis → Causal Exploration** without starting an API call.
2. After generation, each hypothesis and proposed shock set remains inspectable, with visible LIVE META or DETERMINISTIC DEMO labeling.
3. Before acceptance, no A/B calculated comparison is shown. After acceptance, both totals and four factor contributions appear together using backend values; the same-yield claim appears only if the accepted rates inputs agree.
4. Editing a shock clears both comparisons. Independent Shocks and earlier investigations retain their existing functionality.
5. Test `npm test` and `npm run build` in `frontend/` and `uv run pytest -q` at the repository root before merging; rehearse once in the actual browser. Do not infer test success from this document.

**Stop after a usable three-minute recording and submission-ready presentation.** No additional agent framework, provider, economic estimation engine, or verification layer is required.
