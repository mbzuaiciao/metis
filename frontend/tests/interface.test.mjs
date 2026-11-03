import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { registerHooks } from "node:module";
import ts from "typescript";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { initialCausalState } from "../src/causal.ts";

// Render the actual TSX components using the existing TypeScript dependency.
registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier.startsWith(".") && context.parentURL) {
      for (const extension of [".ts", ".tsx"]) {
        const url = new URL(specifier + extension, context.parentURL);
        if (existsSync(url)) return nextResolve(url.href, context);
      }
    }
    return nextResolve(specifier, context);
  },
  load(url, context, nextLoad) {
    if (/\.tsx?$/.test(url)) return {
      format: "module", shortCircuit: true,
      source: ts.transpileModule(readFileSync(new URL(url), "utf8"), {
        compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
      }).outputText,
    };
    return nextLoad(url, context);
  },
});
const { CausalExploration } = await import("../src/CausalExploration.tsx");
const { ClaimVerification } = await import("../src/ClaimVerification.tsx");

function causalMarkup(mode, state = initialCausalState) {
  return renderToStaticMarkup(React.createElement(CausalExploration, {
    state, setState() {}, data: {causal_mode: mode, positions: [], market: {as_of: "2025-03-10"}},
    generate() { throw new Error("Rendering must not generate"); }, calculate() {}, useShocks() {},
  }));
}

test("Demo renders only named hypothesis selectors; Meta retains free-form inputs", () => {
  const demo = causalMarkup("demo");
  assert.equal((demo.match(/<select/g) || []).length, 2);
  assert.doesNotMatch(demo, /<datalist|type your own|<input list=/);
  assert.match(demo, /Custom hypotheses require live Meta mode/);
  assert.match(demo, /DETERMINISTIC DEMO · TEMPLATE HYPOTHESES/);
  for (const hypothesis of ["Recession fears", "Inflation relief", "Liquidity and funding stress"]) {
    assert.ok(demo.includes(`value="${hypothesis}"`));
  }
  const live = causalMarkup("meta", {...initialCausalState, hypothesis: "Supply normalization"});
  assert.doesNotMatch(live, /<select/);
  assert.equal((live.match(/<input list=/g) || []).length, 2);
  assert.match(live, /value="Supply normalization"/);
  assert.match(live, /type your own/);
  assert.match(live, /META-POWERED ECONOMIC EXPLORATION/);
  assert.match(causalMarkup("demo", {...initialCausalState, hypothesis: "Supply normalization"}), /Choose a demo hypothesis/);
});

test("correct structured mapping never labels deliberately mismatched original prose verified", () => {
  const claim = {statement: "The portfolio made money.", kind: "number", value: -560770};
  const result = {claim, mapping: "Daily snapshot · portfolio · total P&L equals -560,770.00 USD",
    verdict: "Verified", original_wording_status: "Not checked", explanation: "Matches the backend value.", evidence: [], limitations: []};
  const markup = renderToStaticMarkup(React.createElement(ClaimVerification, {results: [result]}));
  assert.match(markup, /do not verify the semantic truth of the original prose/);
  assert.match(markup, /Original prose · Not checked/);
  assert.match(markup, /<blockquote>The portfolio made money\.<\/blockquote>/);
  assert.match(markup, /Structured assertion: Verified/);
  assert.doesNotMatch(markup, /Original prose · Verified/);
  assert.match(markup, /-560,770.00 USD/);
  assert.equal(claim.statement, "The portfolio made money.");
});

test("empty assertions explicitly leave original prose unchecked", () => {
  const markup = renderToStaticMarkup(React.createElement(ClaimVerification));
  assert.match(markup, /No structured assertions were submitted/);
  assert.match(markup, /original prose is Not checked/);
});

