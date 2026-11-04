import type { Workstation } from "./types";

export function PortfolioSelection({ portfolios, selectedPortfolio, onSelect, disabled }: {
  portfolios: Workstation["portfolio_selections"];
  selectedPortfolio: string;
  onSelect: (id: string) => void;
  disabled: boolean;
}) {
  const selected = portfolios.find(item => item.id === selectedPortfolio);
  return <section className="captured-evidence" aria-label="Portfolio selection">
    <div className="daily-date-row">
      <label htmlFor="portfolio-selection">Portfolio Selection</label>
      <select id="portfolio-selection" value={selectedPortfolio} disabled={disabled}
        onChange={event => onSelect(event.target.value)}>
        {portfolios.map(portfolio => <option key={portfolio.id} value={portfolio.id}>{portfolio.label}</option>)}
      </select>
    </div>
    <p className="context-note">Demo environment — simulated portfolio and market data. Reference date: {selected?.reference_date}.</p>
    <p className="context-note">{selected?.construction}</p>
  </section>;
}
