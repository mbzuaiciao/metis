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
  for (const hypothesis of ["Recession fears", "Inflation relief", "Liquidity and funding stress"]) {
    assert.ok(demo.includes(`value="${hypothesis}"`));
  }
  const live = causalMarkup("meta", {...initialCausalState, hypothesis: "Supply normalization"});
  assert.doesNotMatch(live, /<select/);
  assert.equal((live.match(/<input list=/g) || []).length, 2);
  assert.match(live, /value="Supply normalization"/);
  assert.match(live, /type your own/);
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
