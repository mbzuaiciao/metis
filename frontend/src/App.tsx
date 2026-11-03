import { useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  BookOpen,
  ChevronRight,
  CircleHelp,
  FlaskConical,
  Globe2,
  Layers3,
  LayoutDashboard,
  LoaderCircle,
  Send,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { VerificationDemo } from "./ClaimVerification";
import { InvestigationResults } from "./InvestigationResults";
import { InvestigationScope } from "./InvestigationScope";
import { DefaultInvestigationDate } from "./DefaultInvestigationDate";
import { CausalExploration } from "./CausalExploration";
import { ResearchLimitations } from "./ResearchLimitations";
import { EtfPortfolio } from "./EtfPortfolio";
import {
  EventSnapshots,
  EventTable,
  money as eventMoney,
  pnlTone as eventPnlTone,
} from "./EventSnapshots";
import { initialCausalState } from "./causal";
import { AgGridReact } from "ag-grid-react";
import {
  AllCommunityModule,
  ModuleRegistry,
  themeQuartz,
  type ColDef,
} from "ag-grid-community";
import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-basic-dist-min";
import type { Data, Layout } from "plotly.js";
import type {
  Calculation,
  Episode,
  EventSnapshot,
  EtfPortfolio as EtfPortfolioType,
  Position,
  Reasoning,
  Shocks,
  Workstation,
} from "./types";

import {
  FactorEvidence,
  PositionEvidence,
} from "./InvestigationEvidence";
import {
  dailyQuestion,
  dailySnapshot,
  historicalQuestion,
  scenarioQuestion,
  investigationRequest,
  followupTarget,
  scopeLabel,
  principalDrivers,
  type InvestigationFocus,
} from "./investigation";

ModuleRegistry.registerModules([AllCommunityModule]);
const Plot = createPlotlyComponent(Plotly);
const palette = [
  "#52d6bb",
  "#748cf4",
  "#c0a0ed",
  "#e4b669",
  "#598fca",
  "#e48f9b",
  "#5d7189",
];
const money = (v: number, compact = false) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: compact ? "compact" : "standard",
    maximumFractionDigits: compact ? 2 : 0,
  }).format(v);
const num = (v: number) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(v);
const signed = (v: number, suffix = "") =>
  `${v > 0 ? "+" : ""}${v.toFixed(2)}${suffix}`;
