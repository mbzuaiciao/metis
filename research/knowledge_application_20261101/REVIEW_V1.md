# Supplied read-only scientific review of v1 — 2026-11-01

Provenance: the assistant's read-only review in this chat, preceding the user's v2 correction request. This is an assistant assessment, not independent human financial adjudication. The assessment below is preserved as supplied; local file links were absolute workspace links in the chat. No experiment was executed during that review.

**NO-GO for the frozen v1.** The package could support a useful behavioral pilot, but its knowledge probes and several evidence-sufficiency labels need correction before training. Passing offline checks does not resolve these scientific problems.

I read AGENTS.md, the research log, all 16 experiment files, all 60 training examples and 20 held-out scenarios, and relevant prior reports/cases. This review remained read-only: no experiment scripts, downloads, training or inference were run.

**1. Scientific validity**

Several controls are sound:

- Knowledge and application use fresh, separate calls; knowledge responses are never inserted into application prompts.
- A and C have identical inference instructions and generation settings; the intended intervention is the adapter.
- B is a reasonable stronger-prompt baseline: it adds general evidence discipline without supplying case-specific answers.
- The rubric credits conditional reasoning without literal questions and penalizes unnecessary questioning on sufficient cases.
- Reporting shared A/C knowledge-correct cases, knowledge changes and application regressions is appropriate.

However, **K=1 does not reliably demonstrate the particular financial relationship needed by the paired application**. Some knowledge questions omit the structure their keys require; others permit an input checklist without demonstrating the governing relationship. Consequently, even the shared-K subset cannot adequately separate newly learned financial reasoning from better application of previously demonstrated reasoning.

Correct knowledge answers would remain behavioral evidence of accessible knowledge—not direct evidence of internal representations. Even after correction, this small pilot could support a narrow behavioral interpretation, not isolate an internal learning mechanism.

**2. Financial dataset quality**

The sufficient-case arithmetic is sound under the stated assumptions: eval-02’s 72–102 collar cost, eval-04’s residuals (+1, −1), eval-06/08’s funding deficits, eval-10’s 4m distribution, eval-11’s 2m write-down, eval-16’s +0.8 percentage points, eval-18’s +$70 and eval-20’s $40 cost.

Most missing inputs are financially relevant. The main problems concern question scope, incomplete targets and shortcut cues—not arithmetic.

| Classification | Affected file/cases and evidence | Why it matters / smallest correction |
|---|---|---|
| **Blocking** | [heldout.jsonl](/Users/xq/Documents/GitHub/metis/research/knowledge_application_20261101/heldout.jsonl): eval-01’s knowledge question never mentions a swap; eval-05 never mentions a barrier; eval-10 never mentions a reserve, yet their keys require surviving swap obligations, barrier behavior and reserve top-up reasoning. Eval-19 additionally requires possible IRR roots although the question asks broadly about annualized return. | Knowledge scoring depends partly on guessing hidden scenario details. Rewrite each knowledge question to name the relevant instrument/structure, without application facts, and require the actual relationship or sufficiency rule. Align mandatory criteria with what was asked. |
| **Material — clear scope errors** | [train.jsonl](/Users/xq/Documents/GitHub/metis/research/knowledge_application_20261101/train.jsonl): train-16 asks whether tomorrow’s proceeds can fund today’s payment; their timing already answers that narrower question negatively. Train-33 asks whether an unchanged rating *establishes* unchanged PD; it does not, without needing current PD estimates. Train-50’s subscriptions already establish that raw NAV growth is not investment return. Train-20 changes “every submitted redemption” into the enforceable payout after gates. | These teach requests for information needed to answer a different question. Reword the questions to ask about overall funding, actual PD, quantified return or contractual payout—or accept the already justified scoped negative answer. |
| **Material — judgment-sensitive** | eval-01 combines fixed-rate debt with a receive-fixed swap, which ordinarily introduces a floating payment leg. Also, the target covers **every permitted call decision**, so a call policy alone cannot establish it. Eval-17 mixes whether unlinked sums are generally valid with whether they happen to reconcile exactly for unspecified return paths. | A competent answer could disagree with the insufficiency key. Specify eval-01’s signed swap terms and pathwise target; clarify eval-17’s annual-return definition and whether the question concerns methodological validity or numerical reconciliation. |
| **Material** | Training uses only `justified_answer` ([train.py:44](/Users/xq/Documents/GitHub/metis/research/knowledge_application_20261101/train.py:44)). For example, train-26’s target never identifies the certified borrowing base; train-35 omits the required guarantor-capacity inquiry. Train-13 introduces “positive” futures P&L although its sign is unspecified. | Several targets would not satisfy the experiment’s own specificity requirements. Make each target identify its required uncertainty and remove unprovided factual implications. |

