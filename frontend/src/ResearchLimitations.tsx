type Study = { title: string; question: string; outcome: string; limitation: string; report: string };

const studies: Study[] = [
  {
    title: "Removing prewritten context",
    question: "Does deleting explanatory context improve or weaken reasoning?",
    outcome: "Two paired runs (four responses) produced broadly similar central conclusions. Both conditions made financial errors; neither was clearly better.",
    limitation: "One synthetic portfolio and two samples per condition; no general reasoning advantage established.",
    report: "financial-reasoning-ablation.md",
  },
  {
    title: "An independent observer",
    question: "Can a separate review catch errors that numerical checks miss?",
    outcome: "Ten cases and four conditions yielded 40 complete calls. Revisions fixed two material errors, including a cash-versus-margin inference, but missed other unsupported statements.",
    limitation: "Manual assessments on a small, frozen set; observer silence does not prove correctness.",
    report: "observer-experiment.md",
  },
  {
    title: "Self-review versus observer review",
    question: "Does asking the original model to self-correct work just as well?",
    outcome: "Self-review repaired the cash-adequacy inference in one case, but one of ten requests timed out. Other unsupported statements and omissions persisted.",
    limitation: "One sample per case; a timeout is unavailable evidence, not an incorrect interpretation.",
    report: "self-review-vs-observer.md",
  },
  {
    title: "Evidence-grounded prompting",
    question: "Does an extra evidence-check instruction improve financial interpretations?",
    outcome: "Fourteen of 20 requests returned complete answers; six were truncated. Some local corrections appeared, but no dependable overall improvement was demonstrated.",
    limitation: "Only five cases had outputs from both conditions, limiting comparisons.",
    report: "evidence-grounded-reasoning.md",
  },
  {
    title: "Meaning and evidence alignment",
    question: "Can simple rules detect a mismatch between numerical evidence and a claim?",
    outcome: "An offline prototype tested 16 authored statements and detected selected structured patterns, not unrestricted financial prose.",
    limitation: "Rules and cases were authored together; no independent held-out generalization evidence.",
    report: "meaning-alignment.md",
  },
  {
    title: "Reasoning-effort configuration",
    question: "Can a lower reasoning budget reduce cost without losing tested distinctions?",
    outcome: "Eight of eight paired requests completed. Low reasoning effort used 81% fewer reasoning tokens, with lower latency and no material error found in the four tested cases.",
    limitation: "Neither condition truncated in this study; no general failure-rate or quality guarantee.",
    report: "reasoning-effort-experiment-20261029.md",
  },
];

const source = "https://github.com/mbzuaiciao/metis/blob/main/research/";

export function ResearchLimitations() {
  return (
    <section className="research-page" aria-label="Research and limitations">
      <div className="research-lead">
        <h2>What we tested, what we learned, and what remains unresolved</h2>
        <p>Metis combines deterministic portfolio calculations with AI-generated interpretations.
          These experiments ask whether changes to context, review, evidence checking, and
          model settings actually improve the reliability of financial explanations.</p>
        <p className="research-scope">Research boundary: small exploratory experiments,
          mainly on synthetic portfolios. Numerical claim checks do not validate entire
          explanations, omitted considerations, causal claims, or investment advice.</p>
      </div>
      <div className="research-heading">
        <h2>Completed research</h2>
        <a href={source + "RESEARCH_LOG.md"} target="_blank" rel="noopener noreferrer">Full research log ↗</a>
      </div>
      <div className="research-grid">
        {studies.map((s, i) => (
          <article className="research-study" key={s.report}>
            <small>STUDY {String(i + 1).padStart(2, "0")}</small>
            <h3>{s.title}</h3>
            <p><strong>Question.</strong> {s.question}</p>
            <p><strong>Finding.</strong> {s.outcome}</p>
            <p><strong>Limit.</strong> {s.limitation}</p>
            <a href={source + s.report} target="_blank" rel="noopener noreferrer">Read the report ↗</a>
          </article>
        ))}
      </div>
      <div className="research-next">
        <h2>Open question: investigation completeness</h2>
        <p>Workshop-inspired research asks whether AI analysts identify missing financial
          information before reaching conclusions. A local baseline assessment exists, but
          its report is not yet in the committed research archive, so this page does not
          present its numerical findings.</p>
        <p>Negative and inconclusive findings are included intentionally. These studies
          do not establish that extra reviewers, prompts, or semantic rules make Metis
          generally reliable; its calculated evidence remains distinct from model prose.</p>
      </div>
    </section>
  );
}
