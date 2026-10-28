# Repository guidance

## Research memory

- Before research-related work, read `research/RESEARCH_LOG.md` and consult its linked detailed reports as relevant.
- After completing an experiment, append a dated log entry, including negative results. Record exact model/settings, evaluation criteria, case/call counts, token usage, latency, failures, limitations and the resulting decision; mark unavailable metadata explicitly.
- Distinguish observations, interpretations, hypotheses and engineering decisions. Small exploratory samples do not establish reliability or causality.
- Do not repeat completed experiments unless the replication purpose is explicit. A backlog entry is not authorization to run inference, provision compute or fine-tune.
- Preserve completed reports and experimental records. Never silently change prior findings; add dated corrections or disagreements with provenance and possible explanations instead.
- Keep credentials, raw model responses and private inference records out of Git. Preserve the ignored `research/runs/` boundary.