Generic caution is **partly controlled**, through balanced labels and justified adverse sufficient cases. Nevertheless, every held-out insufficient case explicitly announces absent information, while sufficient cases commonly announce exhaustive scope. The model can improve by following these textual cues.

Substantive reasoning overlap also remains: train-06→eval-02 shares physical cost minus option payoff plus premium; train-14→eval-04 shares signed residual versus limit; train-17→eval-06 shares a chronological cash ladder; train-21→eval-15 shares timely offshore currency accessibility; train-57→eval-18 shares signed trade cash flows. These are legitimate transfer exercises, but stronger structural independence is not established by different labels.

**Material correction:** remove overt sufficiency cues where practical, and describe the result as transfer across related synthetic templates. No larger dataset is required.

I found no held-out reproduction of the reviewed earlier Metis scenarios. Familiar principles—funding timing, hedge mandates and scoped conclusions—recur, but the earlier portfolio cases and numerical setups are not reproduced. This is a semantic review finding, not proof of benchmark independence.

**3. Scoring and execution findings**

- **Material — knowledge-rating contamination:** [score.py:35](/Users/xq/Documents/GitHub/metis/research/knowledge_application_20261101/score.py:35) puts the application’s `justified_answer`, sufficiency label and missing-evidence key into **knowledge** packets too. This conflicts with rating knowledge independently of application correctness. Supply probe-specific keys; keep application answers out of knowledge-rating packets.
- **Material — stop-rule mismatch:** [evaluate.py:79](/Users/xq/Documents/GitHub/metis/research/knowledge_application_20261101/evaluate.py:79) records truncation, increments `completed`, continues generating and ultimately marks the command complete. The command sequence can therefore proceed to training after truncated A/B outputs. Save the truncated record, then stop with nonzero exit and accurate manifest status.
- **Minor:** eval-09 asks about “posted collateral,” but the evidence describes cash merely held. Align the wording. Unnecessary specialist requirements such as IRR-root discussion should also be removed unless explicitly within scope.

**4. Technical feasibility**

I found **no confirmed static API blocker**. The model exists, is labeled Apache-2.0, and uses Qwen3 architecture supported by the proposed Transformers version. The TRL version supports the supplied prompt/completion format and completion masks. These conclusions follow from the [official model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), [revision-specific configuration](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/raw/cdbee75f17c01a7cc42f958dc650907174af0554/config.json) and [TRL v0.23.1 source](https://github.com/huggingface/trl/blob/v0.23.1/trl/trainer/sft_trainer.py).

The public tokenizer configuration uses an assistant generation prefix, `<|im_end|>` EOS and a distinct padding token, consistent with the implementation’s intended formatting. Exact frozen-artifact behavior still requires runtime checking. [Tokenizer configuration](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/tokenizer_config.json)

Approximately 8.05GB of BF16 base weights plus 11.8m adapter parameters makes a 48GB target plausible. The stated 12–24GB training estimate is unmeasured; activations, vocabulary-sized logits, workspaces and allocator overhead matter. **GPU compatibility, runtime and provider pricing are not verified by this review.**

A separately authorized smoke test must check dependency resolution/imports, frozen tokenizer prefix/EOS behavior, actual completion labels and sequence lengths, BF16/SDPA forward/backward execution, adapter-only gradients, save/reload placement and peak memory. Use training or disposable synthetic inputs, keeping held-out outputs untouched.

**5. Minimum corrections before the first training run**

1. Repair the paired knowledge questions and keys.
2. Resolve the listed scope/label ambiguities and incomplete training targets.
3. Reduce explicit missingness cues and qualify structural-transfer claims.
4. Separate knowledge/application rating keys and enforce truncation stopping.
5. Preserve v1, freeze a corrected version, obtain financially competent human acceptance, and complete a separately authorized runtime smoke test.

**Recommendation: NO-GO for v1; reconsider after these bounded corrections.** The existing three-condition design, dataset sizes and single-adapter scope can remain. No fixes or new artifacts were created.