const tone = (v: number) => (v < 0 ? "negative" : v > 0 ? "positive" : "muted");
const factorName: Record<string, string> = {
  rates_pnl: "Government rates",
  credit_pnl: "Credit spreads",
  equity_pnl: "Equities",
  fx_pnl: "Foreign exchange",
};
const pages = [
  { name: "Overview", icon: LayoutDashboard },
  { name: "Portfolio", icon: Layers3 },
  { name: "Market Monitor", icon: Globe2 },
  { name: "Risk Analytics", icon: BarChart3 },
  { name: "Risk Sensitivity Analysis", icon: SlidersHorizontal },
  { name: "Causal Scenario Exploration", icon: FlaskConical },
  { name: "Meta AI Reasoning", icon: BrainCircuit },
  { name: "Research & Limitations", icon: BookOpen },
];
const subtitles = [
  "Your portfolio, in perspective.",
  "Positions, valuations and the exposures behind them.",
  "The market context behind portfolio performance.",
  "Understand the drivers. Look beyond the headline.",
  "Explore how individual market risk factors affect portfolio P&L.",
  "Compare economic explanations and their potential cross-asset implications.",
  "From measured exposure to economic understanding.",
  "Experiments, evidence, limitations, and open research questions.",
];
async function api<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`/api/${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers:
      body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(
      typeof detail.detail === "string"
        ? detail.detail
        : `Request failed (${response.status}).`,
    );
  }
  return response.json();
}
function Panel({
  title,
  note,
  children,
  className = "",
}: {
  title: string;
  note?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <h2>{title}</h2>
        {note && <span>{note}</span>}
      </div>
      {children}
    </section>
  );
}
function Metric({
  label,
  value,
  detail,
  className = "",
}: {
  label: string;
  value: string;
  detail: string;
  className?: string;
}) {
  return (
    <div className="metric">
      <span className="eyebrow">{label}</span>
      <strong className={className}>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}
function Chart({
  data,
  layout = {},
  height = 265,
}: {
  data: Data[];
  layout?: Partial<Layout>;
  height?: number;
}) {
  return (
    <Plot
      data={data}
      layout={{
        autosize: true,
        height,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: {
          family: "Inter, ui-sans-serif, system-ui",
          color: "#94a3b8",
          size: 11,
        },
        margin: { l: 65, r: 24, t: 16, b: 45 },
        xaxis: {
          gridcolor: "#232e3e",
          zerolinecolor: "#3b485b",
          automargin: true,
        },
        yaxis: {
          gridcolor: "#232e3e",
          zerolinecolor: "#3b485b",
          automargin: true,
        },
        showlegend: false,
        hoverlabel: { bgcolor: "#182334", font: { color: "#edf4fc" } },
        ...layout,
      }}
      config={{
        responsive: true,
        displaylogo: false,
        modeBarButtonsToRemove: ["lasso2d", "select2d"],
      }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );
}
function FactorChart({ calc }: { calc: Calculation }) {
  const entries = Object.entries(calc.by_factor);
  return (
    <Chart
      data={[
        {
          type: "bar",
          x: entries.map(([k]) => factorName[k]),
          y: entries.map(([, v]) => v),
          marker: {
            color: entries.map(([, v]) => (v < 0 ? "#e78d9a" : "#52d6bb")),
          },
          hovertemplate: "%{x}<br>$%{y:,.0f}<extra></extra>",
        },
      ]}
      layout={{
        yaxis: {
          gridcolor: "#232e3e",
          tickprefix: "$",
          tickformat: ".2s",
          zerolinecolor: "#556277",
        },
      }}
    />
  );
}
function ExposureMetrics({ data }: { data: Workstation }) {
  const e = data.exposures;
  return (
    <div className="metrics four">
      <Metric
        label="Net interest-rate DV01"
        value={`${money(e.dv01_usd_per_bp)}/bp`}
        detail="Gain for a 1bp government yield decline"
      />
      <Metric
        label="Credit spread CS01"
        value={`${money(e.cs01_usd_per_bp)}/bp`}
        detail="Gain for a 1bp parallel spread decline"
      />
      <Metric
        label="Equity delta"
        value={money(e.equity_delta_usd, true)}
        detail="USD equivalent directional exposure"
      />
      <Metric
        label="FX delta · long EUR"
        value={money(e.fx_delta_usd, true)}
        detail={`${money(e.fx_delta_usd / 100)} gain for +1% EUR/USD`}
      />
    </div>
  );
}
function EpisodeCards({ episodes }: { episodes: Episode[] }) {
  return (
    <div className="episode-grid">
      {episodes.map((h) => (
        <article key={h.id} className="episode">
          <span className="eyebrow">{h.period} · Historical context</span>
          <h3>{h.title}</h3>
          <p>{h.fact}</p>
          <p>
            <b>Portfolio lens</b> {h.interpretation}
          </p>
          <small>{h.limitation}</small>
          <a href={h.source_url} target="_blank" rel="noreferrer">
            {h.source_title} ↗
          </a>
        </article>
      ))}
    </div>
  );
}
export function Overview({
  data,
  goAI,
  goRisk,
  goCausal,
  busy,
}: {
  data: Workstation;
  goAI: () => void;
  goRisk: () => void;
  goCausal: () => void;
  busy: boolean;
}) {
  const drivers = principalDrivers(data.daily);
  return (
    <div className="overview-tab">
      <div className="metrics four">
        <Metric
          label="Portfolio NAV"
          value={money(data.nav_usd, true)}
          detail="USD · end-of-day synthetic marks"
        />
        <Metric
          label="Daily P&L"
          value={money(data.daily.total_pnl_usd)}
          detail={`${signed(data.daily_return_pct, "%")} vs opening NAV`}
          className={tone(data.daily.total_pnl_usd)}
        />
        <Metric
          label="Rate contribution"
          value={money(data.daily.by_factor.rates_pnl)}
          detail={`Government yields ${((data.market.yields[0].current_pct - data.market.yields[0].previous_pct) * 100).toFixed(0)}bp · parallel`}
          className="positive"
        />
        <Metric
          label="Positions"
          value={`${data.positions.length}`}
          detail={`${data.allocation.length} asset classes · multi-asset mandate`}
        />
      </div>
      <section className="investigation-start">
        <div>
          <span className="eyebrow">
            1 · WHAT HAPPENED? · SYNTHETIC {data.market.as_of}
          </span>
          <h2>
            A positive rate contribution did not prevent a portfolio loss.
          </h2>
          <p>
            Inspect the daily calculation, then ask Metis to interpret the
            economic relationships.
          </p>
        </div>
        <div className="investigation-actions">
          <button className="primary" onClick={goCausal}>
            Explore competing explanations <ArrowRight size={16} />
          </button>
          <button className="secondary" onClick={goAI} disabled={busy}>
            {busy ? "Interpretation in progress…" : "2 · Explain the daily loss"}
            <ArrowRight size={16} />
          </button>
        </div>
      </section>
      <div className="grid-main">
        <Panel
          title="Daily factor contributions"
          note="Calculated · USD · illustrative snapshot"
        >
          <FactorEvidence calculation={data.daily} />
        </Panel>
        <Panel
          title="Principal position drivers"
          note="Calculated net daily P&L"
        >
          <div className="driver-list">
            {[
              ["Largest loss", drivers.loss],
              ["Largest gain", drivers.gain],
            ].map(([label, position]) => {
              const p = position as Position | undefined;
              return (
                p && (
                  <div key={label as string}>
                    <span>
                      {label as string}
                      <small>{p.name}</small>
                    </span>
                    <strong className={tone(p.pnl_usd)}>
                      {money(p.pnl_usd)}
                    </strong>
                  </div>
                )
              );
            })}
          </div>
          <button className="text-button evidence-action" onClick={goRisk}>
            Inspect all risk exposures <ArrowRight size={14} />
          </button>
          <PositionEvidence
            calculation={data.daily}
            exposures={data.exposures}
          />
        </Panel>
      </div>
      <div className="grid-main">
        <Panel title="Asset-class allocation" note="Marked value · % of NAV">
          <div className="allocation">
            <Chart
              height={285}
              data={[
                {
                  type: "pie",
                  labels: data.allocation.map((a) => a.asset_class),
                  values: data.allocation.map((a) => a.market_value_usd),
                  hole: 0.76,
                  sort: false,
                  marker: {
                    colors: palette,
                    line: { color: "#101722", width: 3 },
                  },
                  textinfo: "none",
                  hovertemplate:
                    "%{label}<br>%{percent} · $%{value:,.0f}<extra></extra>",
                },
              ]}
              layout={{
                margin: { l: 10, r: 10, t: 20, b: 20 },
                annotations: [
                  {
                    text: money(data.nav_usd, true),
                    x: 0.5,
                    y: 0.54,
                    showarrow: false,
                    font: { size: 25, color: "#e7eef8" },
                  },
                  {
                    text: "NET ASSET VALUE",
                    x: 0.5,
                    y: 0.4,
                    showarrow: false,
                    font: { size: 9, color: "#8191a7" },
                  },
                ],
              }}
            />
            <div className="legend">
              {data.allocation.map((a, i) => (
                <div key={a.asset_class}>
                  <i style={{ background: palette[i] }} />
                  <span>{a.asset_class}</span>
                  <b>
                    {((a.market_value_usd / data.nav_usd) * 100).toFixed(0)}%
                  </b>
                </div>
              ))}
            </div>
          </div>
        </Panel>
        <Panel title="Daily P&L attribution" note="USD · linear factor model">
          <FactorChart calc={data.daily} />
          <div className="panel-footer">
            <span>Net daily contribution</span>
            <b className="negative">{money(data.daily.total_pnl_usd)}</b>
          </div>
        </Panel>
      </div>
      <div className="grid-main">
        <Panel title="Major risk exposures" note="Signed sensitivities">
          <div className="exposure-list">
            {[
              [
                "Interest-rate DV01",
                money(data.exposures.dv01_usd_per_bp) + "/bp",
                "Government rates",
              ],
              [
                "IG spread CS01",
                money(data.exposures.ig_cs01_usd_per_bp) + "/bp",
                "Investment-grade credit",
              ],
              [
                "HY spread CS01",
                money(data.exposures.hy_cs01_usd_per_bp) + "/bp",
                "High-yield credit",
              ],
              [
                "Equity delta",
                money(data.exposures.equity_delta_usd, true),
                "USD equivalent",
              ],
            ].map(([n, v, d]) => (
              <div key={n}>
                <span>
                  {n}
                  <small>{d}</small>
                </span>
                <strong>{v}</strong>
              </div>
            ))}
          </div>
        </Panel>
        <section className="ai-card">
          <div className="ai-icon">
            <Sparkles size={22} />
          </div>
          <span className="eyebrow">METIS INTELLIGENCE</span>
          <h2>
            Yields fell.
            <br />
            Why did the portfolio lose?
          </h2>
          <p>
            Connect risk exposures to economic drivers, historical experience,
            and what the numbers may miss.
          </p>
          <button className="primary" onClick={goAI} disabled={busy}>
            Explain the daily loss <ArrowRight size={16} />
          </button>
          <small>
            Uses configured provider · live/demo mode is labeled on each answer
          </small>
        </section>
      </div>
      <Panel title="Market brief" note={`${data.market.as_of} · illustrative`}>
        <p className="brief">{data.market.commentary}</p>
      </Panel>
    </div>
  );
}
const gridTheme = themeQuartz.withParams({
  backgroundColor: "#101722",
  foregroundColor: "#cbd5e1",
  headerBackgroundColor: "#151f2e",
  headerTextColor: "#91a1b7",
  borderColor: "#253044",
  rowHoverColor: "#1b293b",
  accentColor: "#52d6bb",
  fontFamily: "Inter, system-ui, sans-serif",
  fontSize: 12,
  spacing: 6,
});
function PositionGrid({
  positions,
  risk = false,
}: {
  positions: Position[];
  risk?: boolean;
}) {
  const [filter, setFilter] = useState("");
  const currency = (p: { value: number }) => money(p.value);
  const cols: ColDef<Position>[] = [
    { field: "id", headerName: "ID", width: 100, pinned: "left" },
    { field: "name", headerName: "Position", minWidth: 260, flex: 2 },
    { field: "asset_class", headerName: "Asset class", minWidth: 180 },
    ...(risk
      ? ([
          {
            field: "dv01_usd_per_bp",
            headerName: "DV01 · $/bp",
            valueFormatter: currency,
            width: 140,
          },
          {
            field: "cs01_usd_per_bp",
            headerName: "CS01 · $/bp",
            valueFormatter: currency,
            width: 140,
          },
          {
            field: "equity_delta_usd",
            headerName: "Equity Δ · USD",
            valueFormatter: currency,
            width: 150,
          },
          {
            field: "fx_delta_usd",
            headerName: "FX Δ · USD",
            valueFormatter: currency,
            width: 150,
          },
        ] as ColDef<Position>[])
      : ([
          {
            field: "market_value_usd",
            headerName: "Mark · USD",
            valueFormatter: currency,
            width: 150,
          },
          {
            field: "notional_usd",
            headerName: "Notional · USD",
            valueFormatter: currency,
            width: 155,
          },
          { field: "instrument", headerName: "Instrument", width: 175 },
        ] as ColDef<Position>[])),
    {
      field: "pnl_usd",
      headerName: "Daily P&L · USD",
      valueFormatter: currency,
      width: 160,
      cellStyle: (p) => ({ color: p.value < 0 ? "#e78d9a" : "#52d6bb" }),
    },
  ];
  return (
    <>
      <div className="table-toolbar">
        <label>
          <span className="sr-only">Filter positions</span>
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Search positions, asset classes…"
          />
        </label>
        <span>
          {positions.length} positions · click headers to sort / filter
        </span>
      </div>
      <div className="position-grid">
        <AgGridReact<Position>
          theme={gridTheme}
          rowData={positions}
          columnDefs={cols}
          defaultColDef={{ sortable: true, filter: true, resizable: true }}
          quickFilterText={filter}
          getRowId={(p) => p.data.id}
          rowHeight={44}
          headerHeight={40}
        />
      </div>
    </>
  );
}
export function Portfolio({ data }: { data: Workstation }) {
  const snapshots = data.event_snapshots ?? [];
  const octoberSnapshot =
    snapshots.find((s) => s.id === "october-2026") ??
    snapshots[0];

  return (
    <div className="portfolio-tab">
      {octoberSnapshot ? (
        <section className="etf-portfolio portfolio-snapshot" aria-label="Portfolio snapshot">
          <h2>Portfolio snapshot · As of {octoberSnapshot.end}</h2>
          <p>
            <b>
              Estimated portfolio P&amp;L:{" "}
              {octoberSnapshot.estimated_pnl_usd === null ? (
                "Unavailable"
              ) : (
                <span className={eventPnlTone(octoberSnapshot.estimated_pnl_usd)}>
                  {eventMoney(octoberSnapshot.estimated_pnl_usd)}
                </span>
              )}
            </b>
            <br />
            Starting illustrative value {eventMoney(octoberSnapshot.start_nav_usd)} → ending illustrative value{" "}
            {eventMoney(octoberSnapshot.end_nav_usd)} · {octoberSnapshot.coverage_count}/12 rows.
            <br />
            <small className="context-note">
              Illustrative modeled P&amp;L, not observed account returns · MTD: Not available
            </small>
          </p>
          <EventTable snapshot={octoberSnapshot} />
        </section>
      ) : (
        <EtfPortfolio portfolio={data.etf_portfolio} history={data.etf_history} />
      )}

      <details className="portfolio-methodology-details">
        <summary>Methodology &amp; Assumptions · Preserved observed-price audit</summary>
        <div className="portfolio-audit-content">
          {octoberSnapshot && (
            <>
              <p>{octoberSnapshot.disclosure}</p>
              <p>
                <span className="badge">Observed input</span> Dated sourced market input ·{" "}
                <span className="badge amber">Estimated</span> Derived value with approximate inputs or
                hypothetical assumptions · <span className="badge">Unavailable</span> Missing required
                evidence.
              </p>
              <p>
                Dollar display rounded to the nearest $1,000; expandable inputs retain calculation precision.
                Rounded rows may not sum exactly. Zero cash P&amp;L is an explicit assumption.
              </p>
              <p>
                Market inputs: {octoberSnapshot.market_provenance?.provider}, downloaded{" "}
                {octoberSnapshot.market_provenance?.retrieved_at}. {octoberSnapshot.market_provenance?.timing}
              </p>
            </>
          )}
          <p className="context-note">
            <b>Observed-only ETF sleeve comparison:</b> On an observed-price-only basis (excluding
            modeled derivatives, OTC swaps, and unquoted Treasuries), covered price P&amp;L is{" "}
            <span className="negative">-$417,244.37</span> on $64,000,000.00 of starting allocations
            across 6 covered ETFs. Complete portfolio P&amp;L on an observed-price-only basis is
            Unavailable because non-ETF instruments lack daily secondary market quotes.
          </p>
          <EtfPortfolio
            portfolio={data.etf_portfolio}
            history={data.etf_history}
            title="Observed-price coverage audit · preserved evidence"
          />
        </div>
      </details>

      <details><summary>Archived October 30 fictional demonstration · original baskets and sensitivities</summary>
      <div className="metrics three">
        <Metric
          label="Net asset value"
          value={money(data.nav_usd, true)}
          detail="Includes signed derivative market values"
        />
        <Metric
          label="Opening NAV"
          value={money(data.opening_nav_usd, true)}
          detail="Closing NAV less modeled daily P&L"
        />
        <Metric
          label="Daily P&L"
          value={money(data.daily.total_pnl_usd)}
          detail="Fully attributed to four modeled factors"
          className="negative"
        />
      </div>
      <Panel title="Archived portfolio positions" note="Synthetic multi-asset portfolio · not ETF risk">
        <PositionGrid positions={data.positions} />
      </Panel>
      <div className="notice">
        <CircleHelp size={16} />
        <span>
          Marks, notionals and sensitivities are different measures. Swap P&L
          uses supplied DV01; FX forward P&L uses its directional USD delta.
          Signed marks contribute separately to NAV. All values are USD.
        </span>
      </div>
      </details>
    </div>
  );
}
export function getMarketSnapshotRows(
  snapshot?: EventSnapshot,
  portfolio?: EtfPortfolioType
) {
  if (!snapshot) return [];

  const ust2 = snapshot.positions.find((p) => p.id === "UST2");
  const irsp = snapshot.positions.find((p) => p.id === "IRS-P");
  const ust10 = snapshot.positions.find((p) => p.id === "UST10");
  const spy = snapshot.positions.find((p) => p.id === "SPY");
  const hefa = snapshot.positions.find((p) => p.id === "HEFA");
  const fx = snapshot.positions.find((p) => p.id === "FX-EUR");

  const spyFund = portfolio?.positions.find((p) => p.id === "SPY");

  // Rates
  const r2Start = ust2?.inputs[0]?.value ?? null;
  const r2End = ust2?.inputs[1]?.value ?? null;
  const r2ChgBp =
    r2Start !== null && r2End !== null ? (r2End - r2Start) * 100 : null;

  const r5Start = irsp?.inputs[0]?.value ?? null;
  const r5End = irsp?.inputs[1]?.value ?? null;
  const r5ChgBp =
    r5Start !== null && r5End !== null ? (r5End - r5Start) * 100 : null;

  const r10Start = ust10?.inputs[0]?.value ?? null;
  const r10End = ust10?.inputs[1]?.value ?? null;
  const r10ChgBp =
    r10Start !== null && r10End !== null ? (r10End - r10Start) * 100 : null;

  // Equities
  const spyStart = spy?.inputs[0]?.value ?? null;
  const spyEnd = spy?.inputs[1]?.value ?? null;
  const spyChgPct =
    spyStart !== null && spyEnd !== null && spyStart > 0
      ? (spyEnd / spyStart - 1) * 100
      : null;

  const hefaStart = hefa?.inputs[0]?.value ?? null;
  const hefaEnd = hefa?.inputs[1]?.value ?? null;
  const hefaChgPct =
    hefaStart !== null && hefaEnd !== null && hefaStart > 0
      ? (hefaEnd / hefaStart - 1) * 100
      : null;

  // Foreign Exchange
  const fxStart = fx?.inputs[0]?.value ?? null;
  const fxEnd = fx?.inputs[1]?.value ?? null;
  const fxChgPct =
    fxStart !== null && fxEnd !== null && fxStart > 0
      ? (fxEnd / fxStart - 1) * 100
      : null;

  // Credit spread assumptions
  const creditIgShock = snapshot.euro_ig_spread_change_bp ?? 0;
  const creditHyShock = snapshot.euro_hy_spread_change_bp ?? 0;

  return [
    {
      id: "DGS2",
      assetClass: "Government rates",
      instrument: "US Treasury 2Y yield",
      ticker: "DGS2",
      startFormatted: r2Start !== null ? `${r2Start.toFixed(2)}%` : "Unavailable",
      endFormatted: r2End !== null ? `${r2End.toFixed(2)}%` : "Unavailable",
      changeFormatted:
        r2ChgBp !== null
          ? `${r2ChgBp > 0 ? "+" : ""}${Math.round(r2ChgBp)}bp`
          : "Unavailable",
      changeTone:
        r2ChgBp !== null ? (r2ChgBp < 0 ? "negative" : r2ChgBp > 0 ? "positive" : "") : "",
      notes:
        "Federal Reserve Board H.15 daily constant-maturity indication; not a bond price quote.",
      sourceUrl: ust2?.inputs[0]?.source_url ?? "https://fred.stlouisfed.org/series/DGS2",
    },
    {
      id: "DGS5",
      assetClass: "Government rates",
      instrument: "US Treasury 5Y yield",
      ticker: "DGS5",
      startFormatted: r5Start !== null ? `${r5Start.toFixed(2)}%` : "Unavailable",
      endFormatted: r5End !== null ? `${r5End.toFixed(2)}%` : "Unavailable",
      changeFormatted:
        r5ChgBp !== null
          ? `${r5ChgBp > 0 ? "+" : ""}${Math.round(r5ChgBp)}bp`
          : "Unavailable",
      changeTone:
        r5ChgBp !== null ? (r5ChgBp < 0 ? "negative" : r5ChgBp > 0 ? "positive" : "") : "",
      notes:
        "Federal Reserve Board H.15 daily constant-maturity indication; not a bond price quote.",
      sourceUrl: irsp?.inputs[0]?.source_url ?? "https://fred.stlouisfed.org/series/DGS5",
    },
    {
      id: "DGS10",
      assetClass: "Government rates",
      instrument: "US Treasury 10Y yield",
      ticker: "DGS10",
      startFormatted: r10Start !== null ? `${r10Start.toFixed(2)}%` : "Unavailable",
      endFormatted: r10End !== null ? `${r10End.toFixed(2)}%` : "Unavailable",
      changeFormatted:
        r10ChgBp !== null
          ? `${r10ChgBp > 0 ? "+" : ""}${Math.round(r10ChgBp)}bp`
          : "Unavailable",
      changeTone:
        r10ChgBp !== null ? (r10ChgBp < 0 ? "negative" : r10ChgBp > 0 ? "positive" : "") : "",
      notes:
        "Federal Reserve Board H.15 daily constant-maturity indication; not a bond price quote.",
      sourceUrl: ust10?.inputs[0]?.source_url ?? "https://fred.stlouisfed.org/series/DGS10",
    },
    {
      id: "SPY",
      assetClass: "Equities",
      instrument: "SPY · US large-cap equities",
      ticker: "SPY",
      startFormatted: spyStart !== null ? `$${spyStart.toFixed(2)}` : "Unavailable",
      endFormatted: spyEnd !== null ? `$${spyEnd.toFixed(2)}` : "Unavailable",
      changeFormatted:
        spyChgPct !== null ? `${spyChgPct > 0 ? "+" : ""}${spyChgPct.toFixed(2)}%` : "Unavailable",
      changeTone:
        spyChgPct !== null ? (spyChgPct < 0 ? "negative" : spyChgPct > 0 ? "positive" : "") : "",
      notes:
        spyFund?.note ??
        "State Street SPDR S&P 500 ETF Trust; unadjusted secondary market close, price return only.",
      sourceUrl: spy?.inputs[0]?.source_url,
    },
    {
      id: "HEFA",
      assetClass: "Equities",
      instrument: "HEFA · Developed ex-US equities (USD hedged)",
      ticker: "HEFA",
      startFormatted: hefaStart !== null ? `$${hefaStart.toFixed(2)}` : "Unavailable",
      endFormatted: hefaEnd !== null ? `$${hefaEnd.toFixed(2)}` : "Unavailable",
      changeFormatted:
        hefaChgPct !== null ? `${hefaChgPct > 0 ? "+" : ""}${hefaChgPct.toFixed(2)}%` : "Unavailable",
      changeTone:
        hefaChgPct !== null ? (hefaChgPct < 0 ? "negative" : hefaChgPct > 0 ? "positive" : "") : "",
      notes:
        "iShares Currency Hedged MSCI EAFE ETF. HEFA represents USD-hedged developed ex-US exposure, not an unhedged index.",
      sourceUrl: hefa?.inputs[0]?.source_url,
    },
    {
      id: "EURUSD",
      assetClass: "Foreign exchange",
      instrument: "EUR/USD spot exchange rate",
      ticker: "DEXUSEU",
      startFormatted: fxStart !== null ? `${fxStart.toFixed(4)}` : "Unavailable",
      endFormatted: fxEnd !== null ? `${fxEnd.toFixed(4)}` : "Unavailable",
      changeFormatted:
        fxChgPct !== null ? `${fxChgPct > 0 ? "+" : ""}${fxChgPct.toFixed(2)}%` : "Unavailable",
      changeTone:
        fxChgPct !== null ? (fxChgPct < 0 ? "negative" : fxChgPct > 0 ? "positive" : "") : "",
      notes:
        "Federal Reserve Board H.10 New York noon buying rate in USD per EUR; observation clock differs from ETF 4:00 PM close.",
      sourceUrl: fx?.inputs[0]?.source_url ?? "https://fred.stlouisfed.org/series/DEXUSEU",
    },
    {
      id: "CREDIT-IG",
      assetClass: "Corporate credit",
      instrument: "Investment grade credit spread",
      ticker: "IG Spread",
      startFormatted: "Not available",
      endFormatted: "Not available",
      changeFormatted:
        creditIgShock > 0 ? `+${creditIgShock}bp (Assumed shock)` : "Not available",
      changeTone: creditIgShock > 0 ? "negative" : "",
      notes:
        creditIgShock > 0
          ? `Hypothetical model assumption (+${creditIgShock}bp euro IG spread shock), not an observed historical spread quote.`
          : "Dated historical spread quotes unavailable. Credit risk monitored via corporate bond ETF price returns (LQD).",
      sourceUrl: undefined,
    },
    {
      id: "CREDIT-HY",
      assetClass: "Corporate credit",
      instrument: "High yield credit spread",
      ticker: "HY Spread",
      startFormatted: "Not available",
      endFormatted: "Not available",
      changeFormatted:
        creditHyShock > 0 ? `+${creditHyShock}bp (Assumed shock)` : "Not available",
      changeTone: creditHyShock > 0 ? "negative" : "",
      notes:
        creditHyShock > 0
          ? `Hypothetical model assumption (+${creditHyShock}bp euro HY spread shock), not an observed historical spread quote.`
          : "Dated historical spread quotes unavailable. Credit risk monitored via corporate bond ETF price returns (HYG).",
      sourceUrl: undefined,
    },
  ];
}

export function Market({
  data,
  selectedEventId,
  onSelectEvent,
}: {
  data: Workstation;
  selectedEventId?: string;
  onSelectEvent?: (id: string) => void;
}) {
  const [localEventId, setLocalEventId] = useState(selectedEventId ?? "october-2026");
  const activeEventId = selectedEventId ?? localEventId;
  const snapshots = data.event_snapshots ?? [];
  const activeSnapshot =
    snapshots.find((s) => s.id === activeEventId) ??
    snapshots.find((s) => s.id === "october-2026") ??
    snapshots[0];

  const marketRows = getMarketSnapshotRows(activeSnapshot, data.etf_portfolio);

  const handleSelectEvent = (id: string) => {
    setLocalEventId(id);
    onSelectEvent?.(id);
  };

  return (
    <div className="market-tab">
      <div className="notice">
        <FlaskConical size={17} />
        <span>
          Market Monitor: coherent multi-asset market snapshot covering rates, credit, equities and FX for the selected historical event window.
          Benchmark comparison date: {data.market.previous_date}. Modeled benchmark fixtures are preserved in collapsed archived details below.
        </span>
      </div>

      {activeSnapshot && marketRows.length > 0 && (
        <Panel
          title={`Market snapshot · ${activeSnapshot.start} → ${activeSnapshot.end}`}
          note="Multi-asset historical comparison · Rates, equities, FX and credit"
        >
          {snapshots.length > 0 && (
            <div className="table-toolbar">
              <label>
                Historical event window:{" "}
                <select
                  value={activeSnapshot.id}
                  onChange={(e) => handleSelectEvent(e.target.value)}
                >
                  {snapshots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.id === "october-2026"
                        ? "October 2026 reference (Default)"
                        : s.id === "march-2025"
                          ? "March 2025 comparison"
                          : s.id === "cpi-2022"
                            ? "September 2022 CPI shock"
                            : `${s.start} → ${s.end} · ${s.title}`}
                    </option>
                  ))}
                </select>
              </label>
              <span className="context-note">
                Synchronized with Causal Scenario Exploration · Sourced FRED &amp; Yahoo Finance data
              </span>
            </div>
          )}

          <div className="etf-table-wrap">
            <table className="etf-table unified-market-table">
              <thead>
                <tr>
                  <th>Market / Instrument</th>
                  <th>
                    Starting level
                    <br />
                    {activeSnapshot.start}
                  </th>
                  <th>
                    Ending level or price
                    <br />
                    {activeSnapshot.end}
                  </th>
                  <th>Change</th>
                  <th>Provenance &amp; Mandate</th>
                </tr>
              </thead>
              <tbody>
                {marketRows.map((row) => (
                  <tr key={row.id} data-market-instrument={row.id}>
                    <td>
                      <b>{row.instrument}</b>
                      <br />
                      <small className="market-asset-class">{row.assetClass} · {row.ticker}</small>
                    </td>
                    <td>{row.startFormatted}</td>
                    <td>{row.endFormatted}</td>
                    <td>
                      {row.changeFormatted !== "Not available" && row.changeFormatted !== "Unavailable" ? (
                        <em
                          className={row.changeTone}
                          style={{ fontStyle: "normal", fontWeight: 600 }}
                        >
                          {row.changeFormatted}
                        </em>
                      ) : (
                        <span className="context-note">{row.changeFormatted}</span>
                      )}
                    </td>
                    <td>
                      <small>
                        {row.notes}{" "}
                        {row.sourceUrl && (
                          <a href={row.sourceUrl} target="_blank" rel="noreferrer">
                            Source
                          </a>
                        )}
                      </small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <details className="market-provenance-details">
            <summary>Sources, Provenance &amp; Observation Timing</summary>
            <div className="market-provenance-content">
              <p>
                <b>Treasury yields:</b> Federal Reserve Board H.15 daily constant-maturity indications (DGS2, DGS5, DGS10) via FRED. Constant-maturity yields are yield-curve benchmarks, not marketable Treasury bond quotes or prices.
              </p>
              <p>
                <b>Equity ETFs:</b> Sourced unadjusted secondary-market closing prices from Yahoo Finance. Price return only; distributions, splits, and cash flows excluded (not a total-return index). HEFA represents USD-hedged developed ex-US exposure (MSCI EAFE hedged to USD), not an unhedged index.
              </p>
              <p>
                <b>Foreign exchange:</b> Federal Reserve Board H.10 New York noon buying rate (DEXUSEU) in USD per EUR. Observation clock is noon ET, asynchronous with the 4:00 PM equity close.
              </p>
              <p>
                <b>Corporate credit spreads:</b> Quoted historical corporate bond option-adjusted spreads (OAS) are unavailable for these windows. September 2022 and March 2025 event models use explicit hypothetical euro credit spread shock assumptions (+15bp/+30bp and +10bp/+25bp); October 2026 relies on observed secondary-market ETF price returns (LQD, HYG).
              </p>
            </div>
          </details>
        </Panel>
      )}

      <details className="archived-market-details">
        <summary>Archived October 30 fictional demonstration · synthetic benchmarks</summary>
        <div className="archived-market-content">
          <p className="context-note" style={{ marginBottom: "16px" }}>
            The chart and benchmark table below contain synthetic multi-asset demonstration fixtures from the archived October 30 portfolio model. Modeled rates, credit spreads, and FX levels are not observed quotes.
          </p>
          <div className="grid-main">
            <Panel title="US Treasury yield curve (Archived synthetic demonstration)" note="Yield · %">
              <Chart
                data={[
                  {
                    type: "scatter",
                    mode: "lines+markers",
                    name: data.market.previous_date,
                    x: data.market.yields.map((y) => y.tenor),
                    y: data.market.yields.map((y) => y.previous_pct),
                    line: { color: "#5d7189", dash: "dot", width: 2 },
                    hovertemplate: "%{x}: %{y:.2f}%<extra>Previous</extra>",
                  },
                  {
                    type: "scatter",
                    mode: "lines+markers",
                    name: data.market.as_of,
                    x: data.market.yields.map((y) => y.tenor),
                    y: data.market.yields.map((y) => y.current_pct),
                    line: { color: "#52d6bb", width: 3 },
                    hovertemplate: "%{x}: %{y:.2f}%<extra>Selected date</extra>",
                  },
                ]}
                layout={{
                  showlegend: true,
                  legend: { orientation: "h", x: 0, y: 1.2 },
                  yaxis: {
                    gridcolor: "#232e3e",
                    ticksuffix: "%",
                  },
                }}
              />
            </Panel>
            <Panel
              title="Archived synthetic market benchmarks"
              note={`Fictional demonstration · As of ${data.market.as_of}`}
            >
              <div className="market-table">
                {data.market.yields.map((y) => (
                  <div key={y.tenor}>
                    <span>Treasury {y.tenor}</span>
                    <b>{y.current_pct.toFixed(2)}%</b>
                    <em>{((y.current_pct - y.previous_pct) * 100).toFixed(0)}bp</em>
                  </div>
                ))}
                {data.market.credit.map((c) => (
                  <div key={c.name}>
                    <span>{c.name} spread</span>
                    <b>{c.level_bp}bp</b>
                    <em className="negative">+{c.change_bp}bp</em>
                  </div>
                ))}
                {data.market.fx.map((f) => (
                  <div key={f.name}>
                    <span>{f.name}</span>
                    <b>{f.level.toFixed(4)}</b>
                    <em className="negative">{signed(f.change_pct, "%")}</em>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        </div>
      </details>

      <Panel title="Economic context" note="Assumed regime">
        <p className="brief">{data.market.commentary}</p>
      </Panel>
      <div className="section-title">
        <h2>Historical reference library</h2>
        <span>
          Historical facts + explicitly labeled portfolio interpretations
        </span>
      </div>
      <EpisodeCards episodes={data.history} />
    </div>
  );
}
function Risk({ data }: { data: Workstation }) {
  return (
    <>
      <ExposureMetrics data={data} />
      <div className="grid-main">
        <Panel title="P&L by risk factor" note="Modeled daily movement">
          <FactorChart calc={data.daily} />
        </Panel>
        <Panel title="P&L by position" note="USD · daily">
          <Chart
            data={[
              {
                type: "bar",
                orientation: "h",
                y: data.positions.map((p) => p.id).reverse(),
                x: data.positions.map((p) => p.pnl_usd).reverse(),
                marker: {
                  color: data.positions
                    .map((p) => (p.pnl_usd < 0 ? "#e78d9a" : "#52d6bb"))
                    .reverse(),
                },
                hovertemplate: "%{y}<br>$%{x:,.0f}<extra></extra>",
              },
            ]}
            layout={{
              xaxis: {
                gridcolor: "#232e3e",
                tickprefix: "$",
                tickformat: ".2s",
              },
            }}
          />
        </Panel>
      </div>
      <Panel
        title="Daily calculation evidence"
        note="Rate and spread legs are separate"
      >
        <PositionEvidence calculation={data.daily} exposures={data.exposures} />
      </Panel>
      <Panel
        title="Position-level risk inventory"
        note="USD reporting currency"
      >
        <PositionGrid positions={data.positions} risk />
      </Panel>
      <Panel title="Conventions and model boundaries">
        <div className="conventions">
          <p>
            <b>Rates / spreads</b> Positive DV01 and CS01 mean a gain for a 1bp
            fall. Rate P&L = −DV01 × yield shock (bp). Spread P&L = −CS01 × the
            position’s IG or HY spread shock (bp). Credit bonds have both rate
            and spread exposure.
          </p>
          <p>
            <b>Equity / FX</b> P&L = USD delta × shock (%) ÷ 100. Positive FX
            delta means long EUR against USD. Hedged baskets have zero residual
            FX exposure by assumption.
          </p>
          <p>
            <b>Accounting</b> End-of-day NAV is the sum of signed position
            marks. Opening NAV = closing NAV − daily modeled P&L. Cash includes
            collateral; no external flows, carry, fees or residual P&L are
            assumed.
          </p>
          <p>
            <b>Limits</b> Constant first-order sensitivities, parallel yield
            moves and a common equity return. No curve basis, convexity, option
            greeks, defaults, funding, liquidity or full derivative pricing.
            Dollar contributions rounded to cents; displayed totals rounded to
            dollars.
          </p>
        </div>
      </Panel>
    </>
  );
}
const shockLabels: Record<
  keyof Shocks,
  { label: string; unit: string; min: number; max: number; step: number }
> = {
  rates_bp: {
    label: "Government yields",
    unit: "bp",
    min: -300,
    max: 300,
    step: 5,
  },
  ig_bp: {
    label: "IG credit spreads",
    unit: "bp",
    min: -300,
    max: 500,
    step: 5,
  },
  hy_bp: {
    label: "HY credit spreads",
    unit: "bp",
    min: -500,
    max: 1500,
    step: 10,
  },
  equity_pct: {
    label: "Equity markets",
    unit: "%",
    min: -60,
    max: 60,
    step: 1,
  },
  fx_pct: { label: "EUR/USD", unit: "%", min: -30, max: 30, step: 1 },
};
function Scenarios({
  data,
  shocks,
  setShocks,
  calc,
  pending,
  error,
  goAI,
  busy,
}: {
  data: Workstation;
  shocks: Shocks;
  setShocks: (s: Shocks) => void;
  calc: Calculation | null;
  pending: boolean;
  error: string;
  goAI: () => void;
  busy: boolean;
}) {
  const selected = data.scenarios.find(
    (s) => JSON.stringify(s.shocks) === JSON.stringify(shocks),
  );
  return (
    <>
      <div className="notice">
        <FlaskConical size={17} />
        <span>
          <b>3 · What could happen next?</b> Daily illustrative P&L:{" "}
          {money(data.daily.total_pnl_usd)} on {data.market.as_of}. The results
          below are a separate hypothetical stress, not a forecast.
        </span>
      </div>
      <div className="scenario-presets">
        {data.scenarios.map((s) => (
          <button
            key={s.id}
            className={selected?.id === s.id ? "preset active" : "preset"}
            onClick={() => setShocks({ ...s.shocks })}
          >
            <Activity size={17} />
            <b>{s.name}</b>
            <small>{s.description}</small>
          </button>
        ))}
      </div>
      <div className="scenario-layout">
        <Panel title="Shock assumptions" note={selected ? "Preset" : "Custom"}>
          <div className="shock-controls">
            {(Object.keys(shockLabels) as (keyof Shocks)[]).map((k) => {
              const m = shockLabels[k];
              return (
                <div key={k}>
                  <label htmlFor={k}>
                    {m.label}
                    <strong>
                      {shocks[k] > 0 ? "+" : ""}
                      {shocks[k]}
                      {m.unit}
                    </strong>
                  </label>
                  <input
                    id={k}
                    type="range"
                    min={m.min}
                    max={m.max}
                    step={Number.isInteger(shocks[k] / m.step) ? m.step : "any"}
                    value={shocks[k]}
                    onChange={(e) =>
                      setShocks({ ...shocks, [k]: Number(e.target.value) })
                    }
                  />
                  <div className="range-label">
                    <span>
                      {m.min}
                      {m.unit}
                    </span>
                    <span>0</span>
                    <span>
                      +{m.max}
                      {m.unit}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
          <button
            className="secondary"
            onClick={() =>
              setShocks({
                rates_bp: 0,
                ig_bp: 0,
                hy_bp: 0,
                equity_pct: 0,
                fx_pct: 0,
              })
            }
          >
            Reset all shocks to zero
          </button>
        </Panel>
        <div>
          <div className="stress-result" aria-live="polite">
            <span className="eyebrow">
              APPROXIMATE SCENARIO P&L · {selected?.name ?? "Custom shocks"}
            </span>
            {error ? (
              <p role="alert" className="negative">
                {error}
              </p>
            ) : pending || !calc ? (
              <div className="calculating">
                <LoaderCircle className="spin" /> Recalculating…
              </div>
            ) : (
              <>
                <strong className={tone(calc.total_pnl_usd)}>
                  {money(calc.total_pnl_usd)}
                </strong>
                <p>
                  {signed(calc.pnl_pct_nav, "%")} of current NAV · first-order
                  approximation
                </p>
              </>
            )}
            <button
              className="text-button"
              disabled={pending || !!error || busy || !calc}
              onClick={goAI}
            >
              Interpret this scenario with Metis <ArrowRight size={15} />
            </button>
          </div>
          {calc && !pending && !error && (
            <Panel title="Scenario attribution" note="USD">
              <FactorChart calc={calc} />
              <FactorEvidence calculation={calc} />
            </Panel>
          )}
        </div>
      </div>
      {calc && !pending && !error && (
        <Panel title="Scenario P&L by position" note="USD · selected shocks">
          <PositionEvidence calculation={calc} exposures={data.exposures} />
          <div className="scenario-positions">
            {calc.positions.map((p) => (
              <div key={p.id}>
                <span>{p.name}</span>
                <b className={tone(p.pnl_usd)}>{money(p.pnl_usd)}</b>
              </div>
            ))}
          </div>
        </Panel>
      )}
      <div className="notice">
        <CircleHelp size={17} />
        <span>
          Illustrative shocks, not forecasts or calibrated historical replays.
          Linear sensitivities can materially misstate losses under large moves.
          Selected shocks persist across pages for new stress investigations.
          Follow-ups retain their captured assumptions.
        </span>
      </div>
    </>
  );
}
const prompts = [
  "Given the portfolio's exposures, current market conditions, and relevant historical patterns, what are its principal risks, and why?",
  "Why is my portfolio losing money despite falling Treasury yields?",
  "Which historical market episodes are relevant to these exposures?",
  "How could a recession-driven rally differ from an inflation-driven rally?",
  "What vulnerabilities might conventional exposure measures overlook?",
];
function ReasoningPage({
  data,
  selectedDate,
  setSelectedDate,
  calc,
  pending,
  messages,
  question,
  setQuestion,
  busy,
  error,
  ask,
  goScenario,
  activeInvestigationId,
  setActiveInvestigationId,
}: {
  data: Workstation;
  selectedDate: string;
  setSelectedDate: (date: string) => void;
  calc: Calculation | null;
  pending: boolean;
  messages: Reasoning[];
  question: string;
  setQuestion: (q: string) => void;
  busy: boolean;
  error: string;
  ask: (q: string, focus?: InvestigationFocus) => Promise<void>;
  goScenario: () => void;
  activeInvestigationId: string | null;
  setActiveInvestigationId: (id: string) => void;
}) {
  const dailyData = dailySnapshot(data, selectedDate);
  const target = followupTarget(messages, activeInvestigationId);
  const investigations = messages.filter((m, i) => messages.findIndex(other => other.investigation_id === m.investigation_id) === i);
  return (
    <div className="reasoning-layout">
      <div className="conversation">
        <div className="reasoning-intro">
          <div className="ai-icon">
            <BrainCircuit size={24} />
          </div>
          <div>
            <span className="eyebrow">ECONOMIC INVESTIGATION</span>
            <h2>From portfolio moves to competing explanations.</h2>
            <p>
              See what happened, what might explain it, and which evidence to investigate next.
            </p>
          </div>
        </div>
        <DefaultInvestigationDate investigation={data.investigation} selectedDate={selectedDate}
          onSelect={setSelectedDate} disabled={busy} />
        <section className="reasoning-actions">
          <div>
            <button className="primary" disabled={busy}
              aria-describedby="historical-option-description"
              onClick={() => void ask(historicalQuestion, "historical")}>
              Investigate a Historical Event
            </button>
            <p id="historical-option-description" className="context-note">
              September 13, 2022 · US CPI surprise. Examine how historical market movements would affect the synthetic portfolio and explore competing macroeconomic explanations.
            </p>
          </div>
          <div>
            <button
              className="primary"
              onClick={() => void ask(dailyQuestion, "daily")}
              disabled={busy}
              aria-describedby="daily-option-description"
            >
              Explain {dailyData.market.as_of} Synthetic P&L <ArrowRight size={15} />
            </button>
            <p id="daily-option-description" className="context-note">
              Investigate the {dailyData.market.as_of} fictional snapshot. Its holdings, market moves and calculated P&L are synthetic.
            </p>
          </div>
          <div>
            <button className="secondary" disabled={busy || pending || !calc}
              aria-describedby="stress-option-description"
              onClick={() => void ask(scenarioQuestion, "scenario")}>
              Explain Current Stress Scenario
            </button>
            <p id="stress-option-description" className="context-note">
              Understand how the portfolio responds to the currently selected stress assumptions.
            </p>
          </div>
          <div>
            <button className="secondary" onClick={goScenario}
              aria-describedby="what-if-option-description">
              Explore What-If Scenarios
            </button>
            <p id="what-if-option-description" className="context-note">
              Change market assumptions and see how they affect portfolio P&L.
            </p>
          </div>
        </section>
        {busy && (
          <div className="notice" role="status">
            <LoaderCircle className="spin" size={17} />
            <span>
              Interpreting portfolio, market, scenario and historical context…
            </span>
          </div>
        )}
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {messages.length === 0 && (
          <div className="prompt-list">
            {prompts.map((q) => (
              <button
                key={q}
                disabled={busy || pending || !calc}
                onClick={() => void ask(q)}
              >
                {q}
                <ChevronRight size={16} />
              </button>
            ))}
          </div>
        )}
        {[...messages].reverse().map((m, displayedIndex) => {
          const i = messages.length - 1 - displayedIndex;
          return (
            <article className="reasoning-answer" key={i}>
              <details className="user-question">
                <summary>
                  <span className="eyebrow">
                    {m.investigation_scope === "daily"
                      ? "DAILY LOSS INVESTIGATION"
                      : m.investigation_scope === "scenario"
                        ? "HYPOTHETICAL SCENARIO INVESTIGATION"
                        : m.investigation_scope === "historical"
                          ? "HISTORICAL CPI INVESTIGATION"
                          : "YOUR QUESTION"}
                  </span> · View question
                </summary>
                <p>{m.question}</p>
              </details>
              <div className="answer-header">
                <Sparkles size={17} />
                <b>Metis interpretation</b>
                <span className={m.mode === "demo" ? "badge amber" : "badge"}>
                  {m.mode === "demo"
                    ? "DETERMINISTIC DEMO"
                    : `LIVE ${m.mode.toUpperCase()} · ${m.model}`}
                </span>
              </div>
              <InvestigationResults answer={m} investigationId={i === messages.length - 1 ? "investigation-findings" : undefined} />
              <button className="text-button" disabled={busy} onClick={() => {
                setActiveInvestigationId(m.investigation_id);
                document.getElementById("followup-composer")?.scrollIntoView({ behavior: "smooth" });
              }}>Continue this investigation</button>
              <button className="text-button" onClick={goScenario}>
                3 · Explore or adjust a hypothetical stress{" "}
                <ArrowRight size={15} />
              </button>
            </article>
          );
        })}
        <section className="verification-examples" aria-label="Demonstration examples">
          <VerificationDemo />
        </section>
        <form
          className="composer"
          id="followup-composer"
          onSubmit={(e) => {
            e.preventDefault();
            void ask(question);
          }}
        >
          {target ? <>
            <label htmlFor="followup-target">Continue captured investigation</label>
            <select id="followup-target" value={target.investigation_id} disabled={busy}
              onChange={e => setActiveInvestigationId(e.target.value)}>
              {investigations.map((m, i) => <option key={m.investigation_id} value={m.investigation_id}>
                {i + 1} · {scopeLabel(m)}
              </option>)}
            </select>
            <InvestigationScope answer={target} label="Follow-up scope" />
          </> : <p className="context-note">New daily investigation of the selected {dailyData.market.as_of} synthetic snapshot.</p>}
          <label className="sr-only" htmlFor="question">
            Ask Metis a portfolio question
          </label>
          <textarea
            id="question"
            maxLength={2000}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={target ? "Ask a follow-up within the captured scope…" : "Ask Metis about the selected synthetic daily scenario…"}
            rows={3}
            disabled={busy}
          />
          <div>
            <small>
              {target ? "Uses captured evidence and history from this investigation only. To analyze different assumptions, start a new investigation." : "Starts a new investigation; no earlier conversation is replayed."}
            </small>
            <button
              className="primary"
              disabled={busy || !question.trim()}
              type="submit"
            >
              <Send size={15} />
              {busy ? "Working…" : target ? "Ask follow-up" : "Start daily investigation"}
            </button>
          </div>
        </form>
      </div>
      <aside className="context-sidebar">
        <Panel title="Current controls" note="For new investigations">
          <span className="badge amber">SYNTHETIC DATA</span>
          <h3>{dailyData.portfolio_name}</h3>
          <div className="context-stat">
            <span>NAV</span>
            <b>{money(dailyData.nav_usd, true)}</b>
          </div>
          <div className="context-stat">
            <span>Daily P&L</span>
            <b className={tone(dailyData.daily.total_pnl_usd)}>{money(dailyData.daily.total_pnl_usd)}</b>
          </div>
          <div className="context-stat">
            <span>Market snapshot</span>
            <b>{dailyData.market.as_of}</b>
          </div>
          <h3>Current hypothetical scenario</h3>
          <p className="context-note">
            Uses the app-wide {data.market.as_of} synthetic holdings when starting a new stress investigation, independently of the daily selector. Existing answers and follow-ups use their captured evidence.
          </p>
          {calc && !pending ? (
            <>
              <div className="context-stat">
                <span>Scenario P&L</span>
                <b className={tone(calc.total_pnl_usd)}>
                  {money(calc.total_pnl_usd)}
                </b>
              </div>
              {(Object.keys(shockLabels) as (keyof Shocks)[]).map((k) => (
                <div className="context-stat" key={k}>
                  <span>{shockLabels[k].label}</span>
                  <b>{signed(calc.shocks[k], shockLabels[k].unit)}</b>
                </div>
              ))}
            </>
          ) : (
            <p>Updating scenario…</p>
          )}
          <h3>Historical library</h3>
          {data.history.map((h) => (
            <p key={h.id} className="context-history">
              {h.title}
              <small>{h.period}</small>
            </p>
          ))}
          <div className="notice compact">
            Mode is labeled on each response. Demo uses deterministic templates;
            live mode requires server configuration.
          </div>
        </Panel>
      </aside>
    </div>
  );
}
export function MarketTicker({ data }: { data: Workstation }) {
  const y = data.market.yields.find((y) => y.tenor === "10Y")!;
  const movement = (y.current_pct - y.previous_pct) * 100;
  return (
    <div className="ticker">
      <span className="ticker-label">MARKET SNAPSHOT · {data.market.as_of}</span>
      <span>
        UST {y.tenor} <b>{y.current_pct.toFixed(2)}%</b>
        <em>
          {movement > 0 ? "+" : ""}
          {movement.toFixed(0)}bp
        </em>
      </span>
      {data.market.credit.map((c, i) => (
        <span key={c.name}>
          {i === 0 ? "IG" : "HY"} SPREAD <b>{c.level_bp}bp</b>
          <em className={c.change_bp > 0 ? "negative" : ""}>
            {c.change_bp > 0 ? "+" : ""}
            {c.change_bp}bp
          </em>
        </span>
      ))}
      <span>
        US EQUITY{" "}
        <em className={tone(data.market.equities[0].change_pct)}>
          {signed(data.market.equities[0].change_pct, "%")}
        </em>
      </span>
      <span>
        EUR/USD <b>{data.market.fx[0].level.toFixed(4)}</b>
        <em className={tone(data.market.fx[0].change_pct)}>
          {signed(data.market.fx[0].change_pct, "%")}
        </em>
      </span>
      <span className="ticker-example">ILLUSTRATIVE · NOT LIVE</span>
    </div>
  );
}
export default function App() {
  const [page, setPage] = useState(() => {
    if (typeof window !== "undefined" && window.location?.search) {
      const p = new URLSearchParams(window.location.search).get("page");
      if (p !== null && !isNaN(Number(p))) return Number(p);
    }
    return 0;
  });
  const [causalState, setCausalState] = useState(initialCausalState);
  const [historicalEventId, setHistoricalEventId] = useState<string>("october-2026");
  const [data, setData] = useState<Workstation | null>(null);
  const [selectedDate, setSelectedDate] = useState("");
  const selectedDaily = data ? dailySnapshot(data, selectedDate || data.investigation.default_date) : null;
  const displayData = data && page === 6 && selectedDaily ? { ...data, ...selectedDaily } : data;
  const [error, setError] = useState("");
  const [shocks, setShocks] = useState<Shocks | null>(null);
  const [calc, setCalc] = useState<Calculation | null>(null);
  const [pending, setPending] = useState(true);
  const [scenarioError, setScenarioError] = useState("");
  const [messages, setMessages] = useState<Reasoning[]>([]);
  const [activeInvestigationId, setActiveInvestigationId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [reasoningBusy, setReasoningBusy] = useState(false);
  const [reasoningError, setReasoningError] = useState("");
  const requestInFlight = useRef(false);
  function navigate(next: number, anchor?: string) {
    setPage(next);
    requestAnimationFrame(() => {
      if (anchor)
        document
          .getElementById(anchor)
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      else window.scrollTo({ top: 0 });
    });
  }
  async function ask(q: string, focus: InvestigationFocus = "question", dailyDate = selectedDate) {
    if (!data || requestInFlight.current || !q.trim()) return;
    navigate(6);
    setQuestion(q);
    setReasoningError("");
    const isFollowup = focus === "question" && messages.length > 0;
    if (focus === "question" && !isFollowup) focus = "daily";
    if (!isFollowup && focus !== "daily" && focus !== "historical" && (pending || scenarioError || !calc)) {
      setReasoningError(scenarioError || "Wait for the selected hypothetical scenario to finish calculating.");
      return;
    }
    requestInFlight.current = true;
    setReasoningBusy(true);
    try {
      const result = await api<Reasoning>(
        "reasoning",
        investigationRequest(focus, q,
          dailySnapshot(data, dailyDate).daily,
          calc, messages, activeInvestigationId, dailyDate),
      );
      setMessages((previous) => [
        ...previous,
        { ...result, investigation_focus: result.investigation_scope },
      ]);
      setActiveInvestigationId(result.investigation_id);
      setQuestion("");
    } catch (e) {
      setReasoningError((e as Error).message);
    } finally {
      requestInFlight.current = false;
      setReasoningBusy(false);
    }
  }
  useEffect(() => {
    const c = new AbortController();
    api<Workstation>("workstation", undefined, c.signal)
      .then((d) => {
        setData(d);
        setSelectedDate(d.investigation.default_date);
        setShocks(d.scenarios[3].shocks);
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => c.abort();
  }, []);
  useEffect(() => {
    if (!shocks) return;
    const c = new AbortController();
    setPending(true);
    setScenarioError("");
    const timer = setTimeout(() => {
      api<Calculation>("scenario", shocks, c.signal)
        .then((r) => {
          setCalc(r);
          setPending(false);
        })
        .catch((e) => {
          if (e.name !== "AbortError") {
            setScenarioError(e.message);
            setPending(false);
          }
        });
    }, 150);
    return () => {
      clearTimeout(timer);
      c.abort();
    };
  }, [shocks]);
  const changeShocks = (s: Shocks) => {
    setPending(true);
    setShocks(s);
  };
  return (
    <div className="workstation">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate(0);
          }}
        >
          <div className="brand-mark">M</div>
          <div>
            metis<span>RISK INTELLIGENCE</span>
          </div>
        </a>
        <div className="workspace-label">
          WORKSPACE <span>v0.7</span>
        </div>
        <nav aria-label="Main navigation">
          {pages.map((p, i) => (
            <button
              key={p.name}
              onClick={() => navigate(i)}
              aria-label={p.name}
              title={p.name}
              className={page === i ? "nav-item selected" : "nav-item"}
              aria-current={page === i ? "page" : undefined}
            >
              <p.icon size={18} />
              <span>{p.name}</span>
              {i === 6 && <span className="ai-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="environment">
            <span className="status-dot" /> LOCAL WORKSTATION
          </div>
          <p>
            <ShieldCheck size={14} /> Research & demonstration
          </p>
          <small>
            Synthetic positions. Illustrative markets.
            <br />
            No trading or order execution.
          </small>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div>
            <span className="muted">Workspace</span>
            <ChevronRight size={13} />
            <b>{pages[page].name}</b>
          </div>
          <div className="topbar-right">
            <span className="date">
              {page === 7 ? "Research archive" : displayData?.market.as_of ?? "Loading snapshot"}
            </span>
            <div className="avatar">MG</div>
          </div>
        </header>
        {displayData && <MarketTicker data={displayData} />}
        <main className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                {page === 7 ? "METIS RESEARCH / METHODS & LIMITATIONS" : <>GLOBAL OPPORTUNITIES <span>/</span> USD BASE</>}
              </div>
              <h1>{pages[page].name}</h1>
              <p>{subtitles[page]}</p>
            </div>
            <div className="snapshot-tag">
              <span className="status-dot" />{" "}
              {page === 7
                ? "Documented studies"
                : data
                  ? `${displayData!.positions.length} synthetic positions · ${displayData!.market.as_of}`
                  : "Connecting to backend"}
            </div>
          </div>
          {data && page !== 7 && <p className="context-note">{page === 1
            ? 'ETF allocation uses illustrative October dollar weights with separately sourced price observations. Archived demonstrations retain synthetic basket risk and P&L.'
            : data.investigation.disclosure + ' Archived basket demonstration; ETF allocation and observed price returns are on Portfolio.'}</p>}
          {page === 7 ? (
            <ResearchLimitations />
          ) : error ? (
            <div role="alert" className="error">
              Could not load workstation: {error} Start the backend on port
              8000, then reload.
            </div>
          ) : !data || !shocks ? (
            <div className="loading">
              <LoaderCircle className="spin" /> Loading portfolio and market
              context…
            </div>
          ) : (
            <>
              {page !== 6 && <nav
                className="investigation-trail"
                aria-label="Risk investigation"
              >
                <button
                  onClick={() => navigate(0)}
                  aria-current={page === 0 ? "step" : undefined}
                >
                  <b>1</b>
                  <span>
                    What happened?<small>Daily calculation</small>
                  </span>
                </button>
                <button
                  onClick={() => navigate(6)}
                  aria-current={page === 6 ? "step" : undefined}
                >
                  <b>2</b>
                  <span>
                    Why did it happen?<small>Metis interpretation</small>
                  </span>
                </button>
                <button
                  onClick={() => navigate(4)}
                  aria-current={page === 4 ? "step" : undefined}
                >
                  <b>3</b>
                  <span>
                    What could happen next?<small>Hypothetical stresses</small>
                  </span>
                </button>
                <button
                  onClick={() => navigate(6, "investigation-findings")}
                  disabled={messages.length === 0}
                >
                  <b>4</b>
                  <span>
                    What deserves investigation?
                    <small>Evidence & missing inputs</small>
                  </span>
                </button>
              </nav>}
              {page === 0 && (
                <Overview
                  data={data}
                  goAI={() => void ask(dailyQuestion, "daily", data.market.as_of)}
                  goRisk={() => navigate(3)}
                  goCausal={() => navigate(5)}
                  busy={reasoningBusy}
                />
              )}
              {page === 1 && <Portfolio data={data} />}{" "}
              {page === 2 && (
                <Market
                  data={data}
                  selectedEventId={historicalEventId}
                  onSelectEvent={(id) => {
                    setHistoricalEventId(id);
                    setCausalState((s) => ({ ...s, eventSnapshotId: id }));
                  }}
                />
              )}{" "}
              {page === 3 && <Risk data={data} />}{" "}
              {page === 4 && (
                <Scenarios
                  data={data}
                  shocks={shocks}
                  setShocks={changeShocks}
                  calc={calc}
                  pending={pending}
                  error={scenarioError}
                  goAI={() => void ask(scenarioQuestion, "scenario")}
                  busy={reasoningBusy}
                />
              )}
              {page === 5 && (
                <CausalExploration
                  state={causalState}
                  setState={setCausalState}
                  data={data}
                  generate={(request) => api("causal-exploration", request)}
                  calculate={(accepted) => api("scenario", accepted)}
                  useShocks={(accepted) => {
                    changeShocks(accepted);
                    navigate(4);
                  }}
                  selectedEventId={historicalEventId}
                  onSelectEvent={(id) => {
                    setHistoricalEventId(id);
                    setCausalState((s) => ({ ...s, eventSnapshotId: id }));
                  }}
                />
              )}
              {page === 6 && (
                <ReasoningPage
                  data={data}
                  selectedDate={selectedDate}
                  setSelectedDate={setSelectedDate}
                  calc={scenarioError ? null : calc}
                  pending={pending}
                  messages={messages}
                  question={question}
                  setQuestion={setQuestion}
                  busy={reasoningBusy}
                  error={reasoningError}
                  activeInvestigationId={activeInvestigationId}
                  setActiveInvestigationId={setActiveInvestigationId}
                  ask={ask}
                  goScenario={() => navigate(4)}
                />
              )}
            </>
          )}
          <footer>
            <span>
              METIS <span className="muted">/</span> FINANCIAL REASONING
              WORKSTATION
            </span>
            <span>Local example data · linear analytics · research use</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
