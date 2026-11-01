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
import { ClaimVerification, VerificationDemo } from "./ClaimVerification";
import { InvestigationScope } from "./InvestigationScope";
import { CausalExploration } from "./CausalExploration";
import { ResearchLimitations } from "./ResearchLimitations";
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
  Position,
  Reasoning,
  Shocks,
  Workstation,
} from "./types";

import {
  FactorEvidence,
  PositionEvidence,
  InvestigationFindings,
} from "./InvestigationEvidence";
import {
  executivePreview,
  dailyQuestion,
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
  { name: "Scenario Analysis", icon: SlidersHorizontal },
  { name: "Metis AI Reasoning", icon: BrainCircuit },
  { name: "Research & Limitations", icon: BookOpen },
];
const subtitles = [
  "Your portfolio, in perspective.",
  "Positions, valuations and the exposures behind them.",
  "The market context behind portfolio performance.",
  "Understand the drivers. Look beyond the headline.",
  "Test the portfolio against a different market.",
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
function Overview({
  data,
  goAI,
  goRisk,
  busy,
}: {
  data: Workstation;
  goAI: () => void;
  goRisk: () => void;
  busy: boolean;
}) {
  const drivers = principalDrivers(data.daily);
  return (
    <>
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
        <button className="primary" onClick={goAI} disabled={busy}>
          {busy ? "Interpretation in progress…" : "2 · Explain the daily loss"}
          <ArrowRight size={16} />
        </button>
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
    </>
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
function Portfolio({ data }: { data: Workstation }) {
  return (
    <>
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
      <Panel title="Portfolio positions" note="Synthetic multi-asset portfolio">
        <PositionGrid positions={data.positions} />
      </Panel>
      <div className="notice">
        <CircleHelp size={16} />
        <span>
          Marks, notionals and sensitivities are different measures. Swap P&L
          uses supplied DV01; FX forward P&L uses $10m directional exposure, not
          its $2m mark. All values are USD.
        </span>
      </div>
    </>
  );
}
function Market({ data }: { data: Workstation }) {
  return (
    <>
      <div className="notice">
        <FlaskConical size={17} />
        <span>
          {data.market.label}. Comparison date: {data.market.previous_date}.
          Historical sources below are separate from these illustrative levels.
        </span>
      </div>
      <div className="grid-main">
        <Panel title="US Treasury yield curve" note="Yield · %">
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
                range: [3.8, 4.8],
              },
            }}
          />
        </Panel>
        <Panel title="Market observations" note="Illustrative daily changes">
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
            {data.market.equities.map((e) => (
              <div key={e.name}>
                <span>{e.name}</span>
                <b>Daily return</b>
                <em className="negative">{signed(e.change_pct, "%")}</em>
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
    </>
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
            <span className="eyebrow">2 · WHY DID IT HAPPEN?</span>
            <h2>Put your risk in context.</h2>
            <p>
              Ask about economic drivers, historical parallels, and the limits
              of measured exposure.
            </p>
          </div>
        </div>
        <section className="reasoning-actions">
          <button
            className="primary"
            onClick={() => void ask(dailyQuestion, "daily")}
            disabled={busy}
          >
            Start new daily investigation <ArrowRight size={15} />
          </button>
          <button className="secondary" disabled={busy || pending || !calc}
            onClick={() => void ask(scenarioQuestion, "scenario")}>
            Start new investigation of current stress
          </button>
          <button className="secondary" onClick={goScenario}>
            3 · Explore a hypothetical scenario
          </button>
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
        <VerificationDemo />
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
              <InvestigationScope answer={m} label="Answer scope" />
              <section className="executive-conclusion">
                <span className="eyebrow">WHAT MATTERS MOST · MODEL JUDGMENT</span>
                <p className="answer-summary">{executivePreview(m.interpretation.summary)}</p>
                {m.interpretation.summary.length > 480 && (
                  <details className="answer-section">
                    <summary>Executive excerpt above · read the full model summary</summary>
                    <p>{m.interpretation.summary}</p>
                  </details>
                )}
              </section>
              <details className="answer-section">
                <summary>Structured assertion checks · original prose Not checked</summary>
                <ClaimVerification results={m.verification} />
              </details>
              <div className="captured-evidence">
                <span className="eyebrow">
                  MEASURED DRIVERS & OFFSETS · BACKEND CALCULATIONS
                </span>
                <p>
                  Daily illustrative snapshot {m.context.market.as_of}:{" "}
                  <b>{money(m.context.daily.total_pnl_usd)}</b>.{" "}
                  {m.investigation_scope !== "daily" && (
                    <>
                      Hypothetical scenario:{" "}
                      <b>{money(m.context.scenario.total_pnl_usd)}</b>.
                    </>
                  )}
                </p>
                <FactorEvidence
                  calculation={
                    m.investigation_scope === "daily"
                      ? m.context.daily
                      : m.context.scenario
                  }
                />
                <PositionEvidence
                  id={`answer-evidence-${i}`}
                  calculation={
                    m.investigation_scope === "daily"
                      ? m.context.daily
                      : m.context.scenario
                  }
                  exposures={m.context.portfolio.exposures}
                />
              </div>
              <details className="answer-section">
                <summary>Economic interpretation · why the risks interact</summary>
                <p>{m.interpretation.economic_interpretation}</p>
              </details>
              {(
                [
                  [
                    "Principal observations · model claims to check against calculations",
                    m.interpretation.principal_risk_observations,
                  ],
                  [
                    "Historical analogies",
                    m.interpretation.historical_analogies,
                  ],
                ] as [string, string[]][]
              ).map(([title, items]) => (
                <details key={title} className="answer-section">
                  <summary>{title}</summary>
                  <ul>
                    {items.map((v, j) => (
                      <li key={j}>{v}</li>
                    ))}
                  </ul>
                </details>
              ))}
              <InvestigationFindings
                id={
                  i === messages.length - 1
                    ? "investigation-findings"
                    : undefined
                }
                items={m.interpretation.potential_vulnerabilities}
                uncertainties={m.interpretation.assumptions_and_uncertainties}
                evidenceId={`answer-evidence-${i}`}
              />
              <button className="text-button" disabled={busy} onClick={() => {
                setActiveInvestigationId(m.investigation_id);
                document.getElementById("followup-composer")?.scrollIntoView({ behavior: "smooth" });
              }}>Continue this investigation</button>
              <button className="text-button" onClick={goScenario}>
                3 · Explore or adjust a hypothetical stress{" "}
                <ArrowRight size={15} />
              </button>
              <div className="evidence">
                <h3>Supporting evidence</h3>
                {m.context.evidence
                  .filter((e) =>
                    m.interpretation.evidence_references.includes(e.id),
                  )
                  .map((e) =>
                    e.url ? (
                      <a
                        href={e.url}
                        key={e.id}
                        target="_blank"
                        rel="noreferrer"
                      >
                        [{e.id}] {e.description} ↗
                      </a>
                    ) : (
                      <span key={e.id}>
                        [{e.id}] {e.description}
                      </span>
                    ),
                  )}
              </div>
              <details>
                <summary>Inspect context and backend operations</summary>
                <p>
                  Application assembled this context before invocation. No
                  autonomous tool calls.
                </p>
                <pre>
                  {JSON.stringify(
                    { operations: m.context_operations, context: m.context },
                    null,
                    2,
                  )}
                </pre>
              </details>
            </article>
          );
        })}
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
          </> : <p className="context-note">New stress investigation using current scenario controls. To investigate the daily snapshot, select Start new daily investigation.</p>}
          <label className="sr-only" htmlFor="question">
            Ask Metis a portfolio question
          </label>
          <textarea
            id="question"
            maxLength={2000}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={target ? "Ask a follow-up within the captured scope…" : "Ask Metis about the current stress scenario…"}
            rows={3}
            disabled={busy}
          />
          <div>
            <small>
              {target ? "Uses captured evidence and history from this investigation only. To analyze different assumptions, start a new investigation." : "Starts a new investigation; no earlier conversation is replayed."}
            </small>
            <button
              className="primary"
              disabled={busy || (!target && (pending || !calc)) || !question.trim()}
              type="submit"
            >
              <Send size={15} />
              {busy ? "Working…" : target ? "Ask follow-up" : "Start stress investigation"}
            </button>
          </div>
        </form>
      </div>
      <aside className="context-sidebar">
        <Panel title="Current controls" note="For new investigations">
          <span className="badge amber">SYNTHETIC DATA</span>
          <h3>{data.portfolio_name}</h3>
          <div className="context-stat">
            <span>NAV</span>
            <b>{money(data.nav_usd, true)}</b>
          </div>
          <div className="context-stat">
            <span>Daily P&L</span>
            <b className="negative">{money(data.daily.total_pnl_usd)}</b>
          </div>
          <div className="context-stat">
            <span>Market snapshot</span>
            <b>{data.market.as_of}</b>
          </div>
          <h3>Current hypothetical scenario</h3>
          <p className="context-note">
            Used only when starting a new stress investigation. Existing answers and follow-ups use their captured evidence.
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
function MarketTicker({ data }: { data: Workstation }) {
  const y = data.market.yields.find((y) => y.tenor === "10Y")!;
  const movement = (y.current_pct - y.previous_pct) * 100;
  return (
    <div className="ticker">
      <span className="ticker-label">MARKET SNAPSHOT</span>
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
  const [page, setPage] = useState(0);
  const [scenarioMode, setScenarioMode] = useState<"independent" | "causal">("independent");
  const [causalState, setCausalState] = useState(initialCausalState);
  const [data, setData] = useState<Workstation | null>(null);
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
  async function ask(q: string, focus: InvestigationFocus = "question") {
    if (!data || requestInFlight.current || !q.trim()) return;
    navigate(5);
    setQuestion(q);
    setReasoningError("");
    const isFollowup = focus === "question" && messages.length > 0;
    if (!isFollowup && focus !== "daily" && (pending || scenarioError || !calc)) {
      setReasoningError(scenarioError || "Wait for the selected hypothetical scenario to finish calculating.");
      return;
    }
    requestInFlight.current = true;
    setReasoningBusy(true);
    try {
      const result = await api<Reasoning>(
        "reasoning",
        investigationRequest(focus, q, data.daily, calc, messages, activeInvestigationId),
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
              {i === 5 && <span className="ai-dot" />}
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
            <span className="badge amber">
              <FlaskConical size={12} /> EXAMPLE DATA
            </span>
            <span className="date">
              {page === 6 ? "Research archive" : data?.market.as_of ?? "Loading snapshot"}
            </span>
            <div className="avatar">MG</div>
          </div>
        </header>
        {data && <MarketTicker data={data} />}
        <main className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                {page === 6 ? "METIS RESEARCH / METHODS & LIMITATIONS" : <>GLOBAL OPPORTUNITIES <span>/</span> USD BASE</>}
              </div>
              <h1>{pages[page].name}</h1>
              <p>{subtitles[page]}</p>
            </div>
            <div className="snapshot-tag">
              <span className="status-dot" />{" "}
              {page === 6
                ? "Documented studies"
                : data
                  ? `${data.positions.length} positions · ${data.market.as_of}`
                  : "Connecting to backend"}
            </div>
          </div>
          {page === 6 ? (
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
              <nav
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
                  onClick={() => navigate(5)}
                  aria-current={page === 5 ? "step" : undefined}
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
                  onClick={() => navigate(5, "investigation-findings")}
                  disabled={messages.length === 0}
                >
                  <b>4</b>
                  <span>
                    What deserves investigation?
                    <small>Evidence & missing inputs</small>
                  </span>
                </button>
              </nav>
              {page === 0 && (
                <Overview
                  data={data}
                  goAI={() => void ask(dailyQuestion, "daily")}
                  goRisk={() => navigate(3)}
                  busy={reasoningBusy}
                />
              )}
              {page === 1 && <Portfolio data={data} />}{" "}
              {page === 2 && <Market data={data} />}{" "}
              {page === 3 && <Risk data={data} />}{" "}
              {page === 4 && (
                <>
                  <div className="scenario-modes" role="group" aria-label="Scenario mode">
                    <button className={scenarioMode === "independent" ? "secondary active" : "secondary"} aria-pressed={scenarioMode === "independent"} onClick={() => setScenarioMode("independent")}>Independent Shocks</button>
                    <button className={scenarioMode === "causal" ? "secondary active" : "secondary"} aria-pressed={scenarioMode === "causal"} onClick={() => setScenarioMode("causal")}>Causal Exploration</button>
                  </div>
                  {scenarioMode === "causal" ? (
                    <CausalExploration state={causalState} setState={setCausalState} data={data}
                      generate={request => api("causal-exploration", request)}
                      calculate={accepted => api("scenario", accepted)}
                      useShocks={accepted => { changeShocks(accepted); setScenarioMode("independent"); }} />
                  ) : (
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
                </>
              )}{" "}
              {page === 5 && (
                <ReasoningPage
                  data={data}
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
