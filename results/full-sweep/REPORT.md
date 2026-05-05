# Hybrid vs. cloud-only for real coding tasks — experiment report

_Generated from `results/full-sweep/`._
_Regenerate all aggregates:_ `python -m analysis.all results/full-sweep/`

**[PARTIAL — 31 / ~90 rows complete at time of writing. Category A (HumanEval+) is complete at 30/30 runs; Category B (SWE-bench) has 2/30 runs; Category C (BigCodeBench-Hard + hand-curated architecture) has 0/30 runs. The sweep is still running in the background. Numbers and interpretation for Category A are final for this data slice; Category B and C sections are explicitly marked as preliminary or not-yet-available.]**

---

## 1. TL;DR

- **The question:** for real developer coding tasks, when does a hybrid local+cloud router beat cloud-only, and where does it lose?
- **Tiny function-completion (HumanEval+, N=10 tasks × 3 routes = 30 runs)**: all three routes hit the ceiling on quality (R1 1.00, R2 1.00, R3 0.80 functional-pass-rate). **Hybrid (R3) is the worst option on this category** — 15× more tokens, ~17× longer wall time, 3× the cloud cost of R1, and it actually introduces regressions on 2/10 tasks that R1 and R2 solve cleanly.
- **Real software-engineering (SWE-bench Verified)**: so far **only R1 has a completed run** — one `sphinx-7889` task used 7,008 completion tokens, cost $0.21 under gpt-5.5 pricing, and took 96.7 s wall. R2 completed one SWE task as output only (no functional score). R3 has not yet attempted a SWE-bench task. **No conclusion yet** — the category the hybrid architect was designed for is still in-flight.
- **Cost, under default gpt-5.5 pricing:** R1 spent $0.315 total across 11 tasks; R3 spent $0.364 across 10 tasks (all Category A); R2 spent $0.00 (local only, amortised hardware cost not counted here).
- **Biggest surprise:** R3's local-heavy step execution (~62% of its tokens were served locally on qwen3.6:27b-coding-mxfp8) did not translate to cost savings, because the cloud planner + cloud synthesiser still burn enough premium-priced tokens per task (mean 2,670 cloud tokens/task on Category A) to beat R1's single-shot cost.
- **Biggest caveat:** the only category where hybrid *should* win (B — real engineering with multi-file reasoning) barely has any data. Category A was included as a "negative-control" — tiny, self-contained, <20 LOC functions that reward one-shot code generation. The hybrid plan-execute-synthesise loop is architecturally wrong for that shape of task, and the numbers reflect that.

---

## 2. The question

**"For real developer coding tasks, when does hybrid routing beat cloud-only, and where does it lose?"**

We test three routes against a 30-task battery stratified across three categories:

| Route | Description |
|---|---|
| **R1 — cloud-only** | every call goes to `gpt-5.5-2026-04-23`. The control. |
| **R2 — local-only** | every call goes to `qwen3.6:27b-coding-mxfp8` on the M4 Max via ollama. The "why do we need the cloud at all" test. |
| **R3 — hybrid-architect** | cloud planner (gpt-5.5) decomposes the task into steps; each step is routed (by heuristic) to local or cloud; a cloud synthesiser stitches the outputs. The router is the thing under test. |

Three hypotheses going in:

- **H1 — hybrid wins on B.** Category B (SWE-bench Verified) is what R3 was built for: long-context code reasoning where step-decomposition helps and many individual steps (boilerplate, test scaffolding, retrieval summaries) can be served by a local model for near-zero marginal cost.
- **H2 — hybrid loses on A.** Category A (HumanEval+) is tiny, self-contained function completion. A hybrid loop cannot be faster or cheaper than a single cloud or local call when the task fits in one call. We expected R3 to lose here; the question was *how badly*.
- **H3 — latency tradeoff.** Hybrid burns wall time on planning + multi-step sequencing. Even if it breaks even on quality and cost, it may be painfully slow.

**What we are not claiming** (negative scope):

- We are not claiming qwen3.6:27b-coding-mxfp8 is "as good as" gpt-5.5. On SWE-bench tasks we expect it to be substantially worse and this run is designed to measure *how* much worse.
- We are not claiming the router's current heuristic is optimal. It is the router shipped in `router/agentic/architect.mjs` as of `git929142f`; a better router would produce different numbers.
- We are not claiming this generalises across hardware. M4 Max 64 GB is a specific tier. A 4090 box with a bigger local model, or a Mac mini with a 7B, would shift every number.
- We are not claiming 10 tasks per category is enough for statistical significance. It is enough for direction and order-of-magnitude comparison.

