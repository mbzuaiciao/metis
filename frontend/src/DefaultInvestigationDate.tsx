import type { Workstation } from "./types";

export function DefaultInvestigationDate({ investigation }: { investigation: Workstation["investigation"] }) {
  return <section className="captured-evidence" aria-label="Default investigation date">
    <p><b>Default investigation · {investigation.default_date} · Data unavailable</b></p>
    <p className="context-note">{investigation.limitation}</p>
    <p className="context-note">No P&amp;L or economic explanation is available for this date. Choose an available investigation below.</p>
  </section>;
}
