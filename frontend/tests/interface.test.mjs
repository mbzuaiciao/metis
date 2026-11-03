import test from "node:test";
import { execFileSync } from "node:child_process";
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
    if (["react-plotly.js/factory", "plotly.js-basic-dist-min"].includes(specifier)) {
      return {url: `test-stub:${specifier}`, shortCircuit: true};
    }
    if (specifier.startsWith(".") && context.parentURL) {
      for (const extension of [".ts", ".tsx"]) {
        const url = new URL(specifier + extension, context.parentURL);
        if (existsSync(url)) return nextResolve(url.href, context);
      }
    }
    return nextResolve(specifier, context);
  },
  load(url, context, nextLoad) {
    // Chart pixels are browser-tested; server rendering checks dashboard text/data.
    if (url === "test-stub:react-plotly.js/factory") return {
      format: "module", shortCircuit: true,
      source: "export default () => props => { (globalThis.metisTestPlots ??= []).push(props); return null; };",
    };
    if (url === "test-stub:plotly.js-basic-dist-min") return {
      format: "module", shortCircuit: true, source: "export default {};",
    };
    if (/\.tsx?$/.test(url)) return {
      format: "module", shortCircuit: true,
      source: ts.transpileModule(readFileSync(new URL(url), "utf8"), {
        compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
      }).outputText,
    };
    return nextLoad(url, context);
  },
});
const etfComponents = await import("../src/EtfPortfolio.tsx");
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
test("research page is the eighth sidebar item and renders without backend data", () => {
  const app = readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
  const ai = app.indexOf('name: "Meta AI Reasoning"');
  const research = app.indexOf('name: "Research & Limitations"');
  assert.ok(ai > 0 && research > ai);
  assert.match(app, /page === 7 \? \(\s*<ResearchLimitations \/>/);
  assert.match(app, /page === 7\s*\? "Documented studies"/);
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
    assert.match(html, scope === "daily" ? /fictional synthetic snapshot/ : /simulated assumptions, not historical observations/);
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

test("historical results preserve three questions, portfolio links and unavailable spread displays", () => {
  const calculation = {shocks: {rates_bp: 5.37, ig_bp: 0, hy_bp: 0, equity_pct: -4.32, fx_pct: -1.46},
    total_pnl_usd: -1416477.2, by_factor: {rates_pnl: -276877.2, credit_pnl: 0, equity_pnl: -993600, fx_pnl: -146000},
    positions: [{id: "IRS-R", name: "Receive-fixed", rates_pnl: -150360, credit_pnl: 0, equity_pnl: 0, fx_pnl: 0, pnl_usd: -150360, dv01_usd_per_bp: 28000, cs01_usd_per_bp: 0, market_value_usd: 4000000, notional_usd: 40000000}]};
  const input = JSON.parse(readFileSync(new URL("../../research/historical-macro-20220913-inputs.json", import.meta.url), "utf8"));
  const answer = {investigation_scope: "historical", mode: "meta", context_operations: [], context: {
    market: {as_of: "2022-09-13"}, historical: input, macro_context: input.macro_context,
    portfolio: {portfolio_name: "Synthetic fixed holdings", nav_usd: 100000000, exposures: {}},
    scenario: calculation, daily: calculation, evidence: []},
    interpretation: {summary: "Historical summary", economic_interpretation: "Competing mechanisms",
      principal_risk_observations: [], historical_analogies: [], potential_vulnerabilities: [], assumptions_and_uncertainties: [], evidence_references: [],
      hypotheses: ["Policy", "Earnings", "Positioning"].map(title => ({title, mechanism: "Proposed transmission", consistent_evidence: "Observed moves",
        portfolio_implications: "IRS-R loses under the positive yield proxy", uncertainty: "Not causal", available_checks: "Compare signs", additional_evidence: "Distinguishing evidence"}))}};
  const html = renderToStaticMarkup(React.createElement(InvestigationResults, {answer}));
  assert.ok(html.indexOf("What happened?") < html.indexOf("What might explain it?"));
  assert.ok(html.indexOf("What might explain it?") < html.indexOf("How can we investigate?"));
  for (const text of ["2022-09-13", "Hypothesis C", "Portfolio implications", "IRS-R loses", "complete historical total is unknown", "IG/HY spread changes and credit-spread", "Unavailable", "Partial-factor position P&amp;L", "Distinguishing evidence", "0.1%", "3.7434"]) assert.ok(html.includes(text), text);
  assert.doesNotMatch(html, /IG spreads · bp|HY spreads · bp|Credit spreads<\/span><strong[^>]*>\$0|2025-03-10|Hypothetical stress investigation/);
  const app = readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
  assert.match(app, /ask\(historicalQuestion, "historical"\)/);
});


test("historical credit correction shows all modeled factors while older captured coverage stays partial", () => {
  const input = JSON.parse(readFileSync(new URL("../../backend/metis/data/historical-20220913.json", import.meta.url), "utf8"));
  const calculation = {shocks: {rates_bp: 5.37, ig_bp: 0, hy_bp: 18, equity_pct: -4.32, fx_pct: -1.46},
    total_pnl_usd: -1496577.2, by_factor: {rates_pnl: -276877.2, credit_pnl: -80100, equity_pnl: -993600, fx_pnl: -146000},
    positions: [{id: "HY-US", name: "US high yield", rates_pnl: -15036, credit_pnl: -44100, equity_pnl: 0, fx_pnl: 0,
      pnl_usd: -59136, dv01_usd_per_bp: 2800, cs01_usd_per_bp: 2450, market_value_usd: 7000000, notional_usd: 7000000}]};
  const answer = {investigation_scope: "historical", mode: "demo", context_operations: [], context: {
    market: {as_of: "2022-09-13"}, historical: {...input, credit_spreads_included: true}, macro_context: input.macro_context,
    portfolio: {portfolio_name: "Synthetic fixed holdings", nav_usd: 100000000, exposures: {}},
    scenario: calculation, daily: calculation, evidence: []},
    interpretation: {summary: "Summary", economic_interpretation: "Mechanisms", principal_risk_observations: [],
      historical_analogies: [], potential_vulnerabilities: [], assumptions_and_uncertainties: [], evidence_references: [],
      hypotheses: ["Policy", "Earnings", "Positioning"].map(title => ({title, mechanism: "Transmission", consistent_evidence: "Moves",
        portfolio_implications: "Position effects", uncertainty: "Not causal", available_checks: "Signs", additional_evidence: "Flows"}))}};
  const original = structuredClone(answer);
  const html = renderToStaticMarkup(React.createElement(InvestigationResults, {answer}));
  for (const text of ["1 · What happened?", "2 · What might explain it?", "3 · How can we investigate?", "Hypothesis C",
    "$1,496,577", "credit spreads -$80,100", "146 → 146bp (0bp)", "450 → 468bp (+18bp)",
    "estimated hypothetical P&amp;L", "European spread moves are not observed", "-$44,100", "-$59,136"]) assert.ok(html.includes(text), text);
  assert.match(html, /equibles.com/);
  assert.doesNotMatch(html, /Unavailable|complete historical total is unknown|Partial-factor|zero engine placeholders/);
  assert.deepEqual(answer, original);
  const scope = renderToStaticMarkup(React.createElement(InvestigationScope, {answer, label: "Follow-up scope"}));
  assert.match(scope, /estimated hypothetical P&amp;L/);
  assert.match(scope, /IG OAS 0bp; HY OAS \+18bp/);
});

test("daily selector offers distinct synthetic dates and discloses fictional data", async () => {
  const { DefaultInvestigationDate } = await import("../src/DefaultInvestigationDate.tsx");
  const config = JSON.parse(readFileSync(new URL("../../backend/metis/data/investigation.json", import.meta.url), "utf8"));
  const investigation = {...config, snapshots: Object.keys(config.snapshots).map(date => ({market: {as_of: date}}))};
  for (const selectedDate of Object.keys(config.snapshots)) {
    const html = renderToStaticMarkup(React.createElement(DefaultInvestigationDate, {
      investigation, selectedDate, disabled: false, onSelect() {},
    }));
    assert.ok(html.includes(`value="${selectedDate}" selected=""`));
    assert.match(html, /2026-10-30.*fictional synthetic snapshot.*default/);
    assert.match(html, /2025-03-10.*fictional synthetic snapshot/);
    assert.match(html, /all dated levels, moves, position marks, notionals, sensitivities and calculated P&amp;L are synthetic/);
    assert.match(html, /not sourced market observations or real portfolio valuations/);
    assert.match(html, /do not establish hackathon development provenance/);
    assert.doesNotMatch(html, /Data unavailable/);
  }
});

test("Overview and shared ticker render October fixture values rather than legacy March metrics", async () => {
  const { Overview, MarketTicker } = await import("../src/App.tsx");
  const market = JSON.parse(readFileSync(new URL("../../backend/metis/data/market-20261030.json", import.meta.url), "utf8"));
  const data = {
    market, nav_usd: 100000000, daily_return_pct: -282200 / 100282200 * 100,
    positions: Array(12).fill({}), allocation: [],
    exposures: {dv01_usd_per_bp: 50100, ig_cs01_usd_per_bp: 12600, hy_cs01_usd_per_bp: 5200, equity_delta_usd: 26000000},
    daily: {total_pnl_usd: -282200,
      by_factor: {rates_pnl: 501000, credit_pnl: -333200, equity_pnl: -390000, fx_pnl: -60000},
      positions: [{id: "IRS-R", name: "Synthetic receive-fixed swap", pnl_usd: 245000},
        {id: "EQ-US", name: "Synthetic equities", pnl_usd: -255000}]},
  };
  const overview = renderToStaticMarkup(React.createElement(Overview, {data, goAI() {}, goRisk() {}, goCausal() {}, busy: false}));
  const ticker = renderToStaticMarkup(React.createElement(MarketTicker, {data}));
  assert.match(overview, /2026-10-30/);
  for (const amount of ["282,200", "501,000", "333,200", "390,000"]) assert.ok(overview.includes(amount));
  assert.match(ticker, /2026-10-30/);
  assert.match(ticker, /3\.90/);
  assert.match(ticker, /1\.1000/);
  assert.doesNotMatch(overview + ticker, /2025-03-10|560,770|412,480|407,250|506,000/);
});

test("market curve uses October traces with automatic bounds including the lower yields", async () => {
  const { Market } = await import("../src/App.tsx");
  const market = JSON.parse(readFileSync(new URL("../../backend/metis/data/market-20261030.json", import.meta.url), "utf8"));
  globalThis.metisTestPlots = [];
  const html = renderToStaticMarkup(React.createElement(Market, {data: {market, history: []}}));
  const curve = globalThis.metisTestPlots.find(plot => plot.data[0].type === "scatter");
  assert.deepEqual(curve.data.map(trace => trace.name), ["2026-10-29", "2026-10-30"]);
  assert.deepEqual(curve.data[1].y, [3.6, 3.75, 3.9, 4.15]);
  assert.equal(curve.layout.yaxis.range, undefined);
  assert.match(html, /2026-10-29/);
  assert.doesNotMatch(html, /2025-03-10|2025-03-07/);
});

test("ETF view renders sourced price returns, unavailable valuations, special mandates and six-row audit", () => {
  const { EtfPortfolio } = etfComponents;
  // Actual API payload from local deterministic code; no provider calls.
  const output = execFileSync('../.venv/bin/python', ['-c',
    "import json; from metis.analytics.etf import portfolio,historical_prices; print(json.dumps({'portfolio':portfolio(),'history':[historical_prices('2022-09-12','2022-09-13')]}))"],
    { cwd: new URL('..', import.meta.url), encoding: 'utf8' });
  const props = JSON.parse(output);
  const html = renderToStaticMarkup(React.createElement(EtfPortfolio, props));
  for (const ticker of ['LQD', 'EUIG', 'HYG', 'EUHY', 'SPY', 'HEFA']) assert.ok(html.includes(ticker));
  assert.match(html, /\$100,000,000/);
  assert.match(html, /-\$1,222,894.05/);
  assert.match(html, /Complete portfolio P&amp;L: Unavailable/);
  assert.match(html, /Total return: Unavailable/);
  assert.match(html, /Nov 6, 2025/);
  assert.match(html, /Nov 3, 2025/);
  assert.match(html, /EAFE/);
  assert.match(html, /bar 2022-09-13/);
  assert.match(html, /query1.finance.yahoo.com/);
  assert.match(html, /Cboe BZX/);
  for (const id of ['UST10', 'UST2', 'IRS-R', 'IRS-P', 'FX-EUR', 'CASH']) assert.ok(html.includes(id));
  for (const term of ['CUSIP', 'coupon', 'discount/forward curves', 'strike', 'statements']) assert.ok(html.includes(term));
  assert.match(html, /old generic-basket sensitivities are retained only in archived demonstrations/);
  assert.match(html, /Their sensitivities and P&amp;L do not describe this ETF allocation/);
});

test("both comparison tables use valuation types and dates; cash and OTC rows never imply quoted closes", () => {
  for (const dates of [["2022-09-12", "2022-09-13"], ["2026-10-29", "2026-10-30"]]) {
    const props = JSON.parse(execFileSync('../.venv/bin/python', ['-c',
      "import json,sys; from metis.analytics.etf import portfolio,historical_prices; print(json.dumps({'portfolio':portfolio(),'history':[historical_prices(*sys.argv[1:])]}))", ...dates],
      { cwd: new URL('..', import.meta.url), encoding: 'utf8' }));
    const html = renderToStaticMarkup(React.createElement(etfComponents.EtfPortfolio, props));
    const row = id => html.match(new RegExp(`<tr data-position-id="${id}">([\\s\\S]*?)</tr>`))[1];
    assert.doesNotMatch(html, /Starting close|Ending close/);
    assert.match(html, /Starting valuation/);
    for (const date of dates) assert.ok(html.includes(date));
    for (const id of ['IRS-R', 'IRS-P', 'FX-EUR']) {
      assert.match(row(id), /Modeled OTC mark/);
      assert.match(row(id), /USD contractual NPV/);
      assert.match(row(id), /no complete contract/);
      assert.match(row(id), /Next step:/);
      assert.match(row(id), /P&amp;L: Unavailable/);
      assert.doesNotMatch(row(id), /price return|Observed security close/);
    }
    const cash = row('CASH');
    assert.match(cash, /Cash balance/);
    assert.match(cash, /Illustrative only/);
    assert.match(cash, /Reference balance: \$4,000,000/);
    assert.match(cash, /2026-10-30/);
    assert.equal((cash.match(/Historical balance/g) || []).length, 2);
    assert.match(cash, /interest accruals/);
    assert.match(cash, /P&amp;L: Unavailable/);
    assert.doesNotMatch(cash, /\$1\.00|price return|Observed security close/);
    for (const id of ['UST10', 'UST2']) {
      assert.match(row(id), /Treasury issue price/);
      assert.match(row(id), /USD per \$100 face/);
      assert.match(row(id), /Generic 2Y\/10Y yields are not bond prices/);
      assert.match(row(id), /P&amp;L: Unavailable/);
    }
    assert.match(row('SPY'), /Observed security close/);
    assert.match(row('SPY'), /USD per ETF share/);
    assert.match(row('SPY'), /price return/);
    assert.match(html, /Research candidate 91282C/);
    assert.match(html, /only to market-based Treasury special securities/);
    assert.match(html, /unused in P&amp;L/);
    assert.match(html, /Live on comparison dates/);
  }
});

test("three illustrative snapshots render qualified estimates and inspectable inputs without replacing observations", async () => {
  const { EventSnapshots } = await import('../src/EventSnapshots.tsx');
  const snapshots = JSON.parse(execFileSync('../.venv/bin/python', ['-c',
    'import json; from metis.analytics.events import event_snapshots; print(json.dumps(event_snapshots()))'],
    {cwd: new URL('..', import.meta.url), encoding: 'utf8'}));
  const full = renderToStaticMarkup(React.createElement(EventSnapshots, {snapshots, onExplore() {}}));
  assert.equal((full.match(/<option/g) || []).length, 3);
  assert.match(full, /Use this snapshot as a causal reference/);
  const methodologyMarker = '<details><summary>Methodology &amp; Assumptions</summary>';
  assert.ok(full.indexOf('</table>') < full.indexOf('Use this snapshot as a causal reference'));
  assert.ok(full.indexOf('Use this snapshot as a causal reference') < full.indexOf(methodologyMarker));
  for (const s of snapshots) {
    const html = renderToStaticMarkup(React.createElement(EventSnapshots, {snapshots: [s]}));
    const methodologyIndex = html.indexOf(methodologyMarker);
    assert.ok(methodologyIndex > html.indexOf('</table>'));
    assert.ok(html.endsWith('</details></section>'));
    assert.equal(html.split(methodologyMarker).length - 1, 1);
    const introduction = html.slice(0, html.indexOf('<table'));
    assert.match(introduction, /<\/select><\/label><p><b>Estimated portfolio P&amp;L:/);
    assert.match(introduction, /Starting illustrative value \$100,000,000/);
    assert.match(introduction, /ending illustrative value/);
    assert.match(introduction, /Illustrative estimate — not actual portfolio returns\./);
    assert.doesNotMatch(introduction, /Observed input|Dollar display|Market inputs:|not actual historical holdings/);
    const methodology = html.slice(methodologyIndex);
    for (const text of ['Observed input', 'Dollar display', 'Market inputs:', 'March ETF observations retrieved', 'not actual historical holdings', 'cannot identify or validate event causes']) {
      assert.ok(methodology.includes(text));
    }
    const table = html.match(/<table[^>]*>([\s\S]*?)<\/table>/)[1];
    assert.equal((table.match(/<th>/g) || []).length, 4);
    assert.doesNotMatch(table, /Status \/ provenance|class="badge|Method \/ inputs/);
    assert.equal((table.match(/<details class="holding-details">/g) || []).length, 12);
    assert.equal((table.match(/class="holding-chevron"/g) || []).length, 12);
    for (const row of table.matchAll(/<tr data-event-position="[^"]+">([\s\S]*?)<\/tr>/g)) {
      assert.equal((row[1].match(/<td\b[^>]*>/g) || []).length, 4);
    }
    assert.equal((html.match(/data-event-position=/g) || []).length, 12);
    assert.match(html, /Observed input/);
    assert.match(html, /Estimated/);
    assert.match(html, /Hypothetical assumption/);
    assert.match(html, /Approximate input/);
    assert.match(html, /not actual historical holdings/);
    assert.match(html, /12\/12 rows/);
    assert.match(html, /fred.stlouisfed.org/);
    assert.match(html, /query1.finance.yahoo.com/);
    assert.match(html, /fixed strike/);
    assert.match(html, /not a par new swap/);
    assert.match(html, /No TreasuryDirect special-security prices used/);
    assert.match(html, /not total return/);
    assert.match(html, /zero-interest\/zero-flow/);
    assert.match(html, /cannot identify or validate event causes/);
    for (const date of [s.start, s.end]) assert.ok(html.includes(date));
    if (s.id !== 'october-2026') assert.match(html, /Not an ETF price or actual pre-inception holding/);
  }
  const missing = {...snapshots[0], estimated_pnl_usd: null, end_nav_usd: null, coverage_count: 11};
  const html = renderToStaticMarkup(React.createElement(EventSnapshots, {snapshots:[missing]}));
  assert.match(html, /Estimated portfolio P&amp;L: Unavailable/);
  assert.match(html, /Missing rows are excluded, never assumed zero/);
  const causal = renderToStaticMarkup(React.createElement(CausalExploration, {
    state: {...initialCausalState, eventSnapshotId:'cpi-2022'}, setState() {},
    data:{causal_mode:'demo',positions:[],market:{as_of:'2026-10-30'},event_snapshots:snapshots},
    generate() {}, calculate() {}, useShocks() {},
  }));
  assert.match(causal, /option value="cpi-2022" selected/);
  assert.match(causal, /they do not revalue the event snapshot/);
  const app = readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(app, /EXAMPLE DATA/);
  assert.match(app, /className="portfolio-tab"/);
  assert.match(app, /className="overview-tab"/);
});

test("event snapshots apply consistent sign colors to P&L and summary while keeping zero neutral and valuations uncolored", async () => {
  const { EventSnapshots } = await import('../src/EventSnapshots.tsx');
  const snapshots = JSON.parse(execFileSync('../.venv/bin/python', ['-c',
    'import json; from metis.analytics.events import event_snapshots; print(json.dumps(event_snapshots()))'],
    {cwd: new URL('..', import.meta.url), encoding: 'utf8'}));

  for (const s of snapshots) {
    const html = renderToStaticMarkup(React.createElement(EventSnapshots, {snapshots: [s]}));
    assert.match(html, /Estimated portfolio P&amp;L: <span class="negative">-\$[\d,]+<\/span>/);

    for (const p of s.positions) {
      const rowMatch = html.match(new RegExp(`<tr data-event-position="${p.id}">([\\s\\S]*?)</tr>`));
      assert.ok(rowMatch, `Row for ${p.id} should exist`);
      const cells = [...rowMatch[1].matchAll(/<td\b([^>]*)>([\s\S]*?)<\/td>/g)];
      assert.equal(cells.length, 4);

      const [, startValCell, endValCell, pnlCell] = cells;

      // Starting and ending valuations must NOT have sign coloring even if signed
      assert.doesNotMatch(startValCell[1], /class="[^"]*(?:negative|positive)[^"]*"/);
      assert.doesNotMatch(endValCell[1], /class="[^"]*(?:negative|positive)[^"]*"/);

      // P&L column color semantics
      if (p.pnl_usd === 0) {
        assert.doesNotMatch(pnlCell[1], /class="[^"]*(?:negative|positive)[^"]*"/);
        assert.match(pnlCell[2], /\$0/);
      } else if (p.pnl_usd < 0) {
        assert.match(pnlCell[1], /class="[^"]*negative[^"]*"/);
        assert.match(pnlCell[2], /-\$[\d,]+/);
      } else {
        assert.match(pnlCell[1], /class="[^"]*positive[^"]*"/);
        assert.match(pnlCell[2], /\$[\d,]+/);
      }
    }
  }

  // Synthetic snapshot with positive aggregate P&L
  const positiveSnapshot = {
    ...snapshots[0],
    id: "synthetic-gain",
    estimated_pnl_usd: 500000,
    positions: [{ id: "WINNER", label: "Gain", method: "M", inputs: [], terms: {}, assumptions: [], start_value_usd: 1000000, end_value_usd: 1500000, pnl_usd: 500000 }]
  };
  const positiveHtml = renderToStaticMarkup(React.createElement(EventSnapshots, {snapshots: [positiveSnapshot]}));
  assert.match(positiveHtml, /Estimated portfolio P&amp;L: <span class="positive">\$500,000<\/span>/);
  assert.match(positiveHtml, /<td class="positive">\$500,000<\/td>/);
});

test("Portfolio opens on dated portfolio snapshot with no event selector and no unsupported MTD claims", async () => {
  const { Portfolio } = await import("../src/App.tsx");
  const output = execFileSync('../.venv/bin/python', ['-c',
    "import json; from metis.analytics.engine import workstation; from metis.analytics.etf import portfolio, historical_prices; from metis.analytics.events import event_snapshots; print(json.dumps({**workstation(), 'event_snapshots': event_snapshots(), 'etf_portfolio': portfolio(), 'etf_history': [historical_prices('2026-10-29', '2026-10-30'), historical_prices('2022-09-12', '2022-09-13')]}))"],
    { cwd: new URL('..', import.meta.url), encoding: 'utf8' });
  const data = JSON.parse(output);
  const html = renderToStaticMarkup(React.createElement(Portfolio, { data }));

  // Check dated snapshot
  assert.match(html, /Portfolio snapshot · As of 2026-10-30/);
  assert.match(html, /Daily price comparison: 2026-10-29 → 2026-10-30/);

  // Check 12 positions and $100m illustrative allocation
  assert.match(html, /\$100,000,000/);
  for (const ticker of ['LQD', 'EUIG', 'HYG', 'EUHY', 'SPY', 'HEFA', 'UST10', 'UST2', 'IRS-R', 'IRS-P', 'FX-EUR', 'CASH']) {
    assert.ok(html.includes(ticker), `Expected holding ${ticker} in Portfolio`);
  }

  // Check supported daily P&L and unavailable totals
  assert.match(html, /Covered price P&amp;L: <span class="negative">-\$417,244\.37<\/span>/);
  assert.match(html, /Complete portfolio P&amp;L: Unavailable/);
  assert.match(html, /MTD P&amp;L: Unavailable/);
  assert.match(html, /intervening daily bars are not retrieved; extrapolation from two daily closes is not defensible/);

  // Confirm NO event selector in Portfolio
  assert.doesNotMatch(html, /<select/);
  assert.doesNotMatch(html, /Event window/);
  assert.doesNotMatch(html, /Observed ETF comparison:/);
});

test("Historical event replay in Causal Scenario Exploration retains 3 event windows and causal reference", async () => {
  const { CausalExploration } = await import("../src/CausalExploration.tsx");
  const snapshots = JSON.parse(execFileSync('../.venv/bin/python', ['-c',
    'import json; from metis.analytics.events import event_snapshots; print(json.dumps(event_snapshots()))'],
    { cwd: new URL('..', import.meta.url), encoding: 'utf8' }));
  const data = {
    causal_mode: 'demo',
    positions: [],
    market: { as_of: '2026-10-30' },
    event_snapshots: snapshots,
  };
  const html = renderToStaticMarkup(React.createElement(CausalExploration, {
    state: initialCausalState,
    setState() {},
    data,
    generate() {},
    calculate() {},
    useShocks() {},
  }));

  // Clearly labeled section
  assert.match(html, /aria-label="Historical event replay"/);
  assert.match(html, /Historical event replay/);
  assert.match(html, /HISTORICAL REPLAY · RECONSTRUCTED/);
  assert.match(html, /aria-label="Hypothetical stress scenarios"/);

  // All 3 event windows present
  for (const id of ['cpi-2022', 'march-2025', 'october-2026']) {
    assert.ok(html.includes(`value="${id}"`), `Event window ${id} should be present`);
  }
  assert.match(html, /2022-09-12 → 2022-09-13 · US CPI shock/);
  assert.match(html, /2025-03-07 → 2025-03-10 · March comparison/);
  assert.match(html, /2026-10-29 → 2026-10-30 · October reference/);

  // Causal reference button
  assert.match(html, /Use this snapshot as a causal reference/);
});

test("Market Monitor presents unified date-consistent multi-asset market snapshot across all three windows", async () => {
  const { Market } = await import("../src/App.tsx");
  const output = execFileSync('../.venv/bin/python', ['-c',
    "import json; from metis.analytics.engine import workstation; from metis.analytics.etf import portfolio; from metis.analytics.events import event_snapshots; print(json.dumps({**workstation(), 'event_snapshots': event_snapshots(), 'etf_portfolio': portfolio()}))"],
    { cwd: new URL('..', import.meta.url), encoding: 'utf8' });
  const data = JSON.parse(output);
  const html = renderToStaticMarkup(React.createElement(Market, { data }));

  // 1. One unified Market snapshot panel header
  assert.match(html, /Market snapshot · 2026-10-29 → 2026-10-30/);
  assert.doesNotMatch(html, /<section class="panel[^"]*">[^<]*<div class="panel-heading"><h2>Observed equity ETF market prices/);

  // 2. Default October 2026 multi-asset table rows
  // Rates (2Y, 5Y, 10Y) - neutral coloring preserving signs
  assert.match(html, /US Treasury 2Y yield/);
  assert.match(html, /4\.61%/);
  assert.match(html, /4\.56%/);
  assert.match(html, /-5bp/);

  const dgs2Row = html.match(/<tr data-market-instrument="DGS2">([\s\S]*?)<\/tr>/)[1];
  assert.match(dgs2Row, />-5bp<\/em>/);
  assert.doesNotMatch(dgs2Row, /class="[^"]*(?:negative|positive)[^"]*"/);

  assert.match(html, /US Treasury 5Y yield/);
  assert.match(html, /4\.78%/);
  assert.match(html, /4\.71%/);
  assert.match(html, /-7bp/);

  const dgs5Row = html.match(/<tr data-market-instrument="DGS5">([\s\S]*?)<\/tr>/)[1];
  assert.match(dgs5Row, />-7bp<\/em>/);
  assert.doesNotMatch(dgs5Row, /class="[^"]*(?:negative|positive)[^"]*"/);

  assert.match(html, /US Treasury 10Y yield/);
  assert.match(html, /4\.98%/);
  assert.match(html, /4\.94%/);
  assert.match(html, /-4bp/);

  const dgs10Row = html.match(/<tr data-market-instrument="DGS10">([\s\S]*?)<\/tr>/)[1];
  assert.match(dgs10Row, />-4bp<\/em>/);
  assert.doesNotMatch(dgs10Row, /class="[^"]*(?:negative|positive)[^"]*"/);

  // Equities (SPY, HEFA) - directional red/teal coloring preserved
  assert.match(html, /SPY/);
  assert.match(html, /\$769\.36/);
  assert.match(html, /\$755\.72/);
  assert.match(html, /-1\.77%/);

  const spyRow = html.match(/<tr data-market-instrument="SPY">([\s\S]*?)<\/tr>/)[1];
  assert.match(spyRow, /class="negative"[^>]*>-1\.77%/);

  assert.match(html, /HEFA/);
  assert.match(html, /\$46\.84/);
  assert.match(html, /\$46\.30/);
  assert.match(html, /-1\.15%/);
  assert.match(html, /HEFA represents USD-hedged developed ex-US exposure, not an unhedged index/);

  const hefaRow = html.match(/<tr data-market-instrument="HEFA">([\s\S]*?)<\/tr>/)[1];
  assert.match(hefaRow, /class="negative"[^>]*>-1\.15%/);

  // FX (EUR/USD)
  assert.match(html, /EUR\/USD/);
  assert.match(html, /1\.1165/);
  assert.match(html, /1\.1163/);
  assert.match(html, /-0\.02%/);
  assert.match(html, /observation clock differs from ETF 4:00 PM close/);

  // Credit (IG, HY) — Not available for Oct 2026
  assert.match(html, /Investment grade credit spread/);
  assert.match(html, /High yield credit spread/);
  assert.match(html, /Dated historical spread quotes unavailable/);

  // Removes 'Daily return' placeholder level
  assert.doesNotMatch(html, /<b>Daily return<\/b>/);
  assert.doesNotMatch(html, /Daily return/);

  // Notice does not contain fictional benchmark date reference
  const noticeMatch = html.match(/<div class="notice">([\s\S]*?)<\/div>/)[1];
  assert.doesNotMatch(noticeMatch, /Benchmark comparison date/);

  // Archived synthetic benchmarks collapsed with synthetic Economic context panel inside
  assert.match(html, /<details class="archived-market-details">/);
  assert.match(html, /Archived synthetic market benchmarks/);
  assert.match(html, /Modeled rates, credit spreads, and FX levels are not observed quotes/);

  const archivedContentMatch = html.match(/<div class="archived-market-content">([\s\S]*?)<\/details>/)[1];
  assert.match(archivedContentMatch, /Economic context/);
  assert.match(archivedContentMatch, /Assumed regime/);

  const afterArchived = html.slice(html.lastIndexOf('</details>'));
  assert.doesNotMatch(afterArchived, /Economic context/);

  // 3. September 2022 CPI window: verify all rows update synchronously
  const cpiHtml = renderToStaticMarkup(React.createElement(Market, { data, selectedEventId: "cpi-2022" }));
  assert.match(cpiHtml, /Market snapshot · 2022-09-12 → 2022-09-13/);
  assert.match(cpiHtml, /3\.58%/);
  assert.match(cpiHtml, /3\.75%/);
  assert.match(cpiHtml, /\+17bp/);

  const cpiDgs2Row = cpiHtml.match(/<tr data-market-instrument="DGS2">([\s\S]*?)<\/tr>/)[1];
  assert.match(cpiDgs2Row, />\+17bp<\/em>/);
  assert.doesNotMatch(cpiDgs2Row, /class="[^"]*(?:negative|positive)[^"]*"/);
  assert.match(cpiHtml, /3\.47%/);
  assert.match(cpiHtml, /3\.58%/);
  assert.match(cpiHtml, /\+11bp/);
  assert.match(cpiHtml, /3\.37%/);
  assert.match(cpiHtml, /3\.42%/);
  assert.match(cpiHtml, /\+5bp/);
  assert.match(cpiHtml, /\$410\.97/);
  assert.match(cpiHtml, /\$393\.10/);
  assert.match(cpiHtml, /-4\.35%/);
  assert.match(cpiHtml, /\$32\.56/);
  assert.match(cpiHtml, /\$31\.86/);
  assert.match(cpiHtml, /-2\.15%/);
  assert.match(cpiHtml, /1\.0129/);
  assert.match(cpiHtml, /0\.9997/);
  assert.match(cpiHtml, /-1\.30%/);
  assert.match(cpiHtml, /\+15bp \(Assumed shock\)/);
  assert.match(cpiHtml, /\+30bp \(Assumed shock\)/);

  // 4. March 2025 window: verify all rows update synchronously
  const marchHtml = renderToStaticMarkup(React.createElement(Market, { data, selectedEventId: "march-2025" }));
  assert.match(marchHtml, /Market snapshot · 2025-03-07 → 2025-03-10/);
  assert.match(marchHtml, /3\.99%/);
  assert.match(marchHtml, /3\.89%/);
  assert.match(marchHtml, /-10bp/);
  assert.match(marchHtml, /4\.09%/);
  assert.match(marchHtml, /3\.98%/);
  assert.match(marchHtml, /-11bp/);
  assert.match(marchHtml, /4\.32%/);
  assert.match(marchHtml, /4\.22%/);
  assert.match(marchHtml, /\$575\.92/);
  assert.match(marchHtml, /\$560\.58/);
  assert.match(marchHtml, /-2\.66%/);
  assert.match(marchHtml, /\$37\.27/);
  assert.match(marchHtml, /\$36\.42/);
  assert.match(marchHtml, /-2\.28%/);
  assert.match(marchHtml, /1\.0859/);
  assert.match(marchHtml, /1\.0837/);
  assert.match(marchHtml, /-0\.20%/);
  assert.match(marchHtml, /\+10bp \(Assumed shock\)/);
  assert.match(marchHtml, /\+25bp \(Assumed shock\)/);
});

test("Market Monitor and Causal Scenario Exploration share historical event selection consistently", async () => {
  const { Market } = await import("../src/App.tsx");
  const { CausalExploration } = await import("../src/CausalExploration.tsx");
  const output = execFileSync('../.venv/bin/python', ['-c',
    "import json; from metis.analytics.engine import workstation; from metis.analytics.etf import portfolio; from metis.analytics.events import event_snapshots; print(json.dumps({**workstation(), 'event_snapshots': event_snapshots(), 'etf_portfolio': portfolio()}))"],
    { cwd: new URL('..', import.meta.url), encoding: 'utf8' });
  const data = JSON.parse(output);

  for (const eventId of ["october-2026", "cpi-2022", "march-2025"]) {
    const marketHtml = renderToStaticMarkup(React.createElement(Market, { data, selectedEventId: eventId }));
    const causalHtml = renderToStaticMarkup(React.createElement(CausalExploration, {
      state: initialCausalState,
      setState() {},
      data,
      generate() {},
      calculate() {},
      useShocks() {},
      selectedEventId: eventId,
    }));

    const snapshot = data.event_snapshots.find(s => s.id === eventId);
    assert.match(marketHtml, new RegExp(snapshot.start));
    assert.match(marketHtml, new RegExp(snapshot.end));
    assert.match(causalHtml, new RegExp(snapshot.start));
    assert.match(causalHtml, new RegExp(snapshot.end));
  }
});

test("Portfolio presents compact 12-position snapshot leading with dated P&L and collapsed methodology audit", async () => {
  const { Portfolio } = await import("../src/App.tsx");
  const output = execFileSync('../.venv/bin/python', ['-c',
    "import json; from metis.analytics.engine import workstation; from metis.analytics.etf import portfolio, historical_prices; from metis.analytics.events import event_snapshots; print(json.dumps({**workstation(), 'event_snapshots': event_snapshots(), 'etf_portfolio': portfolio(), 'etf_history': [historical_prices('2026-10-29', '2026-10-30'), historical_prices('2022-09-12', '2022-09-13')]}))"],
    { cwd: new URL('..', import.meta.url), encoding: 'utf8' });
  const data = JSON.parse(output);
  const html = renderToStaticMarkup(React.createElement(Portfolio, { data }));

  // 1. Structure check: First screen opens with compact 12-position snapshot section
  const snapshotSectionMatch = html.match(/<section class="etf-portfolio portfolio-snapshot" aria-label="Portfolio snapshot">([\s\S]*?)<\/section>/);
  assert.ok(snapshotSectionMatch, "Portfolio snapshot section must exist at top");
  const snapshotHtml = snapshotSectionMatch[1];

  // Title and compact lead summary with modeled full-snapshot P&L (-$333,000 on $100m)
  assert.match(snapshotHtml, /<h2>Portfolio snapshot · As of 2026-10-30<\/h2>/);
  assert.match(snapshotHtml, /Estimated portfolio P&amp;L: <span class="negative">-\$333,000<\/span>/);
  assert.match(snapshotHtml, /Starting illustrative value \$100,000,000 → ending illustrative value \$99,667,000 · 12\/12 rows/);
  assert.match(snapshotHtml, /Illustrative modeled P&amp;L, not observed account returns · MTD: Not available/);

  // Directly followed by the 4-column compact table
  const tableMatch = snapshotHtml.match(/<table class="etf-table event-table">([\s\S]*?)<\/table>/);
  assert.ok(tableMatch, "4-column compact table must exist in snapshot section");
  const tableHtml = tableMatch[1];

  // Header verification: 4 columns
  assert.match(tableHtml, /<th>Holding<\/th>/);
  assert.match(tableHtml, /<th>Starting USD value<br\s*\/?>2026-10-29<\/th>/);
  assert.match(tableHtml, /<th>Ending USD value<br\s*\/?>2026-10-30<\/th>/);
  assert.match(tableHtml, /<th>Estimated P&amp;L<\/th>/);

  // 12 position rows with expander chevrons
  const rows = [...tableHtml.matchAll(/<tr data-event-position="([^"]+)">([\s\S]*?)<\/tr>/g)];
  assert.equal(rows.length, 12, "Must contain exactly 12 position rows");
  assert.equal((tableHtml.match(/class="holding-chevron"/g) || []).length, 12);
  assert.equal((tableHtml.match(/<details class="holding-details">/g) || []).length, 12);

  // Modeled values for non-ETF instruments (Treasuries, Swaps, FX, Cash) rather than "Unavailable"
  for (const [rowHtml, posId] of rows.map(r => [r[2], r[1]])) {
    const cells = [...rowHtml.matchAll(/<td\b([^>]*)>([\s\S]*?)<\/td>/g)];
    assert.equal(cells.length, 4, `Row ${posId} must have 4 cells`);
    const [, startVal, endVal, pnl] = cells;

    // None of the table value cells should be 'Unavailable'
    assert.doesNotMatch(startVal[2], /Unavailable/, `Row ${posId} starting value must be modeled`);
    assert.doesNotMatch(endVal[2], /Unavailable/, `Row ${posId} ending value must be modeled`);
    assert.doesNotMatch(pnl[2], /Unavailable/, `Row ${posId} P&L must be modeled`);

    // Valuations uncolored
    assert.doesNotMatch(startVal[1], /negative|positive/);
    assert.doesNotMatch(endVal[1], /negative|positive/);
  }

  // Specific instrument check in compact table
  const ust10Row = rows.find(r => r[1] === "UST10")[2];
  assert.match(ust10Row, /\$18,000,000/);
  assert.match(ust10Row, /\$18,058,000/);
  assert.match(ust10Row, /<td class="positive">\$58,000<\/td>/);

  const irsPRow = rows.find(r => r[1] === "IRS-P")[2];
  assert.match(irsPRow, /-\$500,000/);
  assert.match(irsPRow, /-\$579,000/);
  assert.match(irsPRow, /<td class="negative">-\$79,000<\/td>/);

  const cashRow = rows.find(r => r[1] === "CASH")[2];
  assert.match(cashRow, /\$4,000,000/);
  assert.match(cashRow, /<td>\$0<\/td>/); // neutral zero uncolored

  // 2. Collapsed details: Methodology, Assumptions, and Preserved observed-price audit
  assert.match(html, /<details class="portfolio-methodology-details">[\s\S]*?<summary>Methodology &amp; Assumptions · Preserved observed-price audit<\/summary>/);

  // Distinct metrics: whole-snapshot modeled P&L vs observed-price ETF sleeve
  assert.match(html, /Observed-only ETF sleeve comparison/);
  assert.match(html, /Covered price P&amp;L: <span class="negative">-\$417,244\.37<\/span><\/b> on \$64,000,000\.00 of starting allocations/);
  assert.match(html, /Complete portfolio P&amp;L: Unavailable \(observed-price basis\)/);

  // Preserved instrument audit and CUSIPs inside collapsed section
  assert.match(html, /Observed-price coverage audit · preserved evidence/);
  assert.match(html, /Remaining six instruments: valuation gaps and minimum data/);
  assert.match(html, /TreasuryDirect historical reference source/);

  // NO event selector anywhere in Portfolio
  assert.doesNotMatch(html, /<select/);
  assert.doesNotMatch(html, /Event window/);
});