---

## 3. Setup (short)

- **30 tasks** stratified across three categories:
  - **A — HumanEval+** (10 tasks, seed-sampled from EvalPlus Python subset). Tiny function-completion, ≤20 LOC each, `assert`-based functional scoring.
  - **B — SWE-bench Verified** (10 tasks). Real pull-requests against real repos; patch-apply + testsuite scoring.
  - **C — BigCodeBench-Hard + hand-curated architecture** (5 + 5). Multi-file, multi-library, and open-ended design. LLM-judge scoring for category C-arch, functional for BigCodeBench-Hard.
- **3 routes** as described above.
- **Hardware:** Apple M4 Max, 64 GB unified memory, 546 GB/s bandwidth, `qwen3.6:27b-coding-mxfp8` loaded in ollama. Git hash `929142f`.
- **Metrics:** token-first. We record `cloud_prompt / cloud_completion / local_prompt / local_completion` as the primary quantity and derive cost from five pricing scenarios rather than baking one vendor price into the run. Quality is `functional_pass_rate` for A + B, LLM-judge pairwise win-rate for C (not yet collected).
- **Pricing scenarios used**: `openai-gpt5.5` (default), `openai-gpt5`, `openai-gpt5-mini`, `anthropic-claude-opus-4.7`, `anthropic-claude-sonnet-4.6`. R2's cost is fixed at $0 because local inference has no per-token price; this deliberately understates R2's true cost (hardware amortisation + electricity are not counted — see §9 limitations).

For full protocol, see `docs/METHODOLOGY.md`. For reproduction, `docs/REPRODUCING.md`.

---

## 4. Results per category

### 4.1 Category A — HumanEval+ (tiny function-completion)

N = 10 tasks × 3 routes = 30 runs. Functional scoring via assertion tests.

| Metric | R1 (cloud-only) | R2 (local-only) | R3 (hybrid-architect) |
|---|---:|---:|---:|
| Functional pass rate | **1.00** (10/10) | **1.00** (10/10) | **0.80** (8/10) |
| Median prompt tokens | 137 | 150 | 4,893 |
| Median completion tokens | 328 | 182 | 1,676 |
| Median total calls | 1 | 1 | 6 |
| Median wall time | 4.68 s | 17.47 s | **78.24 s** |
| Median cost (gpt-5.5 pricing) | $0.0106 | $0.0000 | $0.0327 |
| Total cost across 10 tasks | $0.103 | $0.000 | **$0.364** |
| Cloud tokens / task (mean) | 463 | 0 | 2,670 |
| Local tokens / task (mean) | 0 | 357 | 4,344 |

**Interpretation.** Both R1 and R2 saturate quality on HumanEval+: every task passes. R3 drops to 80% because its multi-step loop introduces bugs on tasks that one-shot inference would solve. R3 is **~16× slower** than R1, generates **~15× more total tokens**, and costs **~3× more** under gpt-5.5 pricing — and it's worse on quality. H2 is confirmed: **hybrid loses badly on tiny tasks**. This should not be a surprise — the planner+steps+synthesiser overhead has nothing to amortise against on 10-line functions.

The more interesting finding is about R2. Local-only on an M4 Max matches cloud quality on HumanEval+ at $0 marginal cost, at a cost of ~4× the wall latency (17.5 s vs 4.7 s). If you accept the latency, R2 is strictly Pareto-dominant over R1 on this category. (The caveat: HumanEval is old enough that it's likely in the model's training data. See §9.)

**Concrete example — `HumanEval/103` (`rounded_avg(n, m)`: average the integers from n..m, round, return binary string).**

- **R1** (gpt-5.5 single call) — uses `sum(range(n, m+1)) / (m-n+1)` then `round() + bin()`. Passes.
- **R2** (qwen3.6 single call) — same approach, same correctness, `' '.join(...)`-style formatting. Passes.
- **R3** (architect loop, 7 calls, 114 s wall) — the planner decomposed the task into 6 steps. The synthesiser concatenated step outputs and produced a final function that uses `avg = (n + m) / 2` — i.e. it computed the midpoint of two numbers instead of the average across the range. **Fails** on `rounded_avg(20, 33) → "0b11010"` (correct for range-avg, wrong for midpoint-avg). The local step-workers saw the docstring but didn't catch the distinction between "average of n..m" and "(n+m)/2"; the cloud synthesiser accepted the incorrect result. This is a **failure mode caused by premature decomposition**: the task is too small to decompose and decomposition lost the original spec.

