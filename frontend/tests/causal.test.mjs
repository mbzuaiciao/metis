import test from "node:test";
import assert from "node:assert/strict";
import { acceptProposals, editAssumption, initialCausalState, causalRequest } from "../src/causal.ts";

const shocks = { rates_bp: -50, ig_bp: 75, hy_bp: 250, equity_pct: -15, fx_pct: -5 };
const result = { exploration: { mechanisms: [{ proposed_shocks: shocks }, { proposed_shocks: {...shocks, ig_bp: -20, equity_pct: 8} }] } };

test("generation stages proposals without calculated consequences or input mutation", () => {
  const state = acceptProposals(initialCausalState, result);
  assert.deepEqual(state.calculations, []);
  assert.equal(state.drafts.length, 2);
  state.drafts[0].ig_bp = 100;
  assert.equal(shocks.ig_bp, 75);
});
test("user edits invalidate both results and preserve original model assumptions", () => {
  const state = { ...acceptProposals(initialCausalState, result), calculations: [{ total_pnl_usd: -3347000 }, { total_pnl_usd: 1 }] };
  const edited = editAssumption(state, 0, "equity_pct", -10);
  assert.deepEqual(edited.calculations, []);
  assert.equal(edited.drafts[0].equity_pct, -10);
  assert.equal(state.drafts[0].equity_pct, -15);
  assert.equal(result.exploration.mechanisms[0].proposed_shocks.equity_pct, -15);
  assert.equal(edited.drafts[1].equity_pct, 8);
});
test("comparison captures two distinct hypotheses and a bounded shared move", () => {
  assert.deepEqual(causalRequest(initialCausalState), { hypothesis: "Recession fears", alternative: "Inflation relief", common_rates_bp: -50 });
  assert.throws(() => causalRequest({...initialCausalState, alternative: "Recession fears"}), /different/);
  assert.throws(() => causalRequest({...initialCausalState, commonRates: NaN}), /between/);
  assert.equal(causalRequest({...initialCausalState, alternative: "Supply normalization"}).alternative, "Supply normalization");
});


test("demo rejects custom hypotheses before generation while Meta preserves free-form requests", () => {
  const custom = {...initialCausalState, hypothesis: "Supply normalization"};
  assert.throws(() => causalRequest(custom, "demo"), /three named hypotheses/);
  assert.throws(() => causalRequest({...initialCausalState, alternative: "Supply normalization"}, "demo"), /three named hypotheses/);
  assert.equal(causalRequest(custom, "meta").hypothesis, "Supply normalization");
  for (const hypothesis of ["Recession fears", "Inflation relief", "Liquidity and funding stress"]) {
    const alternative = hypothesis === "Inflation relief" ? "Recession fears" : "Inflation relief";
    assert.equal(causalRequest({...initialCausalState, hypothesis, alternative}, "demo").hypothesis, hypothesis);
  }
});

test("event reference is optional and captured without changing the yield assumption", () => {
  const request = causalRequest({...initialCausalState, eventSnapshotId: 'cpi-2022'});
  assert.equal(request.event_snapshot_id, 'cpi-2022');
  assert.equal(request.common_rates_bp, -50);
  assert.equal(causalRequest(initialCausalState).event_snapshot_id, undefined);
});
