import { useEffect, useRef } from "react";
import type { Dispatch, SetStateAction } from "react";
import type { Calculation, CausalRequest, CausalResult, Shocks, Workstation } from "./types";
import { acceptProposals, causalRequest, editAssumption, demoHypotheses, type CausalState } from "./causal";
import { FactorEvidence, PositionEvidence } from "./InvestigationEvidence";
import { EpisodeCards } from "./EpisodeCards";
import { EventSnapshots } from "./EventSnapshots";

const usd = (value: number) => new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD", maximumFractionDigits: 0,
}).format(value === 0 ? 0 : value);
const pnlTone = (value: number) => value > 0 ? "positive" : value < 0 ? "negative" : "muted";

const factors: [keyof Shocks, string, string, number, number][] = [
  ["rates_bp", "Government yields", "bp", -300, 300],
  ["ig_bp", "IG spreads", "bp", -300, 500],
  ["hy_bp", "HY spreads", "bp", -500, 1500],
  ["equity_pct", "Equities", "%", -60, 60],
  ["fx_pct", "EUR/USD", "%", -30, 30],
];

function mechanismSummary(text: string): string {
  const match = text.match(/^.*?[.!?](?:\s|$)/);
  return match ? match[0].trim() : text;
}

function formatFactorList(items: string[]): string {
  if (items.length === 0) return "";
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(", ")}, and ${items[items.length - 1]}`;
}

export function comparisonSummary(c0: Calculation, c1: Calculation, title0: string, title1: string): string {
  const s0 = c0.shocks;
  const s1 = c1.shocks;
  const sameRates = s0.rates_bp === s1.rates_bp;

  const creditDiffers = s0.ig_bp !== s1.ig_bp || s0.hy_bp !== s1.hy_bp;
  const equityDiffers = s0.equity_pct !== s1.equity_pct;
  const fxDiffers = s0.fx_pct !== s1.fx_pct;

  const otherDiffs: string[] = [];
  if (creditDiffers) otherDiffs.push("credit");
  if (equityDiffers) otherDiffs.push("equity");
  if (fxDiffers) otherDiffs.push("FX");

  if (sameRates) {
    const yieldSign = s0.rates_bp > 0 ? "+" : "";
    if (otherDiffs.length > 0) {
      return `Shared rates move (${yieldSign}${s0.rates_bp}bp) produces an identical ${usd(c0.by_factor.rates_pnl)} rates contribution in both scenarios, but diverging ${formatFactorList(otherDiffs)} assumptions result in ${usd(c0.total_pnl_usd)} under ${title0} versus ${usd(c1.total_pnl_usd)} under ${title1}.`;
    }
    return `Both scenarios share identical factor assumptions (${yieldSign}${s0.rates_bp}bp yield move), producing ${usd(c0.total_pnl_usd)} under both ${title0} and ${title1}.`;
  }

  const y0Sign = s0.rates_bp > 0 ? "+" : "";
  const y1Sign = s1.rates_bp > 0 ? "+" : "";
  if (otherDiffs.length > 0) {
    return `Accepted yield assumptions differ (${y0Sign}${s0.rates_bp}bp versus ${y1Sign}${s1.rates_bp}bp) alongside differing ${formatFactorList(otherDiffs)} assumptions, producing ${usd(c0.total_pnl_usd)} under ${title0} versus ${usd(c1.total_pnl_usd)} under ${title1}.`;
  }
  return `Accepted yield assumptions differ (${y0Sign}${s0.rates_bp}bp versus ${y1Sign}${s1.rates_bp}bp) with identical non-rate assumptions, producing ${usd(c0.total_pnl_usd)} under ${title0} versus ${usd(c1.total_pnl_usd)} under ${title1}.`;
}

export function CausalExploration({
  state,
  setState,
  data,
  generate,
  calculate,
  useShocks,
  selectedEventId,
  onSelectEvent,
}: {
  state: CausalState;
  setState: Dispatch<SetStateAction<CausalState>>;
  data: Workstation;
  generate: (request: CausalRequest) => Promise<CausalResult>;
  calculate: (shocks: Shocks) => Promise<Calculation>;
  useShocks: (shocks: Shocks) => void;
  selectedEventId?: string;
  onSelectEvent?: (id: string) => void;
}) {
  const inFlight = useRef(false);
  const result = state.result;
  const demo = data.causal_mode === "demo";
  const locked = state.busy || state.calculating;
  const validDrafts = state.drafts.length === 2 && state.drafts.every(shocks => factors.every(([key, , , min, max]) => Number.isFinite(shocks[key]) && shocks[key] >= min && shocks[key] <= max));

  useEffect(() => {
    if (state.calculations.length === 2) {
      document.getElementById("causal-comparison")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [state.calculations.length]);

  async function explore() {
    if (inFlight.current || locked) return;
    try {
      const request = causalRequest(state, data.causal_mode);
      inFlight.current = true;
      // Retain earlier answers only until a new generation explicitly starts.
      setState(s => ({ ...s, busy: true, error: "", result: null, drafts: [], calculations: [] }));
      const result = await generate(request);
      setState(s => acceptProposals(s, result));
    } catch (e) {
      setState(s => ({ ...s, busy: false, error: (e as Error).message }));
    } finally { inFlight.current = false; }
  }

  async function calculatePair() {
    if (inFlight.current || locked || state.drafts.length !== 2) return;
    inFlight.current = true;
    const accepted = state.drafts.map(s => ({ ...s }));
    setState(s => ({ ...s, calculating: true, calculations: [], error: "" }));
    try {
      const results = await Promise.all(accepted.map(calculate));
      setState(s => ({ ...s, calculating: false, calculations: results }));
    } catch (e) {
      setState(s => ({ ...s, calculating: false, error: (e as Error).message }));
    } finally { inFlight.current = false; }
  }

  return (
    <section className="causal-exploration">
      <section className="hypothetical-scenarios-section" id="hypothetical-causal-scenarios" aria-label="Hypothetical stress scenarios">
        <div className="causal-intro">
          <span className="eyebrow">{demo ? "DETERMINISTIC DEMO · TEMPLATE HYPOTHESES" : "META-POWERED ECONOMIC EXPLORATION"}</span>
          <h2>One market movement. Different possible explanations.</h2>
          <p>Explore how competing economic mechanisms could lead to different portfolio outcomes. AI proposes mechanisms and editable assumptions; Metis calculates the deterministic consequences after your review.</p>
        </div>

        <nav className="causal-stages" aria-label="Workflow stages">
          <div className={`causal-stage-step ${!result ? "current" : "completed"}`}>
            <span className="stage-badge">1</span>
            <div className="stage-content">
              <span className="stage-title">Compare hypotheses</span>
              <span className="stage-hint">AI proposes mechanisms</span>
            </div>
          </div>
          <span className="stage-divider" aria-hidden="true">→</span>
          <div className={`causal-stage-step ${result && state.calculations.length !== 2 ? "current" : state.calculations.length === 2 ? "completed" : ""}`}>
            <span className="stage-badge">2</span>
            <div className="stage-content">
              <span className="stage-title">Review assumptions</span>
              <span className="stage-hint">Editable proposal shocks</span>
            </div>
          </div>
          <span className="stage-divider" aria-hidden="true">→</span>
          <div className={`causal-stage-step ${state.calculations.length === 2 ? "current" : ""}`}>
            <span className="stage-badge">3</span>
            <div className="stage-content">
              <span className="stage-title">Compare P&amp;L</span>
              <span className="stage-hint">Deterministic engine</span>
            </div>
          </div>
        </nav>

        <div className="notice">
          <span><b>Explore possible causes, not the true cause.</b> Correlation does not establish causation. Two hypotheses share an initial hypothetical yield move; their other factor assumptions may differ.</span>
        </div>
        <p className="context-note">Supplied facts: {data.positions.length} synthetic positions · dated market snapshot {data.market.as_of}. No live market-data feed.</p>

        {data.event_snapshots && <label>Event snapshot reference (optional)
          <select value={state.eventSnapshotId ?? ''} disabled={locked}
            onChange={e => {
              const val = e.target.value || undefined;
              setState(s => ({ ...s, eventSnapshotId: val }));
              if (val) onSelectEvent?.(val);
            }}>
            <option value="">Archived scenario only</option>
            {data.event_snapshots.map(s => <option key={s.id} value={s.id}>{s.start} → {s.end} · {s.title}</option>)}
          </select>
          <p className="context-note">Reference only: reconstructed values and assumed shocks do not establish historical causes. Accepted scenario calculations below still use archived synthetic basket holdings; they do not revalue the event snapshot.</p>
        </label>}

        <div className="causal-inputs">
          {(["hypothesis", "alternative"] as const).map((key, index) => <label key={key}>
            {index === 0 ? "Economic hypothesis A" : "Competing hypothesis B"}
            {demo ? <select value={demoHypotheses.includes(state[key]) ? state[key] : ""} disabled={locked}
              onChange={e => setState(s => ({ ...s, [key]: e.target.value }))}>
              {!demoHypotheses.includes(state[key]) && <option value="" disabled>Choose a demo hypothesis</option>}
              {demoHypotheses.map(h => <option value={h} key={h}>{h}</option>)}
            </select> : <input list="causal-hypotheses" maxLength={600} value={state[key]} disabled={locked}
              onChange={e => setState(s => ({ ...s, [key]: e.target.value }))} />}
          </label>)}
          {!demo && <datalist id="causal-hypotheses">{demoHypotheses.map(h => <option value={h} key={h} />)}</datalist>}
          <label>Shared government-yield move · bp
            <input type="number" min={-300} max={300} step="any" value={Number.isNaN(state.commonRates) ? "" : state.commonRates} disabled={locked}
              onChange={e => setState(s => ({ ...s, commonRates: e.target.valueAsNumber }))} />
          </label>
        </div>
        <p className="context-note">{demo ? "Demo supports only the three named hypotheses. Custom hypotheses require live Meta mode." : "Choose a suggested hypothesis or type your own."} The shared move is an assumption, not a real-time observation. Editing these inputs changes only the next request; existing results retain their captured hypotheses.</p>
        <button className="primary" disabled={locked} onClick={() => void explore()}>{state.busy ? "Exploring hypotheses…" : "Generate competing mechanisms"}</button>
        {state.error && <p role="alert" className="negative">{state.error}</p>}

        {result && <>
          <div className="causal-result-header">
            <p className="context-note">Causal narratives are Not checked by the bounded financial claim verifier. Accepted shock consequences are calculated separately below.</p>
            <span className={result.mode === "demo" ? "badge amber" : "badge"}>{result.mode === "demo" ? "DETERMINISTIC DEMO" : `LIVE META · ${result.model}`}</span>
            <p><b>Captured comparison:</b> {result.request.hypothesis} versus {result.request.alternative} · shared government yields {result.request.common_rates_bp}bp.</p>
            {result.context?.event_reference && <p>Captured event reference: {result.context.event_reference.start} → {result.context.event_reference.end}. {result.context.event_reference.causal_use}</p>}
          </div>

          {state.calculations.length === 2 && <section className="causal-comparison" id="causal-comparison" aria-label="Accepted scenario comparison">
            <span className="eyebrow">ACCEPTED ASSUMPTIONS · CALCULATED BY METIS</span>
            <h2>{state.calculations[0].shocks.rates_bp === state.calculations[1].shocks.rates_bp
              ? "Same yield move. Different portfolio outcomes."
              : "Different yield assumptions. Compare the outcomes."}</h2>
            <p className="causal-comparison-explanation">
              {comparisonSummary(
                state.calculations[0],
                state.calculations[1],
                result.exploration.mechanisms[0].title,
                result.exploration.mechanisms[1].title,
              )}
            </p>
            <p className="context-note">These are hypothetical portfolio results from the accepted shocks, not predictions or identified causes. The model generated possible mechanisms; Metis calculated the numbers.</p>
            <div className="causal-comparison-grid">
              {state.calculations.map((calc, i) => <article className="causal-comparison-card" key={i}>
                <span className="eyebrow">HYPOTHESIS {i === 0 ? "A" : "B"}</span>
                <h3>{result.exploration.mechanisms[i].title}</h3>
                <strong className={pnlTone(calc.total_pnl_usd)}>{usd(calc.total_pnl_usd)}</strong>
                <span className="context-note">Calculated portfolio P&amp;L</span>
                <dl>
                  <div><dt>Government yields</dt><dd>{calc.shocks.rates_bp > 0 ? "+" : ""}{calc.shocks.rates_bp}bp</dd></div>
                  {([
                    ["Rates", "rates_pnl"],
                    ["Credit spreads", "credit_pnl"],
                    ["Equities", "equity_pnl"],
                    ["FX", "fx_pnl"],
                  ] as const).map(([name, key]) => <div key={key}>
                    <dt>{name} contribution</dt><dd className={pnlTone(calc.by_factor[key])}>{usd(calc.by_factor[key])}</dd>
                  </div>)}
                </dl>
                <button className="text-button" onClick={() => useShocks({ ...calc.shocks })}>
                  Use accepted {i === 0 ? "A" : "B"} shocks in Risk Sensitivity Analysis
                </button>
              </article>)}
            </div>
          </section>}

          <div className="causal-pair">
            {result.exploration.mechanisms.map((m, i) => <article className="causal-card" key={i}>
              <span className="eyebrow">{i === 0 ? "A" : "B"} · CAUSAL HYPOTHESIS</span>
              <h2>{m.title}</h2>
              <p className="causal-mechanism-summary">{mechanismSummary(m.economic_mechanism)}</p>

              <details className="answer-section causal-review-assumptions" open>
                <summary>Review scenario assumptions (5 factors)</summary>
                <p className="context-note">{m.assumption_note} Editable values below are scenario assumptions; changes do not rewrite the model's original directional explanation.</p>
                <div className="causal-shocks">{factors.map(([key, label, unit, min, max]) => <label key={key}>
                  {label} · {unit}<small>{min} to +{max}{unit}</small><input aria-label={`${i === 0 ? "A" : "B"} ${label} ${unit}`} type="number" min={min} max={max} step="any" disabled={locked}
                    value={Number.isNaN(state.drafts[i][key]) ? "" : state.drafts[i][key]}
                    onChange={e => setState(s => editAssumption(s, i, key, e.target.valueAsNumber))} />
                </label>)}</div>
              </details>

              <details className="answer-section">
                <summary>Full economic mechanism</summary>
                <p>{m.economic_mechanism}</p>
              </details>

              <details className="answer-section">
                <summary>Proposed cross-asset relationships</summary>
                {factors.map(([key, label]) => <p key={key}><b>{label}: {m.cross_asset[key].direction}</b> — {m.cross_asset[key].rationale}</p>)}
              </details>

              <details className="answer-section">
                <summary>Alternative explanations &amp; discriminating evidence</summary>
                <h3>Other possible mechanisms</h3><ul>{m.alternative_explanations.map((text, j) => <li key={j}>{text}</li>)}</ul>
                <h3>Evidence to obtain</h3><ul>{m.discriminating_evidence.map((text, j) => <li key={j}>{text}</li>)}</ul>
              </details>

              <details className="answer-section">
                <summary>Uncertainty &amp; evidence references</summary>
                <ul>{m.uncertainty.map((text, j) => <li key={j}>{text}</li>)}</ul><p>{m.evidence_references.map(ref => `[${ref}]`).join(" ")}</p>
              </details>

              {state.calculations[i] && <div className="causal-calculation">
                <h3>{i === 0 ? "A" : "B"} · Calculated consequences · accepted assumptions</h3>
                <details className="answer-section">
                  <summary>Position &amp; factor breakdown ({i === 0 ? "A" : "B"})</summary>
                  <FactorEvidence calculation={state.calculations[i]} />
                  <PositionEvidence calculation={state.calculations[i]} exposures={result.context.portfolio.exposures} />
                </details>
                <button className="text-button" onClick={() => useShocks({ ...state.calculations[i].shocks })}>
                  Use accepted {i === 0 ? "A" : "B"} shocks in Risk Sensitivity Analysis
                </button>
              </div>}
            </article>)}
          </div>

          {state.drafts.length === 2 && state.drafts[0].rates_bp !== state.drafts[1].rates_bp && (
            <p className="notice">Edited yield assumptions differ. This comparison no longer holds the initial rate movement constant.</p>
          )}
          {!validDrafts && <p role="alert" className="negative">Enter all five assumptions within the displayed input bounds before calculating.</p>}
          <button className="primary" disabled={locked || !validDrafts} onClick={() => void calculatePair()}>
            {state.calculating ? "Calculating…" : "Accept reviewed shocks & calculate both"}
          </button>
          <p className="context-note">Only this action invokes the existing scenario engine. Editing an assumption clears both previous results. Model directions and magnitudes are hypotheses; P&L is a deterministic consequence of the accepted inputs, not a forecast. Neither result identifies the actual economic cause.</p>

          <details className="answer-section">
            <summary>Supplied facts &amp; original historical sources</summary>
            <p>Synthetic portfolio and dated market snapshot: {result.context.market.as_of}. These facts are separate from the proposed causal relationships and hypothetical shared yield move. Historical sources provide qualitative context, not calibrated causal estimates.</p>
            {result.context.evidence.map(e => <p key={e.id}>{e.url ? <a href={e.url} target="_blank" rel="noreferrer">[{e.id}] {e.description} ↗</a> : `[${e.id}] ${e.description}`}</p>)}
            <details><summary>Inspect supplied context</summary><pre>{JSON.stringify(result.context, null, 2)}</pre></details>
          </details>
        </>}
      </section>

      {data.event_snapshots && data.event_snapshots.length > 0 && (
        <details className="answer-section historical-replay-details" aria-label="Historical event replay">
          <summary>
            Historical event replay · <span className="eyebrow">HISTORICAL REPLAY · RECONSTRUCTED MARKET EVENTS</span>
          </summary>
          <p className="context-note">
            Reconstruct illustrative portfolio outcomes for past market events using observed prices and frozen parameters. Historical replay references reconstruct a different valuation basis than the archived synthetic sensitivity basket used by the causal scenario engine.
          </p>
          <EventSnapshots
            snapshots={data.event_snapshots}
            selectedId={selectedEventId}
            onSelect={onSelectEvent}
            onExplore={(id) => {
              onSelectEvent?.(id);
              setState((s) => ({ ...s, eventSnapshotId: id }));
              document.getElementById("hypothetical-causal-scenarios")?.scrollIntoView({ behavior: "smooth" });
            }}
          />
        </details>
      )}

      <details className="answer-section historical-library">
        <summary>Historical reference library</summary>
        <p className="context-note">Historical facts + explicitly labeled portfolio interpretations</p>
        <EpisodeCards episodes={data.history ?? []} />
      </details>
    </section>
  );
}