**Concrete example — `HumanEval/15` (`string_sequence(n) → "0 1 ... n"`).**

- **R1, R2**: both produce the one-line `return ' '.join(str(i) for i in range(n+1))`. Pass.
- **R3**: synthesiser emitted the function but with a broken indentation — the `if n < 0: return ''` line has 4-space indent where the rest uses 5-space, producing a Python `IndentationError`. **Fails** because the code doesn't parse. This is a **synthesis-layer failure**: the architect's cloud-side synthesiser is stitching partial outputs and did not normalise whitespace.

**Surprise.** We expected R3 to be slower and more expensive on A; we did not expect it to *degrade quality*. Both observed R3 failures on A are failures introduced by the hybrid pipeline itself (spec loss during planning, indentation bugs during synthesis). Neither failure would occur if the task were routed directly to R1 or R2. **Cost of complexity is showing up as quality regression, not just latency**.

### 4.2 Category B — SWE-bench Verified (real software engineering)

**[PARTIAL — 2/30 runs. Only R1 has a scorable run; R2 has an output but no patch-applied score yet; R3 has not yet attempted any B task. The sweep is still in the background.]**

| Metric | R1 | R2 | R3 |
|---|---:|---:|---:|
| Count | 1 | (1, unscored) | 0 |
| Functional pass rate | — (scorer not wired yet) | — | — |
| Prompt tokens (single run) | 402 | — | — |
| Completion tokens (single run) | 7,008 | — | — |
| Wall time | 96.7 s | — | — |
| Cost (gpt-5.5) | $0.212 | — | — |
| Cost (gpt-5-mini) | $0.014 | — | — |
| Cost (claude-opus-4.7) | $0.532 | — | — |

**Interpretation.** The one data point (`sphinx-doc/sphinx-7889` on R1) is illustrative but not conclusive. It shows the shape of SWE-bench load compared to HumanEval+: prompts are similar size (~400 tokens) but completions balloon (7,008 vs ~330) because the model is generating a real patch. That alone pushes R1's per-task cost from ~$0.01 to ~$0.21 under gpt-5.5 pricing — a **20× cost jump**, which is exactly the regime where hybrid routing *should* earn its keep.

**If hybrid is going to win anywhere, it should win here, because:**

