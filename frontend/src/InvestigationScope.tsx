import type { Reasoning } from "./types";
import { scopeLabel } from "./investigation";
import { ShockEvidence } from "./InvestigationEvidence";

export function InvestigationScope({ answer, label }: { answer: Reasoning; label: string }) {
  const calculation = answer.investigation_scope === "daily" ? answer.context.daily : answer.context.scenario;
  return <section className="captured-evidence" aria-label={label}>
    <p><b>{label}: {scopeLabel(answer)}</b></p>
    <p className="context-note">Captured portfolio: {answer.context.portfolio.portfolio_name} · NAV {answer.context.portfolio.nav_usd.toLocaleString("en-US", {style: "currency", currency: "USD", maximumFractionDigits: 0})}. Current scenario controls do not change this investigation.</p>
    <ShockEvidence calculation={calculation} />
  </section>;
}
