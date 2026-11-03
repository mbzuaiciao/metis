import type { Reasoning } from "./types";
import { scopeLabel } from "./investigation";
import { ShockEvidence } from "./InvestigationEvidence";

export function InvestigationScope({ answer, label }: { answer: Reasoning; label: string }) {
  const calculation = answer.investigation_scope === "daily" ? answer.context.daily : answer.context.scenario;
  return <section className="captured-evidence" aria-label={label}>
    <p><b>{label}: {scopeLabel(answer)}</b></p>
    <p className="context-note">Captured portfolio: {answer.context.portfolio.portfolio_name} · {answer.context.historical ? "synthetic reference NAV" : "NAV"} {answer.context.portfolio.nav_usd.toLocaleString("en-US", {style: "currency", currency: "USD", maximumFractionDigits: 0})}. Current scenario controls do not change this investigation.</p>
    {answer.context.historical
      ? <p className="context-note">Partial-factor proxy assumptions: 10Y parallel rates +{calculation.shocks.rates_bp}bp; both equity baskets {calculation.shocks.equity_pct}%; EUR/USD {calculation.shocks.fx_pct}%. IG/HY spreads and spread P&amp;L unavailable; zero engine placeholders omit their contributions.</p>
      : <ShockEvidence calculation={calculation} />}
  </section>;
}
