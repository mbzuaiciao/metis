import type { Reasoning } from "./types";
import { ClaimVerification } from "./ClaimVerification";
import { FactorEvidence, PositionEvidence } from "./InvestigationEvidence";
import { InvestigationScope } from "./InvestigationScope";

const usd = (value: number) => new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD", maximumFractionDigits: 0,
}).format(value);
const factorNames: Record<string, string> = {
  rates_pnl: "government rates", credit_pnl: "credit spreads", equity_pnl: "equities", fx_pnl: "FX",
};

export function InvestigationResults({ answer, investigationId, presentation = "full" }: { answer: Reasoning; investigationId?: string; presentation?: "focused" | "full" }) {
  const historical = answer.context.historical;
  const creditIncluded = historical?.credit_spreads_included === true;
  const daily = answer.investigation_scope === "daily";
  const calculation = daily ? answer.context.daily : answer.context.scenario;
  const interpretation = answer.interpretation;
  const hypotheses = interpretation.hypotheses ?? [];
  const factors = Object.entries(calculation.by_factor).filter(([, value]) => value !== 0)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
  return <div className="investigation-results">
    <section className="investigation-step question-answer" aria-label="Answer to your question">
      <h2>{answer.question}</h2>
      <p className="context-note">{answer.mode === "demo"
        ? "Deterministic demo answer · template content, not a live model response."
        : "Model answer · original prose Not checked. Structured assertion checks are in supporting evidence."}</p>
      <p className="answer-summary">{interpretation.summary}</p>
      <ul>{interpretation.principal_risk_observations.map((text, i) => <li key={i}>{text}</li>)}</ul>
    </section>
    <p className="context-note"><b>{historical ? `Historical investigation · ${answer.context.market.as_of} · US inflation surprise` : daily
      ? `Daily investigation · fictional synthetic snapshot · ${answer.context.market.as_of}`
      : "Hypothetical stress investigation · simulated assumptions, not historical observations or a forecast"}</b></p>
    {presentation === "full" && <>
    <section className="investigation-step">
      <h2>1 · What happened?</h2>
      <p className="answer-summary">{historical ? "Under historical proxy mappings, the synthetic portfolio" : daily ? "The synthetic daily portfolio" : "Under the captured hypothetical assumptions, the portfolio"}{" "}
        {calculation.total_pnl_usd < 0 ? "lost" : calculation.total_pnl_usd > 0 ? "gained" : "had unchanged P&L of"}{" "}
        {usd(Math.abs(calculation.total_pnl_usd))}{historical ? creditIncluded ? " in estimated hypothetical P&L across all four modeled factors, using historical movements and index proxies." : " across included factors; the complete historical total is unknown." : "."}</p>
      <p>Calculated contributions: {factors.length ? factors.map(([key, value]) =>
        `${factorNames[key] ?? key} ${value > 0 ? "+" : ""}${usd(value)}`).join("; ") : "all factors were unchanged"}.</p>
      {historical && <>
        <p><b>Historical observations:</b> 10Y Treasury {historical.observations.ust10.previous_yield_pct}% → {historical.observations.ust10.current_yield_pct}% (+{calculation.shocks.rates_bp}bp);
          2Y Treasury {historical.observations.ust2.previous_yield_pct}% → {historical.observations.ust2.current_yield_pct}% (+{((historical.observations.ust2.current_yield_pct - historical.observations.ust2.previous_yield_pct) * 100).toFixed(2)}bp);
          S&amp;P 500 {historical.observations.sp500.reported_return_pct}%; EUR/USD {historical.observations.eurusd.reported_return_pct}% (dollar strengthened).</p>
        {creditIncluded && <p><b>Credit index observations:</b> IG OAS {historical.observations.ig_spread?.previous_spread_bp} → {historical.observations.ig_spread?.current_spread_bp}bp ({historical.observations.ig_spread?.change_bp}bp);
          HY OAS {historical.observations.hy_spread?.previous_spread_bp} → {historical.observations.hy_spread?.current_spread_bp}bp (+{historical.observations.hy_spread?.change_bp}bp).
          {" "}<a href={historical.sources.ig_oas?.url} target="_blank" rel="noreferrer">[IG source] ↗</a>{" "}
          <a href={historical.sources.hy_oas?.url} target="_blank" rel="noreferrer">[HY source] ↗</a></p>}
        {answer.context.macro_context?.facts.map((fact, i) => <p key={i}>{fact.text} <a href={historical.sources[fact.source]?.url} target="_blank" rel="noreferrer">[{fact.source}] ↗</a></p>)}
        <p className="context-note"><b>Data limitations:</b> {creditIncluded ? "Aggregate US index OAS proxies cover all four modeled credit baskets; European spread moves are not observed. This is not an exact historical portfolio valuation." : "IG/HY spread changes and credit-spread P&L are unavailable, not unchanged."} Bond/FX quotes are asynchronous; exact FX prior level and quote clocks are unavailable. Current synthetic holdings are not historical positions.</p>
        <details><summary>Proxy mappings and historical source details</summary>
          <ul>{historical.mapping_assumptions.map((text, i) => <li key={i}>{text}</li>)}</ul>
          {Object.entries(historical.sources).map(([key, source]) => <p key={key}><a href={source.url} target="_blank" rel="noreferrer">{source.description} ↗</a></p>)}
        </details>
      </>}
    </section>
    <section className="investigation-step hypothesis-section">
      <h2>2 · What might explain it?</h2>
      <p className="context-note">Competing economic hypotheses · consistency with P&L does not verify an explanation.
        The supplied {historical ? "historical observations and macro context" : daily ? "synthetic observations" : "scenario assumptions"} alone cannot distinguish these mechanisms or identify a cause.</p>
      {answer.mode === "demo" && <p className="context-note">Deterministic demonstration templates, not model-selected findings. Check their fit to this investigation.</p>}
      {hypotheses.length === 0 && <p>No structured competing hypotheses were returned for this answer. The original economic interpretation remains in supporting evidence; start a new investigation for the three-question format.</p>}
      {hypotheses.length > 0 && <div className="hypothesis-comparison" aria-label="Competing hypothesis comparison">
        {hypotheses.map((hypothesis, index) => <article className="economic-hypothesis" key={index}>
          <h3>Hypothesis {String.fromCharCode(65 + index)} · {hypothesis.title}</h3>
          <p><b>Proposed mechanism</b></p>
          <p>{hypothesis.mechanism}</p>
          <p><b>{historical ? "Consistent historical observations" : daily ? "Consistent synthetic observations" : "Consistent scenario assumptions"}</b></p>
          <p>{hypothesis.consistent_evidence}</p>
          {hypothesis.portfolio_implications && <><p><b>Portfolio implications</b></p><p>{hypothesis.portfolio_implications}</p></>}
          <p><b>Unknown or not established</b></p>
          <p>{hypothesis.uncertainty}</p>
        </article>)}
      </div>}
    </section>
    <section className="investigation-step" id={investigationId}>
      <h2>3 · How can we investigate?</h2>
      <p className="context-note">Proposed checks, not completed analyses. Additional data listed below are not supplied by Metis.</p>
      {hypotheses.length === 0 && <p>Inspect the captured inputs and original model uncertainties in supporting evidence to identify missing data.</p>}
      {hypotheses.map((hypothesis, index) => <article className="investigation-plan" key={index}>
        <h3>Investigate hypothesis {String.fromCharCode(65 + index)} · {hypothesis.title}</h3>
        <p><b>Available in Metis · proposed check:</b> {hypothesis.available_checks}</p>
        <p><b>Requires additional data:</b> {hypothesis.additional_evidence}</p>
      </article>)}
    </section>
    </>}
    <details className="answer-section investigation-support">
      <summary>Supporting evidence and details · calculations, verification and model limitations</summary>
      <InvestigationScope answer={answer} label="Answer scope" />
      <details className="answer-section">
        <summary>Detailed numerical claims and factor attribution</summary>
        <FactorEvidence hypothetical={!!historical} calculation={calculation} omittedCredit={!!historical && !creditIncluded} />
      </details>
      <PositionEvidence omittedCredit={!!historical && !creditIncluded} calculation={calculation} exposures={answer.context.portfolio.exposures} />
      <details className="answer-section">
        <summary>Structured assertion verification · this investigation · original prose Not checked</summary>
        <ClaimVerification results={answer.verification} />
      </details>
      <details className="answer-section">
        <summary>Model economic interpretation</summary>
        <p>{interpretation.economic_interpretation}</p>
      </details>
      {([
        ["Historical analogies · qualitative context", interpretation.historical_analogies],
        ["Potential portfolio vulnerabilities", interpretation.potential_vulnerabilities],
        ["Model assumptions and limitations", interpretation.assumptions_and_uncertainties],
      ] as [string, string[]][]).map(([title, items]) => <details className="answer-section" key={title}>
        <summary>{title}</summary><ul>{items.map((text, i) => <li key={i}>{text}</li>)}</ul>
      </details>)}
      <details className="answer-section">
        <summary>Evidence references</summary>
        <div className="evidence">{answer.context.evidence.filter(e => interpretation.evidence_references.includes(e.id)).map(e =>
          e.url ? <a href={e.url} key={e.id} target="_blank" rel="noreferrer">[{e.id}] {e.description} ↗</a>
            : <span key={e.id}>[{e.id}] {e.description}</span>)}</div>
      </details>
      <details className="answer-section">
        <summary>Inspect context and backend operations</summary>
        <p>Application assembled this context before invocation. No autonomous tool calls.</p>
        <pre>{JSON.stringify({ operations: answer.context_operations, context: answer.context }, null, 2)}</pre>
      </details>
    </details>
  </div>;
}