const { InvestigationScope } = await import("../src/InvestigationScope.tsx");
test("answer and follow-up labels render captured daily or stress scope and assumptions", () => {
  const shocks = {rates_bp: -50, ig_bp: 75, hy_bp: 250, equity_pct: -15, fx_pct: -5};
  for (const scope of ["daily", "scenario"]) {
    const answer = {investigation_scope: scope, context: {
      market: {as_of: "2025-03-10"}, portfolio: {portfolio_name: "Original portfolio", nav_usd: 100000000},
      daily: {shocks: {...shocks, rates_bp: -8}}, scenario: {shocks},
    }};
    for (const label of ["Answer scope", "Follow-up scope"]) {
      const markup = renderToStaticMarkup(React.createElement(InvestigationScope, {answer, label}));
      assert.match(markup, new RegExp(label));
      assert.match(markup, scope === "daily" ? /Daily snapshot/ : /Captured stress/);
      assert.match(markup, /Original portfolio/);
      assert.match(markup, /2025-03-10/);
      assert.match(markup, /Current scenario controls do not change this investigation/);
      assert.match(markup, scope === "daily" ? /<b>-8<\/b>/ : /<b>-50<\/b>/);
    }
  }
});

const { ResearchLimitations } = await import("../src/ResearchLimitations.tsx");
test("research tab exposes six sourced studies and unresolved boundaries", () => {
  const html = renderToStaticMarkup(React.createElement(ResearchLimitations));
  assert.equal((html.match(/Read the report/g) || []).length, 6);
  assert.match(html, /STUDY 06/);
  assert.match(html, /six were truncated/);
  assert.match(html, /not yet in the committed research archive/);
  assert.match(html, /RESEARCH_LOG\.md/);
  assert.match(html, /Numerical claim checks do not validate entire/);
});
test("research page is the seventh sidebar item and renders without backend data", () => {
  const app = readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
  const ai = app.indexOf('name: "Metis AI Reasoning"');
  const research = app.indexOf('name: "Research & Limitations"');
  assert.ok(ai > 0 && research > ai);
  assert.match(app, /page === 6 \? \(\s*<ResearchLimitations \/>/);
  assert.match(app, /page === 6\s*\? "Documented studies"/);
});

test("accepted causal hypotheses show backend P&L side by side, never before calculation", () => {
  const first = {rates_bp: -50, ig_bp: 75, hy_bp: 250, equity_pct: -15, fx_pct: -5};
  const second = {rates_bp: -50, ig_bp: -20, hy_bp: -50, equity_pct: 8, fx_pct: 2};
  const makeMechanism = (title, shocks) => ({
    title, economic_mechanism: "An illustrative economic mechanism.",
    proposed_shocks: shocks, assumption_note: "Uncalibrated assumptions, not a prediction.",
    cross_asset: Object.fromEntries(Object.keys(shocks).map(key => [key, {direction: "ambiguous", rationale: "Conditional mechanism."}])),
    alternative_explanations: [], discriminating_evidence: [], uncertainty: [], evidence_references: [],
  });
  const state = {
    ...initialCausalState,
    result: {
      mode: "demo", model: null,
      request: {hypothesis: "Recession fears", alternative: "Inflation relief", common_rates_bp: -50},
      context: {market: {as_of: "2025-03-10"}, evidence: [], portfolio: {exposures: {dv01_usd_per_bp: 0, cs01_usd_per_bp: 0}}},
      exploration: {mechanisms: [makeMechanism("Recession fears", first), makeMechanism("Inflation relief", second)]},
    },
    drafts: [first, second],
  };
  const calculation = (shocks, pnl, by_factor) => ({shocks, total_pnl_usd: pnl, by_factor, positions: []});
  const completed = {
    ...state,
    calculations: [
      calculation(first, -3347000, {rates_pnl: 2578000, credit_pnl: -1975000, equity_pnl: -3450000, fx_pnl: -500000}),
      calculation(second, 5070500, {rates_pnl: 2578000, credit_pnl: 452500, equity_pnl: 1840000, fx_pnl: 200000}),
    ],
  };
  const before = causalMarkup("demo", state);
  assert.doesNotMatch(before, /id="causal-comparison"/);
  const after = causalMarkup("demo", completed);
  assert.match(after, /id="causal-comparison"/);
  assert.match(after, /Same yield move\. Different portfolio outcomes/);
  assert.match(after, /-\$3,347,000/);
  assert.match(after, /\$5,070,500/);
  assert.match(after, /Credit spreads contribution/);
  assert.match(after, /DETERMINISTIC DEMO/);
  assert.match(after, /not predictions or identified causes/);
  const unequal = causalMarkup("demo", {
    ...completed,
    calculations: [completed.calculations[0], {...completed.calculations[1], shocks: {...second, rates_bp: -45}}],
  });
  assert.match(unequal, /Different yield assumptions\. Compare the outcomes/);
});

const { InvestigationResults } = await import("../src/InvestigationResults.tsx");
test("three-question results retain scoped backend values and collapse supporting evidence", () => {
  const makeCalculation = (total, rate, equity) => ({total_pnl_usd: total,
    by_factor: {rates_pnl: rate, credit_pnl: 0, equity_pnl: equity, fx_pnl: 0},
    positions: [], shocks: {rates_bp: -8, ig_bp: 18, hy_bp: 45, equity_pct: -2.2, fx_pct: -0.6}});
  for (const scope of ["daily", "scenario"]) {
    const answer = {investigation_scope: scope, mode: "demo", context_operations: [],
      context: {market: {as_of: "2025-03-10"}, portfolio: {portfolio_name: "Captured", nav_usd: 100000000, exposures: {dv01_usd_per_bp: 0, cs01_usd_per_bp: 0}},
        daily: makeCalculation(-123, 100, -223), scenario: makeCalculation(456, 500, -44), evidence: []},
      interpretation: {summary: "Full original summary", economic_interpretation: "Original economic text",
        principal_risk_observations: ["Original numerical claim"], historical_analogies: ["Historical analogy"],
        potential_vulnerabilities: ["Funding concern"], assumptions_and_uncertainties: ["Linear model"], evidence_references: [],
        hypotheses: ["Growth", "Liquidity"].map(title => ({title, mechanism: `${title} mechanism`,
          consistent_evidence: "Captured moves", uncertainty: "Cause unknown", available_checks: "Inspect the captured signs",
          additional_evidence: "Obtain new data"}))}};
    const original = structuredClone(answer);
    const html = renderToStaticMarkup(React.createElement(InvestigationResults, {answer}));
    const first = html.indexOf("1 · What happened?");
    const second = html.indexOf("2 · What might explain it?");
    const third = html.indexOf("3 · How can we investigate?");
    const details = html.indexOf('<details');
    assert.ok(first < second && second < third && third < details);
    assert.match(html, scope === "daily" ? /lost \$123/ : /gained \$456/);
    assert.match(html, scope === "daily" ? /synthetic observed snapshot/ : /simulated assumptions, not historical observations/);
    assert.match(html, /Hypothesis A/);
    assert.match(html, /Hypothesis B/);
    assert.match(html, /cannot distinguish these mechanisms/);
    assert.match(html, /Available in Metis · proposed check/);
    assert.match(html, /Requires additional data/);
    assert.match(html, /Structured assertion verification · this investigation/);
    for (const text of ["Full original summary", "Original economic text", "Original numerical claim", "Historical analogy", "Funding concern", "Linear model"]) assert.ok(html.includes(text));
    assert.doesNotMatch(html, /<details[^>]*\bopen(?:=|>)/);
    assert.deepEqual(answer, original);
  }
});
test("verification demonstrations follow active answers and are labeled separately", () => {
  const app = readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
  assert.ok(app.indexOf("<InvestigationResults") < app.indexOf("<VerificationDemo"));
  assert.match(app, /aria-label="Demonstration examples"/);
});
