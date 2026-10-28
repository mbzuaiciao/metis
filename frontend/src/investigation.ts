import type { Calculation, Reasoning } from "./types";

export type InvestigationFocus = "daily" | "scenario" | "question";
export const dailyQuestion =
  "Explain the illustrative daily portfolio loss. Why did positive government-rate P&L fail to offset credit-spread, equity and FX losses? Identify the important positions and exposures. Separate calculated facts from economic interpretations, and identify vulnerabilities and missing evidence worth investigating. The scenario supplied with this question uses the daily snapshot shocks, not the separately selected stress scenario.";
export const scenarioQuestion =
  "Interpret the selected hypothetical stress scenario. Explain its assumed shocks, factor contributions and total portfolio P&L, distinguish rate gains from spread losses and net position P&L, and identify vulnerabilities and missing evidence worth investigating. Keep this hypothetical result separate from the dated illustrative daily P&L; it is not a forecast.";

export function investigationRequest(
  focus: InvestigationFocus,
  question: string,
  daily: Calculation,
  scenario: Calculation | null,
  messages: Reasoning[],
) {
  const calculation = focus === "daily" ? daily : scenario;
  if (!calculation)
    throw new Error("Wait for the selected scenario to finish calculating.");
  return {
    question: question.trim(),
    shocks: { ...calculation.shocks },
    // Contextual investigations start fresh; only explicit follow-up questions replay history.
    history:
      focus === "question"
        ? messages.slice(-3).flatMap((m) => [
            { role: "user", content: m.question },
            { role: "assistant", content: m.interpretation.summary },
          ])
        : [],
  };
}

export function principalDrivers(calculation: Calculation) {
  const sorted = [...calculation.positions].sort(
    (a, b) => a.pnl_usd - b.pnl_usd,
  );
  return {
    loss: sorted.find((p) => p.pnl_usd < 0),
    gain: sorted
      .slice()
      .reverse()
      .find((p) => p.pnl_usd > 0),
  };
}

// Order supplied factor contributions by measured P&L, without recomputing them.
export function measuredContributions(calculation: Calculation) {
  return Object.entries(calculation.by_factor).sort((a, b) => a[1] - b[1]);
}

// Presentation excerpt only: preserve the original model text in an expandable section.
export function executivePreview(summary: string) {
  if (summary.length <= 480) return summary;
  const boundary = summary.lastIndexOf(" ", 480);
  return summary.slice(0, boundary > 0 ? boundary : 480) + "…";
}

// A reading checklist, not a financial claim classifier or model-output verifier.
export function vulnerabilityGuide(text: string) {
  if (/margin|funding|collateral|counterparty|swap|forward/i.test(text))
    return {
      topic: "Funding & counterparties",
      consequence: "Collateral calls or a counterparty disruption could require cash or constrain the hedge. Exposure size alone does not establish a shortfall.",
      evidence:
        "Signed marks, reference notionals, DV01 and the cash position are available below.",
      missing:
        "Obtain netting and CSA terms, current collateral balances, initial/variation-margin sensitivity, collateral eligibility, net counterparty exposure and available liquidity/funding facilities. Notional and cash alone do not establish a margin shortfall.",
    };
  if (/liquid|bid.ask|execution|\bsell\b|redemption/i.test(text))
    return {
      topic: "Liquidity",
      consequence: "Execution away from modeled marks could deepen losses or delay liquidation. The linear calculation does not estimate these costs.",
      evidence:
        "Position sizes and modeled P&L are available; no executable prices or liquidity measures are supplied.",
      missing:
        "Obtain bid-ask quotes, market depth, liquidation horizons, redemption terms and stressed execution costs before estimating liquidation losses.",
    };
  if (/correlat|divers|equity|equities|inflation|recession/i.test(text))
    return {
      topic: "Joint market moves",
      consequence: "Concurrent credit and equity losses can exceed a positive rates contribution; a different regime could also reverse the rate hedge contribution.",
      evidence:
        "Daily factor moves and the selected joint shocks are assumptions supplied to the linear model, not estimated correlations.",
      missing:
        "Obtain return histories, investment horizons, sector/beta exposures and regime assumptions before assessing diversification or joint-loss probabilities.",
    };
  if (/credit|default|downgrade|spread|\bHY\b/i.test(text))
    return {
      topic: "Credit",
      consequence: "Issuer deterioration or default could produce losses beyond the first-order spread estimate. CS01 does not estimate jump-to-default losses.",
      evidence:
        "Credit positions have separate rate and spread contributions; their net P&L includes both legs.",
      missing:
        "Obtain issuer holdings and concentrations, ratings, maturities, migration/default assumptions and recovery estimates. CS01 does not quantify default jumps.",
    };
  return {
    topic: "Model boundaries",
    consequence: "If the concern is supported, actual losses or cash needs could differ from the modeled result. The supplied linear calculation alone cannot establish that consequence.",
    evidence:
      "Captured sensitivities, factor contributions and net position P&L can be inspected below.",
    missing:
      "Identify the missing inputs needed to test this specific claim: instrument terms, concentration/return histories, or nonlinear, curve/basis and valuation analysis as applicable. A model interpretation is not a quantified loss estimate.",
  };
}
