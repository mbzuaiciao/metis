import { useRef } from "react";
import type { Dispatch, SetStateAction } from "react";
import type { Calculation, CausalRequest, CausalResult, Shocks, Workstation } from "./types";
import { acceptProposals, causalRequest, editAssumption, type CausalState } from "./causal";
import { FactorEvidence, PositionEvidence } from "./InvestigationEvidence";

const factors: [keyof Shocks, string, string, number, number][] = [
  ["rates_bp", "Government yields", "bp", -300, 300],
  ["ig_bp", "IG spreads", "bp", -300, 500],
  ["hy_bp", "HY spreads", "bp", -500, 1500],
  ["equity_pct", "Equities", "%", -60, 60],
  ["fx_pct", "EUR/USD", "%", -30, 30],
];
const hypotheses = ["Recession fears", "Inflation relief", "Liquidity and funding stress"];

export function CausalExploration({ state, setState, data, generate, calculate, useShocks }: {
  state: CausalState;
  setState: Dispatch<SetStateAction<CausalState>>;
  data: Workstation;
  generate: (request: CausalRequest) => Promise<CausalResult>;
  calculate: (shocks: Shocks) => Promise<Calculation>;
  useShocks: (shocks: Shocks) => void;
}) {
  const inFlight = useRef(false);
  const result = state.result;
  const locked = state.busy || state.calculating;
  const validDrafts = state.drafts.length === 2 && state.drafts.every(shocks => factors.every(([key, , , min, max]) => Number.isFinite(shocks[key]) && shocks[key] >= min && shocks[key] <= max));
  async function explore() {
    if (inFlight.current || locked) return;
    try {
      const request = causalRequest(state);
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
  return <section className="causal-exploration">
    <div className="notice"><span><b>Explore possible causes, not the true cause.</b> Correlation does not establish causation. Two hypotheses share an initial hypothetical yield move; their other factor assumptions may differ.</span></div>
    <p className="context-note">Supplied facts: {data.positions.length} synthetic positions · dated market snapshot {data.market.as_of}. No live market-data feed.</p>
    <div className="causal-inputs">
      {(["hypothesis", "alternative"] as const).map((key, index) => <label key={key}>
        {index === 0 ? "Economic hypothesis A" : "Competing hypothesis B"}
        <input list="causal-hypotheses" maxLength={600} value={state[key]} disabled={locked}
          onChange={e => setState(s => ({ ...s, [key]: e.target.value }))} />
      </label>)}
      <datalist id="causal-hypotheses">{hypotheses.map(h => <option value={h} key={h} />)}</datalist>
      <label>Shared government-yield move · bp
        <input type="number" min={-300} max={300} step="any" value={Number.isNaN(state.commonRates) ? "" : state.commonRates} disabled={locked}
          onChange={e => setState(s => ({ ...s, commonRates: e.target.valueAsNumber }))} />
      </label>
    </div>
    <p className="context-note">Choose a suggested hypothesis or type your own. The shared move is an assumption, not a real-time observation. Editing these inputs changes only the next request; existing results retain their captured hypotheses.</p>
    <button className="primary" disabled={locked} onClick={() => void explore()}>{state.busy ? "Exploring hypotheses…" : "Generate competing mechanisms"}</button>
    {state.error && <p role="alert" className="negative">{state.error}</p>}
    {result && <>
      <div className="causal-result-header">
        <p className="context-note">Causal narratives are Not checked by the bounded financial claim verifier. Accepted shock consequences are calculated separately below.</p>
        <span className={result.mode === "demo" ? "badge amber" : "badge"}>{result.mode === "demo" ? "DETERMINISTIC DEMO" : `LIVE META · ${result.model}`}</span>
        <p><b>Captured comparison:</b> {result.request.hypothesis} versus {result.request.alternative} · shared government yields {result.request.common_rates_bp}bp.</p>
      </div>
      <details className="answer-section"><summary>Supplied facts & original historical sources</summary>
        <p>Synthetic portfolio and dated market snapshot: {result.context.market.as_of}. These facts are separate from the proposed causal relationships and hypothetical shared yield move. Historical sources provide qualitative context, not calibrated causal estimates.</p>
        {result.context.evidence.map(e => <p key={e.id}>{e.url ? <a href={e.url} target="_blank" rel="noreferrer">[{e.id}] {e.description} ↗</a> : `[${e.id}] ${e.description}`}</p>)}
        <details><summary>Inspect supplied context</summary><pre>{JSON.stringify(result.context, null, 2)}</pre></details>
      </details>
      <div className="causal-pair">
        {result.exploration.mechanisms.map((m, i) => <article className="causal-card" key={i}>
          <span className="eyebrow">{i === 0 ? "A" : "B"} · CAUSAL HYPOTHESIS</span>
          <h2>{m.title}</h2><p>{m.economic_mechanism}</p>
          <details className="answer-section" open><summary>Proposed cross-asset relationships</summary>
            {factors.map(([key, label]) => <p key={key}><b>{label}: {m.cross_asset[key].direction}</b> — {m.cross_asset[key].rationale}</p>)}
          </details>
          <details className="answer-section"><summary>Alternative explanations & discriminating evidence</summary>
            <h3>Other possible mechanisms</h3><ul>{m.alternative_explanations.map((text, j) => <li key={j}>{text}</li>)}</ul>
            <h3>Evidence to obtain</h3><ul>{m.discriminating_evidence.map((text, j) => <li key={j}>{text}</li>)}</ul>
          </details>
          <details className="answer-section"><summary>Uncertainty & evidence references</summary>
            <ul>{m.uncertainty.map((text, j) => <li key={j}>{text}</li>)}</ul><p>{m.evidence_references.map(ref => `[${ref}]`).join(" ")}</p>
          </details>
          <h3>Review scenario assumptions</h3>
          <p className="context-note">{m.assumption_note} Editable values below are scenario assumptions; changes do not rewrite the model's original directional explanation.</p>
          <div className="causal-shocks">{factors.map(([key, label, unit, min, max]) => <label key={key}>
            {label} · {unit}<small>{min} to +{max}{unit}</small><input aria-label={`${i === 0 ? "A" : "B"} ${label} ${unit}`} type="number" min={min} max={max} step="any" disabled={locked}
              value={Number.isNaN(state.drafts[i][key]) ? "" : state.drafts[i][key]}
              onChange={e => setState(s => editAssumption(s, i, key, e.target.valueAsNumber))} />
          </label>)}</div>
          {state.calculations[i] && <div className="causal-calculation">
            <h3>{i === 0 ? "A" : "B"} · Calculated consequences · accepted assumptions</h3>
            <FactorEvidence calculation={state.calculations[i]} />
            <PositionEvidence calculation={state.calculations[i]} exposures={result.context.portfolio.exposures} />
            <button className="text-button" onClick={() => useShocks({ ...state.calculations[i].shocks })}>Use accepted {i === 0 ? "A" : "B"} shocks in Independent Shocks</button>
          </div>}
        </article>)}
      </div>
      {state.drafts[0].rates_bp !== state.drafts[1].rates_bp && <p className="notice">Edited yield assumptions differ. This comparison no longer holds the initial rate movement constant.</p>}
      {!validDrafts && <p role="alert" className="negative">Enter all five assumptions within the displayed input bounds before calculating.</p>}
      <button className="primary" disabled={locked || !validDrafts} onClick={() => void calculatePair()}>{state.calculating ? "Calculating…" : "Accept reviewed shocks & calculate both"}</button>
      <p className="context-note">Only this action invokes the existing scenario engine. Editing an assumption clears both previous results. Model directions and magnitudes are hypotheses; P&L is a deterministic consequence of the accepted inputs, not a forecast. Neither result identifies the actual economic cause.</p>
    </>}
  </section>;
}
