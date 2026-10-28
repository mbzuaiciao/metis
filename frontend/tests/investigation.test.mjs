import test from "node:test";
import assert from "node:assert/strict";
import {
  investigationRequest,
  principalDrivers,
  vulnerabilityGuide,
} from "../src/investigation.ts";

const daily = {
  shocks: {
    rates_bp: -8,
    ig_bp: 18,
    hy_bp: 45,
    equity_pct: -2.2,
    fx_pct: -0.6,
  },
};
const stress = {
  shocks: { rates_bp: -50, ig_bp: 75, hy_bp: 250, equity_pct: -15, fx_pct: -5 },
};
const prior = [
  {
    question: "Earlier question",
    interpretation: { summary: "Earlier interpretation" },
  },
];

test("daily investigation uses the daily snapshot, without changing selected stress or leaking earlier interpretation", () => {
  const selected = structuredClone(stress);
  const request = investigationRequest(
    "daily",
    "Explain the loss",
    daily,
    stress,
    prior,
  );
  assert.deepEqual(request.shocks, daily.shocks);
  assert.deepEqual(request.history, []);
  assert.deepEqual(stress, selected);
  request.shocks.rates_bp = 99;
  assert.equal(daily.shocks.rates_bp, -8);
});
test("scenario request captures current shocks and stays stable after later edits", () => {
  const scenario = structuredClone(stress);
  const request = investigationRequest(
    "scenario",
    "Interpret this stress",
    daily,
    scenario,
    prior,
  );
  scenario.shocks.hy_bp = 500;
  assert.equal(request.shocks.hy_bp, 250);
  assert.deepEqual(request.history, []);
  assert.throws(
    () => investigationRequest("scenario", "Stress?", daily, null, []),
    /finish calculating/,
  );
});
test("only explicit follow-up requests replay bounded conversational history", () => {
  const history = Array.from({ length: 5 }, (_, i) => ({
    question: `Q${i}`,
    interpretation: { summary: `A${i}` },
  }));
  const request = investigationRequest(
    "question",
    " Follow up ",
    daily,
    stress,
    history,
  );
  assert.equal(request.question, "Follow up");
  assert.deepEqual(
    request.history.map((t) => t.content),
    ["Q2", "A2", "Q3", "A3", "Q4", "A4"],
  );
});
test("driver selection uses signed backend net P&L without altering positions", () => {
  const calculation = {
    positions: [
      { id: "A", pnl_usd: -100 },
      { id: "B", pnl_usd: 500 },
      { id: "C", pnl_usd: -300 },
      { id: "D", pnl_usd: 0 },
    ],
  };
  const original = structuredClone(calculation);
  assert.equal(principalDrivers(calculation).loss.id, "C");
  assert.equal(principalDrivers(calculation).gain.id, "B");
  assert.deepEqual(calculation, original);
  assert.equal(
    principalDrivers({ positions: [{ pnl_usd: 0 }] }).loss,
    undefined,
  );
});
test("reading guides distinguish missing evidence without inventing quantified losses", () => {
  assert.match(vulnerabilityGuide("Swap margin calls").missing, /CSA/);
  assert.match(
    vulnerabilityGuide("Liquidity and exit costs").missing,
    /market depth/,
  );
  assert.match(vulnerabilityGuide("Credit defaults").missing, /recovery/);
  assert.match(
    vulnerabilityGuide("Correlation breakdown").missing,
    /return histories/,
  );
  assert.match(
    vulnerabilityGuide("Unspecified vulnerability").missing,
    /not a quantified loss/,
  );
});

test("economic regime wording does not route a rate selloff to an execution checklist", () => {
  assert.equal(
    vulnerabilityGuide("Inflation and credit-spread correlation in a selloff")
      .topic,
    "Joint market moves",
  );
});