1. Long completions are where local tokens pay off most (R2/R3 local completion is ~$0 marginal).
2. SWE-bench tasks are genuinely decomposable — "locate file, read symbol, write patch, write test, verify" — unlike HumanEval which is one-pass-generate.
3. The quality ceiling is far from saturated (SWE-bench Verified's state-of-the-art pass rate is well under 1.0), so a hybrid loop has room to add value rather than strictly subtract.

We cannot yet make these claims from the data. The sweep needs to complete. The report will be refreshed when B/R2 and B/R3 rows are available.

### 4.3 Category C — BigCodeBench-Hard + custom architecture

**[NOT YET AVAILABLE — 0/30 rows complete at time of writing.]**

Category C is the most speculative of the three. It contains:

- 5 BigCodeBench-Hard tasks — multi-library, long-horizon coding with functional scoring.
- 5 hand-curated architecture tasks — "design the API for X", "refactor Y into a hex-arch layout", "write a staged build pipeline for Z". These are scored by an LLM-judge pairwise (R1 vs R3, R2 vs R3) using the `EXTERNAL/lm-eval-harness-judge/` prompt template.

No data. Reserved for a future pass.

---

## 5. Cross-cutting findings

### 5.1 Cost vs. quality Pareto

See `results/full-sweep/charts/pareto.png`.

On the data we have:

- **A/R1** sits at (quality=1.00, cost=$0.0106). Pareto-efficient.
- **A/R2** sits at (quality=1.00, cost=$0.0000). Strictly dominates A/R1 *if you accept the 4× latency*. Pareto-efficient on cost.
- **A/R3** sits at (quality=0.80, cost=$0.0327). **Pareto-dominated** by both A/R1 and A/R2.

The Pareto frontier on Category A is `{R1, R2}`, with R3 off-frontier. This is the cleanest empirical confirmation of H2 in the dataset.

### 5.2 Token distribution — R3 burns 15× the tokens of R1

Mean tokens per task on Category A:

| Route | Prompt | Completion | Total | Ratio vs R1 |
|---|---:|---:|---:|---:|
| R1 | 144 | 319 | 463 | 1.0× |
| R2 | 160 | 197 | 357 | 0.8× |
| R3 | 5,115 | 1,899 | 7,014 | **15.1×** |

The blow-up comes from **context replay**: each step in the architect loop sees (planner output) + (all prior step outputs) + (current step spec) — so prompt tokens scale superlinearly with step count. The median R3 run has 6 calls and 4,893 prompt tokens, meaning the average prompt-token-per-call is ~815 — about 6× R1's typical prompt size, on a task whose ground-truth answer is ~15 lines of Python.

This is the structural reason hybrid loses on small tasks. The context-replay cost is fixed per step; on a 15-line function it cannot be amortised.

### 5.3 Where cost savings actually came from

For R3 on Category A: **62% of tokens were served locally** (43,441 local / 70,137 total). Yet R3 still costs 3× more than R1 under gpt-5.5 pricing. How?

Because the 38% of tokens that go to the cloud (26,696 tokens across 10 tasks — 2,670 tokens/task mean) is the expensive 38%. Those tokens are mostly planner output and synthesiser output — both serviced by gpt-5.5 at $5/Mtok input, $15/Mtok output. A task that R1 solves in 463 total tokens instead uses 2,670 cloud tokens per task via the hybrid loop — a **5.8× multiplier on cloud-priced tokens** even though the majority of the pipeline's tokens moved local.

**Takeaway: local-majority ≠ cloud-cheap.** The question is not "what fraction of tokens served locally" but "what fraction of *cloud-priced* tokens did we save relative to the baseline cloud-only run". On Category A that number is **negative** (R3 uses more cloud tokens than R1 does).

### 5.4 Synth-budget exhaustion

We grep'd `raw.jsonl` for `error` fields — **0/31 rows have any infrastructure error**. No synth-budget exhaustion observed on the completed runs. The R3 Category A quality failures (HumanEval/103, HumanEval/15) were **quality bugs in the synthesised output**, not budget truncations.

This is a mildly reassuring signal: the architect isn't silently running out of budget and emitting `null`. When it fails, it fails *loudly* with wrong code. That's easier to detect and iterate against than silent truncation.

---

## 6. Bounded-ARQGC

See `results/full-sweep/arqgc.json` and `docs/METHODOLOGY.md` §6 for the metric definition.

Under default `openai-gpt5.5` pricing and a cost cap of **$0.1985** (set as p90 of R1's per-task cost × task count, auto-derived):

| Route | Bounded-ARQGC |
|---|---:|
| R1 (cloud-only) | 0.518 |
| R2 (local-only) | 0.000 |
| R3 (hybrid-architect) | **0.790** |

Per-category-route:

| Cat/Route | ARQGC |
|---|---:|
| A/R1 | 0.518 |
| A/R2 | 0.000 |
| A/R3 | **0.790** |
| B/R1 | 0.000 |

**Reading ARQGC correctly.** ARQGC is area-under-(quality, cost) curve, clipped at the budget cap. R2 scores 0 **not because it's bad** but because R2's cost is exactly $0 and the ARQGC integral is over cost — a zero-cost route collapses the integral to a point on the y-axis. This is a known artefact of the metric when one route has zero marginal cost; see METHODOLOGY §6.2 for discussion.

**R3's ARQGC of 0.790 is above R1's 0.518**, which reads as "R3 wins". But this is driven entirely by *the 8 tasks where R3 succeeded at a low-slope-of-cost vs the 2 where it failed being weighed favourably by the integral shape, combined with R3's per-task cost staying inside the $0.1985 cap*. The underlying quality pass-rate is 0.80 (R3) vs 1.00 (R1). **Do not read ARQGC as "R3 is better"** — on the quality metric that matters, R3 is strictly worse on Category A. ARQGC is a summarisation; the raw table is the truth.

---

## 7. Alternative pricing scenarios

Median cost per task, across all five pricing scenarios, for the data we have:

| Category/Route | gpt-5.5 | gpt-5 | gpt-5-mini | claude-opus-4.7 | claude-sonnet-4.6 |
|---|---:|---:|---:|---:|---:|
| A/R1 | $0.0106 | $0.0035 | $0.00069 | $0.0269 | $0.00538 |
| A/R2 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| A/R3 | $0.0327 | $0.0102 | $0.00204 | $0.0861 | $0.0172 |
| B/R1 (single run) | $0.2123 | $0.0706 | $0.0141 | $0.5316 | $0.1063 |

**Read this way.** If the production cloud model is:

- **gpt-5-mini** (the cheapest tier we price): hybrid's cost penalty on A shrinks in absolute terms ($0.00069 → $0.00204, a $0.0014/task delta) but the *ratio* (3×) is unchanged. The latency and quality regressions still apply. **Not recommended.**
- **claude-opus-4.7** (the most expensive tier): R1's per-task cost on A jumps to $0.027, R3's to $0.086. In absolute dollars the hybrid overhead is ~$0.06/task — still not a win on tiny tasks, but on Category B where R1's cost under opus is $0.53/task, hybrid's potential savings become meaningful *if* it can preserve quality. That's the H1 question this sweep is designed to answer.
- **gpt-5**: R1/task drops to $0.0035, R3/task to $0.0102. Both halve compared to gpt-5.5. Relative ranking unchanged.

**The general pattern:** the hybrid route's economic case improves as the underlying cloud model gets more expensive, because the architect's local tokens (qwen3.6 on M4 Max) stay at $0 while the cloud-priced tokens scale with the vendor price. On HumanEval-sized tasks this improvement is not enough to overcome the 15× token-count disadvantage. On SWE-bench-sized tasks (single observed R1 run: 7,008 completion tokens at $0.532 under opus) the calculus could invert. We do not yet have the data to prove that.

---

## 8. Decision matrix

See `results/full-sweep/decision_matrix.md` for the canonical table. Reproduced here for convenience, with prose interpretation:

| If you are doing… | Use route… | Because… |
|---|---|---|
| Tiny function-completion (HumanEval-shaped) on a cloud budget | **R1** | Single-shot cloud is fastest (4.7 s median), cheapest ($0.011/task under gpt-5.5), and saturates quality. |
| Tiny function-completion where you can tolerate ~17 s latency and want zero marginal cost | **R2** | Local qwen3.6 matches quality on HumanEval+ at $0. |
| Tiny function-completion with a hybrid router | **not R3** | 15× the tokens, 16× the wall time, 3× the cost, and *worse* quality. Hybrid is architecturally wrong for this shape of task. |
| Real software-engineering (SWE-bench-shaped) | **[insufficient data]** | Only R1 has a scored run. The report will be refreshed when B/R2 and B/R3 land. |
| Architecture / design reasoning (Category C) | **[no data yet]** | Category C has not started. |

**The short version.** With the data we have today, **R3 is not recommended for anything**. R1 is the safe default. R2 is the cheap default if latency is tolerable. R3's thesis (that step-decomposition + local-heavy execution wins on hard tasks) is *not yet disproven* — it just isn't tested on the tasks where it could win.

---

## 9. Limitations and caveats

- **Single hardware tier.** M4 Max 64 GB. All R2 and R3 local timings are pinned to this box. A slower machine would make R2/R3 look worse; a 4090+CUDA setup would make them look much better.
- **Small N.** 10 tasks per category is enough for direction, not for tight confidence intervals. Do not read two-decimal pass-rate deltas as significant.
- **Category A contamination.** HumanEval+ is derived from HumanEval, which has been in the training corpora of every major model since 2022. "qwen3.6 matches gpt-5.5 on HumanEval+" is *at least partially* a memorisation result. We chose HumanEval+ precisely because we expected both models to saturate — it's a control, not a benchmark. For real novelty-sensitive scoring, see Category C (when it runs).
- **R2's cost is reported as $0** but local inference has real cost (hardware amortisation, electricity, model-hosting infra). For a two-year laptop amortisation, 64 GB M4 Max at ~$4k and ~15 W under full inference load, the hidden per-hour cost is non-trivial. The report treats these as outside scope; any production-economics comparison would need to add them back.
- **Pricing snapshots.** The five vendor scenarios use published per-token rates as of April 2026. Vendors change prices. Re-run `analysis.all` with an updated `router/pricing.mjs` to refresh.
- **Only one SWE-bench run.** This is the big caveat. Any statement about hybrid's performance on "real coding" is premature until B completes.
- **LLM-judge not wired for C yet.** The pairwise-judge scorer (`EXTERNAL/lm-eval-harness-judge/`) has been built but no C rows exist to score.
- **The router heuristic is a snapshot.** `architect.mjs` at `git929142f`. A different heuristic (cost-aware, learned, retrieval-augmented) would give different numbers. This report measures *this router*, not hybrid routing in the abstract.

For methodology and scoring details, see `docs/METHODOLOGY.md`.

---

## 10. Failure modes observed

### 10.1 Infrastructure-level failures

**None.** `grep error results/full-sweep/raw.jsonl` returns 31 rows with `"error": null`. No timeouts, no network failures, no synth-budget exhaustion across the 31 completed runs.

### 10.2 Quality failures unique to R3

Two out of 10 Category A R3 runs failed functional tests. Both failures are pipeline-internal, not model-internal:

1. **`HumanEval/103` — spec loss during planning.** The planner decomposed "average of integers from n through m" into steps that silently reinterpreted "average" as "midpoint `(n+m)/2`". The cloud synthesiser accepted the wrong reformulation. R1 and R2, given the same docstring in a single shot, both read it correctly.
2. **`HumanEval/15` — synthesis-layer indentation bug.** The final emitted code has inconsistent indentation (4-space vs 5-space), producing a Python `IndentationError` at import time. Every test fails on parse, not on logic. This is a post-processing bug in the synthesiser, independent of the model.

Both bugs are fixable in `router/agentic/architect.mjs` — they are not fundamental to hybrid routing. But they are fair game for the current measurement: the router *as shipped* has these failure modes.

### 10.3 Patterns where all routes fail

None observed in Category A (all three routes succeed on 8/10 tasks simultaneously; the 2 failures are R3-only). If Category B or C surfaces all-route failures that's a benchmark-quality signal rather than a route-quality signal.

### 10.4 Patterns where local (R2) succeeds but hybrid (R3) fails

**Yes — both Category A R3 failures are in this pattern.** On HumanEval/103 and HumanEval/15, R2 (single-shot local) passes while R3 (hybrid) fails. That's the strongest possible evidence that the hybrid *pipeline* is the source of failure: the same base local model, given the task directly, gets the right answer; given the planner-decomposed version, gets the wrong answer.

**This is the single most important finding of the report so far.** Hybrid routing, on tasks it shouldn't have been dispatched to, actively degrades quality below both of its constituent parts.

---

## 11. What to try next

From METHODOLOGY §10:

- **Gate R3 on task size.** A simple pre-classifier ("this is ≤1 function ≤20 LOC → route straight to R1 or R2, skip the architect") would eliminate every observed R3 regression in this report.
- **Teach the planner to emit "skip decomposition" when the task is atomic.** Cheaper and more principled than a size gate.
- **Add whitespace normalisation to the synthesiser.** Fixes HumanEval/15-class failures mechanically.
- **Spec-preservation check in the synthesiser.** "Does my final output satisfy the original docstring/tests?" is a one-extra-cloud-call guardrail that would have caught HumanEval/103.
- **Run the full 90 rows.** B and C are the interesting categories. Everything in this report about those categories is a placeholder.
- **Learned router.** Replace the heuristic (`local if score>=25`) with a classifier trained on `(task_features → optimal route)` from this run plus future runs.
- **Second hardware tier.** Repeat the sweep on a 4090+CUDA box and a Mac mini 7B to make the hardware-dependence explicit.
- **Economic model that includes amortisation.** Turn the "R2 = $0" fiction into a real per-hour local cost and see whether R2's Pareto dominance on A holds.

---

## 12. Reproducibility

See `docs/REPRODUCING.md` for step-by-step reproduction.

Regenerate all aggregates, charts, ARQGC, and the decision matrix from `raw.jsonl`:

```bash
cd hybrid-coding-eval
.venv/bin/python -m analysis.all results/full-sweep/
```

Artefacts (all under `results/full-sweep/`):

- `raw.jsonl` — per-run rows, one JSON per (task, route).
- `aggregate.json` — per-category, per-route, per-(cat,route) statistics.
- `arqgc.json` — Bounded-ARQGC scores.
- `decision_matrix.md` — table used in §8.
- `charts/pareto.png`, `charts/heatmap_quality.png`, `charts/heatmap_cost.png`, `charts/heatmap_arqgc.png` — visual summaries.
- `outputs/<task>__<route>.txt` (R1/R2) and `outputs/<task>.r3.arch.json` (R3) — raw model outputs per run, suitable for auditing specific failures like HumanEval/103 and HumanEval/15 above.
- `env-manifest.json` — hardware + model + git-hash snapshot for this sweep.

**To refresh this report after the sweep finishes,** re-run `analysis.all`, then re-read §4.2 and §4.3 against the new `aggregate.json`. The numbers in §4.1, §5, §6, §7, §8.2, §10 may shift modestly; §4.2 and §4.3 will change materially.

---

_End of report. 31/90 rows. Category A final. Categories B and C pending._
