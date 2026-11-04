import type { Workstation } from "./types";

export function DefaultInvestigationDate({ investigation, selectedDate, onSelect, disabled }: {
  investigation: Workstation["investigation"];
  selectedDate: string;
  onSelect: (date: string) => void;
  disabled: boolean;
}) {
  return <section className="captured-evidence" aria-label="Portfolio snapshot selection">
    <div className="daily-date-row">
      <label htmlFor="daily-investigation-date">Portfolio Snapshot</label>
      <select id="daily-investigation-date" value={selectedDate} disabled={disabled}
        onChange={event => onSelect(event.target.value)}>
        {investigation.snapshots.map(snapshot => <option key={snapshot.market.as_of} value={snapshot.market.as_of}>
          {snapshot.market.as_of === investigation.default_date ? "Current Portfolio" : "Previous Portfolio"} — {snapshot.market.as_of}
        </option>)}
      </select>
    </div>
    <p className="context-note">Demo environment — simulated portfolio and market data.</p>
  </section>;
}
