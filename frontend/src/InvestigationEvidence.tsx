import type { Calculation, Workstation } from "./types";
import { measuredContributions, vulnerabilityGuide } from "./investigation";

const usd = (v: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(v === 0 ? 0 : v);
const tone = (v: number) => (v < 0 ? "negative" : v > 0 ? "positive" : "muted");

export function FactorEvidence({ calculation, omittedCredit = false, hypothetical = false }: { calculation: Calculation; omittedCredit?: boolean; hypothetical?: boolean }) {
  const names: Record<string, string> = {
    rates_pnl: "Government rates",
    credit_pnl: "Credit spreads",
    equity_pnl: "Equities",
    fx_pnl: "FX",
  };
  return (
    <div className="factor-evidence">
      {measuredContributions(calculation).map(([key, value]) => (
        <div key={key}>
          <span>{names[key] ?? key}</span>
          <strong className={tone(value)}>{omittedCredit && key === "credit_pnl" ? "Unavailable" : usd(value)}</strong>
        </div>
      ))}
      <div className="evidence-net">
        <span>{omittedCredit ? "Partial-factor P&L · complete total unknown" : hypothetical ? "Estimated hypothetical P&L" : "Total portfolio P&L"}</span>
        <strong className={tone(calculation.total_pnl_usd)}>
          {usd(calculation.total_pnl_usd)}
        </strong>
      </div>
      {calculation.by_factor.rates_pnl > 0 && calculation.total_pnl_usd < 0 && (
        <p>
          Rates contributed a gain. The portfolio still lost money after the
          other factor contributions.
        </p>
      )}
    </div>
  );
}

export function PositionEvidence({
  calculation,
  omittedCredit = false,
  exposures,
  id,
}: {
  calculation: Calculation;
  omittedCredit?: boolean;
  exposures: Workstation["exposures"];
  id?: string;
}) {
  return (
    <details className="position-evidence" id={id}>
      <summary>Inspect position contributions and signed DV01</summary>
      <p>
        Backend calculations · USD. {omittedCredit ? "Partial-factor P&L excludes unknown spread contributions; zero engine placeholders are not observations." : "Net position P&L includes all four factors."}
        Positive DV01 gains on a 1bp yield decline; it is not P&L.
        CS01 is a first-order spread sensitivity. Instrument and asset-class
        DV01 views can overlap; do not add overlapping groups.
      </p>
      <div className="evidence-scroll">
        <table>
          <thead>
            <tr>
              <th>Position</th>
              <th>Rates</th>
              <th>Credit spreads</th>
              <th>Equities</th>
              <th>FX</th>
              <th>{omittedCredit ? "Partial-factor position P&L" : "Net position P&L"}</th>
              <th>DV01 · $/bp</th>
              <th>CS01 · $/bp</th>
              <th>Marked value</th>
              <th>Reference notional</th>
            </tr>
          </thead>
          <tbody>
            {calculation.positions.map((p) => (
              <tr key={p.id}>
                <th title={p.name}>
                  {p.id}
                  <small>{p.name}</small>
                </th>
                {[
                  p.rates_pnl,
                  p.credit_pnl,
                  p.equity_pnl,
                  p.fx_pnl,
                  p.pnl_usd,
                ].map((v, i) => (
                  <td className={tone(v)} key={i}>
                    {omittedCredit && i === 1 ? "Unavailable" : usd(v)}
                  </td>
                ))}
                <td>{usd(p.dv01_usd_per_bp)}</td>
                <td>{usd(p.cs01_usd_per_bp)}</td>
                <td>{usd(p.market_value_usd)}</td>
                <td>{usd(p.notional_usd)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th>{omittedCredit ? "Partial-factor totals" : "Portfolio totals"}</th>
              {[
                calculation.by_factor.rates_pnl,
                calculation.by_factor.credit_pnl,
                calculation.by_factor.equity_pnl,
                calculation.by_factor.fx_pnl,
                calculation.total_pnl_usd,
              ].map((v, i) => (
                <td key={i} className={tone(v)}>
                  {omittedCredit && i === 1 ? "Unavailable" : usd(v)}
                </td>
              ))}
              <td>{usd(exposures.dv01_usd_per_bp)}</td>
              <td>{usd(exposures.cs01_usd_per_bp)}</td>
              <td>—</td>
              <td>—</td>
            </tr>
          </tfoot>
        </table>
      </div>
      <p>
        Totals above are supplied by the backend. Credit-spread P&L is a factor
        contribution; {omittedCredit ? "here it is unavailable, so credit-position P&L shows only its rate leg." : "net credit-position P&L also includes the rate leg."} Swap
        notionals, marks and DV01 measure different things.
      </p>
    </details>
  );
}

export function InvestigationFindings({
  items,
  uncertainties,
  evidenceId,
  id,
}: {
  items: string[];
  uncertainties: string[];
  evidenceId: string;
  id?: string;
}) {
  return (
    <section className="investigation-findings" id={id}>
      <div className="section-title">
        <h2>4 · What deserves investigation?</h2>
      </div>
      <p className="muted">
        Unquantified vulnerabilities · shown in model order, not a measured risk ranking.
        Missing evidence prevents a reliable ranking of funding, liquidity,
        counterparty and default losses. Topic guides are analyst prompts, not verified findings.
      </p>
      {items.length === 0 && (
        <p>
          No vulnerabilities were returned. This does not establish that the
          portfolio has none.
        </p>
      )}
      {items.map((item, i) => {
        const prefix = item.split(":")[0];
        const guide = vulnerabilityGuide(prefix.length <= 90 ? prefix : "");
        const title = prefix.length <= 90 ? prefix : item.slice(0, 90) + "…";
        return (
          <details className="finding" key={i} open={i === 0}>
            <summary>
              {title}
              <small>Topic checklist: {guide.topic}</small>
            </summary>
            <div>
              <span className="eyebrow">CONCERN · MODEL HEADING / EXCERPT</span>
              <p>{title}</p>
              <details className="model-concern-detail">
                <summary>Read the full model concern, rationale and proposed investigation</summary>
                <p>{item}</p>
              </details>
              <span className="eyebrow">WHY IT MATTERS · ANALYTICAL FRAMING</span>
              <p>{guide.consequence}</p>
              <span className="eyebrow">
                AVAILABLE EVIDENCE · INSPECT FOR THIS CONCERN
              </span>
              <p>
                {guide.evidence}{" "}
                <a
                  href={`#${evidenceId}`}
                  onClick={() => {
                    const node = document.getElementById(evidenceId);
                    if (node instanceof HTMLDetailsElement) node.open = true;
                  }}
                >
                  Inspect calculations ↓
                </a>
              </p>
              <span className="eyebrow">
                NEXT INVESTIGATION · MISSING DATA / ANALYTICAL WORK
              </span>
              <p>{guide.missing}</p>
            </div>
          </details>
        );
      })}
      <details className="finding">
        <summary>Model assumptions and uncertainties</summary>
        <ul>
          {uncertainties.map((v, i) => (
            <li key={i}>{v}</li>
          ))}
        </ul>
      </details>
    </section>
  );
}

export function ShockEvidence({ calculation }: { calculation: Calculation }) {
  const labels: Record<string, string> = {
    rates_bp: "Government rates · bp",
    ig_bp: "IG spreads · bp",
    hy_bp: "HY spreads · bp",
    equity_pct: "Equities · %",
    fx_pct: "EUR/USD · %",
  };
  return (
    <div className="shock-evidence" aria-label="Captured shock assumptions">
      {Object.entries(calculation.shocks).map(([key, value]) => (
        <span key={key}>
          {labels[key]}{" "}
          <b>
            {value > 0 ? "+" : ""}
            {value}
          </b>
        </span>
      ))}
    </div>
  );
}
