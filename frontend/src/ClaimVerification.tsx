import { useEffect, useState } from "react";
import type { ClaimVerdict } from "./types";

export function ClaimVerification({ results = [] }: { results?: ClaimVerdict[] }) {
  return <div className="claim-verification">
    <p className="context-note">Checks apply only to the explicit mappings below. Original wording, economic explanations, omitted claims and evidence-ID validity alone are <b>Not checked</b>.</p>
    {results.length === 0 && <p>No structured assertions were submitted. No financial claims have been verified for this answer.</p>}
    {results.map((r, i) => <article className="claim-result" key={i}>
      <p className="context-note">Original statement · {r.original_wording_status} as unconstrained prose</p>
      <blockquote>{r.claim.statement}</blockquote>
      <div className="claim-result-heading"><b>Mapped assertion</b><span className={`claim-verdict ${r.verdict.toLowerCase().replaceAll(" ", "-")}`}>{r.verdict}</span></div>
      <p className="claim-mapping">{r.mapping}</p>
      <p>{r.explanation}</p>
      <details open><summary>Supporting backend evidence</summary>
        {r.evidence.length ? <dl>{r.evidence.map((e, j) => <div key={j}><dt>{e.path}</dt><dd>{typeof e.value === "number" ? e.value.toLocaleString("en-US", {maximumFractionDigits: 4}) : e.value}</dd></div>)}</dl> : <p>No supported calculation was matched.</p>}
      </details>
      <details><summary>Original structured claim</summary><pre>{JSON.stringify(r.claim, null, 2)}</pre></details>
      <details><summary>Limitations & missing information</summary><ul>{r.limitations.map((text, j) => <li key={j}>{text}</li>)}</ul></details>
    </article>)}
  </div>;
}

export function VerificationDemo() {
  const [results, setResults] = useState<ClaimVerdict[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/verification-demo", {signal: controller.signal}).then(async response => {
      if (!response.ok) throw new Error("Could not load the fixed verification examples.");
      const data: {results: ClaimVerdict[]} = await response.json();
      setResults(data.results);
    }).catch(e => { if (e.name !== "AbortError") setError(e.message); });
    return () => controller.abort();
  }, []);
  return <details className="verification-demo">
    <summary>Financial claim verification · three reproducible examples</summary>
    <p className="context-note">Fixed analyst-authored claims against the illustrative daily calculation. No live model is required. The challenge, correct distinction and unsupported funding assertion demonstrate the three verdicts.</p>
    {error ? <p role="alert" className="negative">{error}</p> : results.length ? <ClaimVerification results={results} /> : <p>Loading verification examples…</p>}
  </details>;
}
