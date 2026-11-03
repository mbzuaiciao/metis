import test from "node:test";
import assert from "node:assert/strict";
import {
  executivePreview,
  followupTarget,
  scopeLabel,
  measuredContributions,
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
    investigation_id: "captured-a",
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
function captured(id, scope = "scenario", calculation = stress) {
  return {investigation_id: id, investigation_scope: scope, question: "Original question",
    interpretation: {summary: "Original summary"},
    context: {portfolio: {portfolio_name: "Captured portfolio", nav_usd: 100000000},
      market: {as_of: "2025-03-10"}, daily: structuredClone(daily), scenario: structuredClone(calculation)}};
}

test("daily and stress follow-ups retain their snapshot reference before and after controls change", () => {
  for (const scope of ["daily", "scenario"]) {
    const original = captured("captured-a", scope, scope === "daily" ? daily : stress);
    const unchanged = structuredClone(original);
    const messages = [original];
    const before = investigationRequest("question", "Which positions?", daily, stress, messages);
    const edited = structuredClone(stress);
    edited.shocks.rates_bp = 70;
    const after = investigationRequest("question", "Which positions?", daily, edited, messages);
    assert.deepEqual(after, before);
    assert.equal(after.investigation_id, original.investigation_id);
    assert.equal(after.shocks, undefined); // Only the server-owned snapshot is used.
    assert.deepEqual(investigationRequest("question", "Which positions?", daily, null, messages), before);
    assert.deepEqual(original, unchanged);
    assert.equal(followupTarget(messages), original);
  }
});

test("daily-to-stress and stress-to-daily start fresh; older investigations can still be continued", () => {
  const first = captured("daily-a", "daily", daily);
  const second = captured("stress-a");
  const third = captured("daily-b", "daily", daily);
  const messages = [first, second, third];
  for (const focus of ["scenario", "daily"]) {
    const request = investigationRequest(focus, "Analyze different scope", daily, stress, messages, first.investigation_id);
    assert.deepEqual(request.history, []);
    assert.equal(request.investigation_id, undefined);
    assert.equal(request.investigation_scope, focus);
    assert.deepEqual(request.shocks, (focus === "daily" ? daily : stress).shocks);
  }
  const follow = investigationRequest("question", "Follow up", daily, stress, messages, second.investigation_id);
  assert.equal(follow.investigation_id, second.investigation_id);
  assert.deepEqual(follow.history.map(t => t.content), [second.question, second.interpretation.summary]);
  const repeatedDaily = investigationRequest("question", "Follow up", daily, stress, messages, third.investigation_id);
  assert.equal(repeatedDaily.history.length, 2); // Same shocks do not merge independent investigations.
  assert.equal(followupTarget(messages), third);
  assert.equal(followupTarget(messages, first.investigation_id), first);
  assert.throws(() => investigationRequest("question", "Follow up", daily, stress, messages, "missing"), /available investigation/);
  assert.match(scopeLabel(first), /Daily snapshot.*2025-03-10/);
  assert.match(scopeLabel(second), /Captured stress.*rates -50bp.*HY 250bp/);
});

test("history is bounded within the chosen investigation even when other investigations intervene", () => {
  const messages = Array.from({length: 8}, (_, i) => ({...captured(i % 2 ? "other" : "chosen"), question: `Q${i}`}));
  const request = investigationRequest("question", "Follow up", daily, null, messages, "chosen");
  assert.deepEqual(request.history.filter(t => t.role === "user").map(t => t.content), ["Q2", "Q4", "Q6"]);
  assert.equal(request.history.length, 6);
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

test("executive preview preserves short conclusions and exposes a bounded literal excerpt for verbose output", () => {
  const short = "Rates gained, but equity and credit losses were larger. Collateral needs are unknown.";
  assert.equal(executivePreview(short), short);
  const long = "Model interpretation with evidence [daily]. ".repeat(30);
  const preview = executivePreview(long);
  assert.ok(preview.length <= 481);
  assert.ok(long.startsWith(preview.slice(0, -1)));
  assert.ok(preview.endsWith("…"));
});

test("measured factor ordering prioritizes losses without changing backend amounts or input", () => {
  const calculation = { by_factor: { rates_pnl: 412480, credit_pnl: -407250, equity_pnl: -506000, fx_pnl: -60000 } };
  const original = structuredClone(calculation);
  assert.deepEqual(measuredContributions(calculation), [
    ["equity_pnl", -506000], ["credit_pnl", -407250], ["fx_pnl", -60000], ["rates_pnl", 412480],
  ]);
  assert.deepEqual(calculation, original);
});

test("investigation guides explain conditional consequences without asserting a shortfall or default estimate", () => {
  assert.match(vulnerabilityGuide("Funding").consequence, /does not establish a shortfall/);
  assert.match(vulnerabilityGuide("Credit").consequence, /first-order/);
  assert.match(vulnerabilityGuide("Liquidity").consequence, /does not estimate/);
});

test("historical start is independent of stress controls and follow-up retains historical snapshot", () => {
  const request = investigationRequest("historical", "Explain CPI", daily, null, prior);
  assert.deepEqual(request, {question: "Explain CPI", investigation_scope: "historical", history: []});
  const original = captured("historical-a", "historical");
  original.context.market.as_of = "2022-09-13";
  assert.match(scopeLabel(original), /Historical CPI investigation.*2022-09-13.*partial-factor/);
  assert.equal(investigationRequest("question", "Distinguish them", daily, null, [original]).investigation_id, "historical-a");
});

test("explicit daily date is sent; follow-ups retain their captured date", () => {
  const request = investigationRequest("daily", "Explain", daily, stress, [], null, "2025-03-10");
  assert.equal(request.investigation_date, "2025-03-10");
  const follow = investigationRequest("question", "More", daily, stress, [captured("saved")], null, "2026-10-30");
  assert.equal(follow.investigation_date, undefined);
  assert.equal(follow.investigation_id, "saved");
  const scenario = investigationRequest("scenario", "Stress", daily, stress, [], null, "2025-03-10");
  assert.equal(scenario.investigation_date, undefined);
});
