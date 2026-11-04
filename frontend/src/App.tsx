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
import { PortfolioSelection } from "./PortfolioSelection";
import { CausalExploration } from "./CausalExploration";
import { ResearchLimitations } from "./ResearchLimitations";
import { EtfPortfolio } from "./EtfPortfolio";
import {
  EventSnapshots,
  EventTable,
  money as eventMoney,
  pnlTone as eventPnlTone,
} from "./EventSnapshots";
import { getMarketSnapshotRows, treasuryCurve } from "./market";
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
  portfolioSnapshot,
  scenarioQuestion,
  investigationRequest,
  followupTarget,
  scopeLabel,
  principalDrivers,
  answerPresentation,
  type DisplayedReasoning,
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
  { name: "Risk Sensitivity", icon: SlidersHorizontal },
  { name: "Causal Exploration", icon: FlaskConical },
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
          family: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', Inter, system-ui, sans-serif",
          color: "#475569",
          size: 11,
        },
        margin: { l: 65, r: 24, t: 16, b: 45 },
        xaxis: {
          gridcolor: "#f1f5f9",
          zerolinecolor: "#cbd5e1",
          automargin: true,
        },
        yaxis: {
          gridcolor: "#f1f5f9",
          zerolinecolor: "#cbd5e1",
          automargin: true,
        },
        showlegend: false,
        hoverlabel: { bgcolor: "#ffffff", font: { color: "#0f172a" }, bordercolor: "#cbd5e1" },
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
function FactorChart({ calc, readable = false }: { calc: Calculation; readable?: boolean }) {
  const entries = Object.entries(calc.by_factor);
  return (
    <Chart
      data={[
        {
          type: "bar",
          x: entries.map(([k]) => factorName[k]),
          y: entries.map(([, v]) => v),
          marker: {
            color: entries.map(([, v]) => (v < 0 ? "#dc2626" : "#047857")),
          },
          hovertemplate: "%{x}<br>$%{y:,.0f}<extra></extra>",
        },
      ]}
      layout={{
        ...(readable ? { font: { size: 14, color: "#334155" }, margin: { l: 80, r: 24, t: 20, b: 65 } } : {}),
        yaxis: {
          gridcolor: "#f1f5f9",
          tickprefix: "$",
          tickformat: ".2s",
          zerolinecolor: "#cbd5e1",
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
          detail="USD · daily movement"
          className={tone(data.daily.total_pnl_usd)}
        />
        <Metric
          label="Daily Return"
          value={signed(data.daily_return_pct, "%")}
          detail="Versus opening NAV"
          className={tone(data.daily_return_pct)}
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
            What drove the portfolio loss?
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
                    line: { color: "#ffffff", width: 3 },
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
                    font: { size: 25, color: "#0f172a" },
                  },
                  {
                    text: "NET ASSET VALUE",
                    x: 0.5,
                    y: 0.4,
                    showarrow: false,
                    font: { size: 9, color: "#64748b" },
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
  backgroundColor: "#ffffff",
  foregroundColor: "#0f172a",
  headerBackgroundColor: "#f8fafc",
  headerTextColor: "#475569",
  borderColor: "#e2e8f0",
  rowHoverColor: "#f1f5f9",
  accentColor: "#0f766e",
  fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', Inter, system-ui, sans-serif",
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
      cellStyle: (p) => ({ color: p.value < 0 ? "#dc2626" : "#047857" }),
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
          <table className="portfolio-summary" aria-label="Portfolio summary">
            <tbody>
              <tr>
                <th scope="row">Estimated portfolio P&amp;L</th>
                <td className={octoberSnapshot.estimated_pnl_usd === null ? "muted" : eventPnlTone(octoberSnapshot.estimated_pnl_usd)}>
                  {eventMoney(octoberSnapshot.estimated_pnl_usd)}
                </td>
              </tr>
              <tr>
                <th scope="row">Starting value</th>
                <td>{eventMoney(octoberSnapshot.start_nav_usd)}</td>
              </tr>
              <tr>
                <th scope="row">Ending value</th>
                <td>{eventMoney(octoberSnapshot.end_nav_usd)}</td>
              </tr>
              <tr>
                <th scope="row">Holdings covered</th>
                <td>{octoberSnapshot.coverage_count} / {octoberSnapshot.positions.length}</td>
              </tr>
            </tbody>
          </table>
          <p className="portfolio-summary-disclosure">
            Modeled estimate for demo purposes · Not live account returns
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
  const curve = treasuryCurve(marketRows);
  const driverMoves = (ids: string[]) => ids.map(id => marketRows.find(r => r.id === id)).filter(r => r !== undefined);

  const handleSelectEvent = (id: string) => {
    setLocalEventId(id);
    onSelectEvent?.(id);
  };

  return (
    <div className="market-tab">
      {activeSnapshot && marketRows.length > 0 && (
        <Panel
          title={`Market Prices & Rates · ${activeSnapshot.start} → ${activeSnapshot.end}`}
          note="Market measures for 12 illustrative holdings"
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
                Synchronized with Causal Exploration
              </span>
            </div>
          )}

          <p className="context-note market-measures-note">Cached market observations · Proxies labeled below. Position valuations remain in Portfolio.</p>
          <div className="etf-table-wrap">
            <table className="etf-table market-prices-table">
              <thead><tr>
                <th>Instrument</th><th>Market measure</th>
                <th>Starting<br />{activeSnapshot.start}</th>
                <th>Ending<br />{activeSnapshot.end}</th><th>Change</th>
              </tr></thead>
              <tbody>{marketRows.map(row => <tr key={row.id} data-market-position={row.id}>
                <td><b>{row.id}</b><span className="holding-label">{row.label}</span></td>
                <td><details className="market-measure-basis">
                  <summary>{row.measure}<span className="holding-label">{row.unit}</span></summary>
                  <p>{row.note}</p>
                  {row.sources.map((url, i) => <a key={url} href={url} target="_blank" rel="noreferrer">Source {row.sources.length > 1 ? i + 1 : ''} ↗ </a>)}
                </details></td>
                <td>{row.startFormatted}</td><td>{row.endFormatted}</td>
                <td className={row.tone || undefined}>{row.changeFormatted}</td>
              </tr>)}</tbody>
            </table>
          </div>
          <p className="context-note market-measures-note">Treasury yields proxy bond/swap market rates; swaps have no observed par quotes here. ETF changes are price returns. EUR/USD spot proxies the forward. Cash denotes a constant USD, not an account balance.</p>
        </Panel>
      )}
      {activeSnapshot && <div className="grid-main market-context-grid">
        <Panel title="Treasury yield curve" note={`${activeSnapshot.start} → ${activeSnapshot.end} · FRED constant-maturity yields`}>
          <Chart data={[
            { type: "scatter", mode: "lines+markers", name: activeSnapshot.start,
              x: curve.map(p => p.tenor), y: curve.map(p => p.start), connectgaps: false,
              line: { color: "#64748b", dash: "dot", width: 2 },
              hovertemplate: "%{x}: %{y:.2f}%<extra></extra>" },
            { type: "scatter", mode: "lines+markers", name: activeSnapshot.end,
              x: curve.map(p => p.tenor), y: curve.map(p => p.end), connectgaps: false,
              line: { color: "#0f766e", width: 3 },
              hovertemplate: "%{x}: %{y:.2f}%<extra></extra>" },
          ]} layout={{ showlegend: true, legend: { orientation: "h", x: 0, y: 1.18 },
            yaxis: { gridcolor: "#f1f5f9", ticksuffix: "%", title: { text: "Yield (%)" } },
          }} />
          <p className="context-note market-measures-note">DGS2 / DGS5 / DGS10 · Yield benchmarks, not bond prices. DGS5 proxies IRS-P; DGS10 also proxies IRS-R.</p>
        </Panel>
        <Panel title="Market drivers" note={`${activeSnapshot.start} → ${activeSnapshot.end}`}>
          <div className="market-drivers">
            <article><h3>Treasury yields</h3><p>{curve.map((p, i) => <span key={p.tenor}>{i > 0 && ' · '}{p.tenor} <b>{driverMoves(['UST2', 'IRS-P', 'UST10'])[i]?.changeFormatted}</b></span>)}</p></article>
            {[
              {title: 'Equity ETF prices', ids: ['SPY', 'HEFA']},
              {title: 'Credit ETF prices', ids: ['LQD', 'EUIG', 'HYG', 'EUHY']},
              {title: 'EUR/USD spot', ids: ['FX-EUR']},
            ].map(group => <article key={group.title}><h3>{group.title}</h3>
              <p>{driverMoves(group.ids).filter(r => r.change !== null).map((r, i) => <span key={r.id}>{i > 0 && ' · '}{r.id === 'FX-EUR' ? 'Spot' : r.id} <b className={r.tone}>{r.changeFormatted}</b></span>)}</p>
              {driverMoves(group.ids).some(r => r.change === null) && <small>{driverMoves(group.ids).filter(r => r.change === null).map(r => r.id).join(' / ')} quotes unavailable for this window.</small>}
            </article>)}
            <small>Credit ETF price returns include multiple market effects; they are not observed credit-spread changes. Movements do not identify their causes.</small>
          </div>
        </Panel>
      </div>}
      {activeSnapshot && <details className="market-provenance-details">
        <summary>Sources &amp; measure definitions</summary>
        <p>{activeSnapshot.market_provenance.provider}, downloaded {activeSnapshot.market_provenance.retrieved_at}. {activeSnapshot.market_provenance.timing}</p>
        <p>ETF closes: cached Yahoo Finance unadjusted USD/share observations; distributions excluded. March cache retrieved {activeSnapshot.march_etf_retrieved_at}; September/October use the existing cached records. Row details retain dated source links and eligibility notes.</p>
        <p>EUIG/EUHY quotes before their eligible listing/mandate are unavailable; hypothetical spread shocks used in Portfolio reconstructions are not market quotes. Measures correspond to illustrative holdings, not actual historical ownership. No live feed or observed forward/par-swap quotes.</p>
      </details>}

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
                    .map((p) => (p.pnl_usd < 0 ? "#dc2626" : "#047857"))
                    .reverse(),
                },
                hovertemplate: "%{y}<br>$%{x:,.0f}<extra></extra>",
              },
            ]}
            layout={{
              xaxis: {
                gridcolor: "#f1f5f9",
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
export function Scenarios({
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
  goAI: (question: string) => void;
  busy: boolean;
}) {
  const selected = data.historical_stress_presets.find(
    (s) => (Object.keys(s.shocks) as (keyof Shocks)[]).every((k) => s.shocks[k] === shocks[k]),
  );
  return (
    <div className="risk-sensitivity">
      <div className="notice">
        <FlaskConical size={17} />
        <span>
          <b>3 · What could happen next?</b> Daily illustrative P&L:{" "}
          {money(data.daily.total_pnl_usd)} on {data.market.as_of}. The results
          below are a separate hypothetical stress, not a forecast.
        </span>
      </div>
      <h2>Historical-event-inspired illustrative stress tests</h2>
      <p className="muted">
        Apply five-factor shocks to the current {data.market.as_of} illustrative
        portfolio ({data.positions.length} positions). Hypothetical P&L, not actual
        historic portfolio returns or a forecast. The sensitivity engine uses
        archived basket exposures, separately from the Portfolio ETF event estimates.
      </p>
      <div className="scenario-presets">
        {data.historical_stress_presets.map((s) => (
          <button
            key={s.id}
            className={selected?.id === s.id ? "preset active" : "preset"}
            onClick={() => setShocks({ ...s.shocks })}
          >
            <Activity size={17} />
            <b>{s.name}</b>
            <small>{s.window}</small>
            <small>{s.description}</small>
          </button>
        ))}
      </div>
      {selected && (
        <div className="notice">
          <CircleHelp size={17} />
          <span>
            <b>{selected.name} · {selected.window}.</b> {selected.basis}{" "}
            <a href={selected.source_url} target="_blank" rel="noreferrer">Event background</a>
            {" "}(background only; not a source for assumed shocks).
          </span>
        </div>
      )}
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
              HYPOTHETICAL PORTFOLIO P&L · {selected?.name ?? "Custom shocks"}
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
              onClick={() => goAI(selected ? `${scenarioQuestion} Historical-event-inspired illustrative stress: ${selected.name}, ${selected.window}. ${selected.basis} Applied to current illustrative holdings, not actual historic portfolio returns.` : scenarioQuestion)}
            >
              Interpret this scenario with Metis <ArrowRight size={15} />
            </button>
          </div>
          {calc && !pending && !error && (
            <Panel title="Scenario attribution" note="USD">
              <FactorChart calc={calc} readable />
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
    </div>
  );
}
const prompts = [
  "Given the portfolio's exposures, current market conditions, and relevant historical patterns, what are its principal risks, and why?",
  "Why is my portfolio losing money despite falling Treasury yields?",
  "Which positions and risk factors contributed most to the selected daily P&L?",
  "How could a recession-driven rally differ from an inflation-driven rally?",
  "What vulnerabilities might conventional exposure measures overlook?",
];
function ReasoningPage({
  data,
  selectedPortfolio,
  setSelectedPortfolio,
  shocks,
  setShocks,
  calc,
  pending,
  messages,
  question,
  setQuestion,
  busy,
  error,
  ask,
  activeInvestigationId,
  setActiveInvestigationId,
  askAnotherQuestion,
}: {
  data: Workstation;
  selectedPortfolio: string;
  setSelectedPortfolio: (id: string) => void;
  shocks: Shocks;
  setShocks: (shocks: Shocks) => void;
  calc: Calculation | null;
  pending: boolean;
  messages: DisplayedReasoning[];
  question: string;
  setQuestion: (q: string) => void;
  busy: boolean;
  error: string;
  ask: (q: string, focus?: InvestigationFocus) => Promise<void>;
  activeInvestigationId: string | null;
  setActiveInvestigationId: (id: string) => void;
  askAnotherQuestion: () => void;
}) {
  const dailyData = portfolioSnapshot(data, selectedPortfolio);
  const inflationPreset = data.historical_stress_presets.find((preset) => preset.id === "inflation-2022");
  const inflationSelected = inflationPreset && (Object.keys(inflationPreset.shocks) as (keyof Shocks)[]).every((key) => inflationPreset.shocks[key] === shocks[key]);
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
        <PortfolioSelection portfolios={data.portfolio_selections} selectedPortfolio={selectedPortfolio}
          onSelect={setSelectedPortfolio} disabled={busy} />
        {inflationPreset && <section className="captured-evidence" aria-label="Historical stress selection">
          <div className="daily-date-row">
            <label htmlFor="historical-stress-event">Historical Stress Scenario</label>
            <select id="historical-stress-event" value={inflationSelected ? inflationPreset.id : ""}
              disabled={busy || pending}
              onChange={(event) => { if (event.target.value === inflationPreset.id) setShocks({ ...inflationPreset.shocks }); }}>
              <option value="">Risk Sensitivity assumptions</option>
              <option value={inflationPreset.id}>2022 U.S. Inflation Shock — {inflationPreset.window}</option>
            </select>
          </div>
          <p className="context-note">Historical-style shocks on the portfolio, not a calibrated historical replay. Adjust shocks in Risk Sensitivity.</p>
        </section>}
        <section className="reasoning-actions">
          <div>
            <button
              className="primary"
              onClick={() => void ask(dailyQuestion, "daily")}
              disabled={busy}
              aria-describedby="daily-option-description"
            >
              Explain Daily Portfolio P&L <ArrowRight size={15} />
            </button>
            <p id="daily-option-description" className="context-note">
              Explain the portfolio's P&L for {dailyData.market.as_of}, including its key positions and risk drivers.
            </p>
          </div>
          <div>
            <button className="secondary" disabled={busy || pending || !calc}
              aria-describedby="stress-option-description"
              onClick={() => void ask(inflationSelected ? `${scenarioQuestion} Historical stress preset: ${inflationPreset.name}, ${inflationPreset.window}. ${inflationPreset.basis} Illustrative shocks, not historical portfolio returns.` : scenarioQuestion, "scenario")}>
              Analyze Stress Scenario
            </button>
            <p id="stress-option-description" className="context-note">
              Understand how the portfolio responds to the currently selected stress assumptions.
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
        <p id="preset-question-context" className="context-note">
          Preset questions start a new daily P&L investigation using the selected portfolio's daily snapshot. They do not apply the Historical Stress Scenario.
          After an investigation starts, use the follow-up question box to continue it. Follow-ups retain the investigation's captured portfolio and assumptions, including stress assumptions for stress investigations, even if you change the selectors.
        </p>
        {messages.length === 0 && (
          <div className="prompt-list" id="preset-questions" tabIndex={-1}>
            {prompts.map((q) => (
              <button
                key={q}
                disabled={busy}
                onClick={() => void ask(q, "preset")}
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
              <span className="eyebrow">
                {m.investigation_scope === "daily"
                  ? "DAILY LOSS INVESTIGATION"
                  : m.investigation_scope === "scenario"
                    ? "HYPOTHETICAL SCENARIO INVESTIGATION"
                    : m.investigation_scope === "historical"
                      ? "HISTORICAL CPI INVESTIGATION"
                      : "YOUR QUESTION"}
              </span>
              <div className="answer-header">
                <Sparkles size={17} />
                <b>Metis interpretation</b>
                <span className={m.mode === "demo" ? "badge amber" : "badge"}>
                  {m.mode === "demo"
                    ? "DETERMINISTIC DEMO"
                    : `LIVE ${m.mode.toUpperCase()} · ${m.model}`}
                </span>
              </div>
              <InvestigationResults answer={m} presentation={m.presentation} investigationId={i === messages.length - 1 ? "investigation-findings" : undefined} />
              <button className="text-button" disabled={busy} onClick={() => {
                setActiveInvestigationId(m.investigation_id);
                document.getElementById("followup-composer")?.scrollIntoView({ behavior: "smooth" });
              }}>Continue this investigation</button>
            </article>
          );
        })}
        {(messages.length > 0 || error) && <section className="reasoning-actions" aria-label="New question">
          <div>
            <button className="secondary" disabled={busy} onClick={askAnotherQuestion}>Ask another question</button>
            <p className="context-note">Clears this conversation and restores the presets. Your portfolio and scenario selections stay selected.</p>
          </div>
        </section>}
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
          </> : <p className="context-note">New daily investigation for {dailyData.market.as_of}.</p>}
          <label className="sr-only" htmlFor="question">
            Ask Metis a portfolio question
          </label>
          <textarea
            id="question"
            maxLength={2000}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={target ? "Ask a follow-up within the captured scope…" : "Ask Metis about the selected portfolio…"}
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
          <span className="badge amber">DEMO DATA</span>
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
            New stress investigations use {dailyData.portfolio_name} as of {dailyData.market.as_of}. Existing answers retain their captured evidence.
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
  const [selectedPortfolio, setSelectedPortfolio] = useState("current");
  const selectedDaily = data ? portfolioSnapshot(data, selectedPortfolio) : null;
  const displayData = data && page === 6 && selectedDaily ? { ...data, ...selectedDaily } : data;
  const [error, setError] = useState("");
  const [shocks, setShocks] = useState<Shocks | null>(null);
  const [calc, setCalc] = useState<Calculation | null>(null);
  const [portfolioCalc, setPortfolioCalc] = useState<Calculation | null>(null);
  const [pending, setPending] = useState(true);
  const [scenarioError, setScenarioError] = useState("");
  const [messages, setMessages] = useState<DisplayedReasoning[]>([]);
  const [activeInvestigationId, setActiveInvestigationId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [reasoningBusy, setReasoningBusy] = useState(false);
  const [reasoningError, setReasoningError] = useState("");
  const requestInFlight = useRef(false);
  function askAnotherQuestion() {
    if (requestInFlight.current) return;
    setMessages([]);
    setActiveInvestigationId(null);
    setQuestion("");
    setReasoningError("");
    requestAnimationFrame(() => {
      const presets = document.getElementById("preset-questions");
      presets?.focus();
      presets?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }
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
  async function ask(q: string, focus: InvestigationFocus = "question", dailyDate?: string) {
    if (!data || requestInFlight.current || !q.trim()) return;
    const portfolioId = page === 6 && !dailyDate ? selectedPortfolio : "current";
    const selectedCalc = portfolioId === selectedPortfolio ? portfolioCalc : calc;
    navigate(6);
    if ((page !== 6 || dailyDate) && selectedPortfolio !== "current") {
      setPending(true);
      setSelectedPortfolio("current");
    }
    setQuestion(q);
    setReasoningError("");
    const isFollowup = focus === "question" && messages.length > 0;
    if (focus === "question" && !isFollowup) focus = "daily";
    if (!isFollowup && focus !== "daily" && focus !== "preset" && focus !== "historical" && (pending || scenarioError || !selectedCalc)) {
      setReasoningError(scenarioError || "Wait for the selected hypothetical scenario to finish calculating.");
      return;
    }
    requestInFlight.current = true;
    setReasoningBusy(true);
    try {
      const presentation = answerPresentation(focus, messages, activeInvestigationId);
      const result = await api<Reasoning>(
        "reasoning",
        investigationRequest(focus, q,
          (dailyDate ? dailySnapshot(data, dailyDate) : portfolioSnapshot(data, portfolioId)).daily,
          selectedCalc, messages, activeInvestigationId, dailyDate, portfolioId),
      );
      setMessages((previous) => [
        ...previous,
        { ...result, investigation_focus: result.investigation_scope, presentation },
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
        setSelectedPortfolio("current");
        setShocks(d.historical_stress_presets[0].shocks);
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
      Promise.all([
        api<Calculation>("scenario", shocks, c.signal),
        api<Calculation>(`scenario?portfolio_id=${encodeURIComponent(selectedPortfolio)}`, shocks, c.signal),
      ]).then(([current, selected]) => {
          setCalc(current);
          setPortfolioCalc(selected);
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
  }, [shocks, selectedPortfolio]);
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
              {page === 7 ? "Research archive" : page === 2 ? data?.event_snapshots?.find(s => s.id === historicalEventId)?.end ?? "Event snapshot" : displayData?.market.as_of ?? "Loading snapshot"}
            </span>
            <div className="avatar">MG</div>
          </div>
        </header>
        {displayData && page !== 2 && <MarketTicker data={displayData} />}
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
                : page === 2
                  ? "12 illustrative holdings · Selected event window"
                : data
                  ? `${displayData!.positions.length} synthetic positions · ${displayData!.market.as_of}`
                  : "Connecting to backend"}
            </div>
          </div>
          {data && page !== 7 && page !== 2 && <p className="context-note">{page === 1
            ? 'ETF allocation uses illustrative October dollar weights with separately sourced price observations. Archived demonstrations retain synthetic basket risk and P&L.'
            : page === 4
            ? 'Current holdings, sensitivities and daily market ticker are synthetic. Event stress inputs are illustrative assumptions except the explicitly identified cached September benchmarks; modeled P&L is hypothetical.'
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
                  goAI={(q) => void ask(q, "scenario")}
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
                  selectedPortfolio={selectedPortfolio}
                  setSelectedPortfolio={(id) => { setPending(true); setSelectedPortfolio(id); }}
                  shocks={shocks}
                  setShocks={changeShocks}
                  calc={scenarioError ? null : portfolioCalc}
                  pending={pending}
                  messages={messages}
                  question={question}
                  setQuestion={setQuestion}
                  busy={reasoningBusy}
                  error={reasoningError}
                  activeInvestigationId={activeInvestigationId}
                  setActiveInvestigationId={setActiveInvestigationId}
                  ask={ask}
                  askAnotherQuestion={askAnotherQuestion}
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
