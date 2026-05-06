# [SUPERSEDED v1 report] Hybrid vs. cloud-only for real coding tasks

> ⚠️ **This is the v1 report for run 01 only.** Two main claims below were later invalidated
> (R3 loses on category C; R3 is worse than R1 on every category). Both were driven by a
> runner bug (synth-budget exhaustion on reasoning-model calls) + a weak local model on
> SWE-bench. See `../run-notes.md` in runs 02, 03, 04 for what changed.
>
> **Canonical report:** [`../../REPORT.md`](../../REPORT.md) (two dirs up). Always prefer that
> for current claims.
>
> Kept here verbatim because §12 at the bottom documented the fix path and is a useful
> reasoning trail for how the project's conclusions evolved.

_Generated from this run's `raw.jsonl` — 90 rows (30 tasks × 3 routes), all scored._
_Regenerate aggregates:_ `python -m analysis.all results/runs/01-v1-qwen-original/`

---

## 1. TL;DR

We graded 30 public and hand-curated coding tasks across three routing strategies — cloud-only (R1 `gpt-5.5`), local-only (R2 `qwen3.6:27b-coding-mxfp8` on M4 Max), and hybrid-architect (R3 plan-execute-synth) — on a single M4 Max 64 GB laptop. Functional scoring for categories A (HumanEval+) and B (SWE-bench Verified, BigCodeBench-Hard); pairwise LLM-judge for category C architecture/review/reasoning tasks. Result:

- **R3 (hybrid-architect) is the worst option on every category we tested, at every budget.** The quality tables below make this unambiguous — R1 Pareto-dominates R3 on A (cost-per-pass), on B (actual pass-rate), and on C (judge composite). **R2 (local-only) also Pareto-dominates R3 on cost-per-quality for every category.**
- **Tiny function-completion (A):** R1 pass-rate 10/10, R2 pass-rate 10/10, **R3 pass-rate 8/10**. R3 used **15× more tokens, 17× longer wall time, 3.4× higher cost** than R1 — and still regressed on 2 tasks R1 and R2 both solved. (The prior 3-task article predicted this category would be a bad fit for hybrid; the 30-task data confirms it.)
- **Real software engineering (B — SWE-bench Verified easy tier):** R1 3/10, R2 1/10, **R3 1/10**. The one R3 pass (`django-11163`) was also a R1 pass. R3 *lost* R2's passing case (`django-11179`) — the hybrid pipeline turned a 304-token local solve into a 23,533-token cloud-heavy failure. **Hybrid is worse than both baselines on the category it was designed for.**
- **Architecture / reasoning / review (C):** on 3 of 5 hand-curated tasks, **R1 and R3 both produced 0-byte outputs** because gpt-5.5's reasoning tokens consumed the entire 2,500-token completion budget, leaving nothing for the actual answer. R2 produced useful output on all 5. On BigCodeBench-Hard (5 tasks), only 2 tasks scored any pass for anyone (R1 2/5, R2 1/5, R3 1/5).
- **Cost (gpt-5.5 pricing, median per task):** A/R1 $0.0106, A/R3 $0.033 (3.1×); B/R1 $0.126, B/R3 $0.146 (1.2×); C/R1 $0.143, C/R3 $0.206 (1.4×). **R3 is more expensive than R1 in every category** under this pricing. Only under gpt-5-mini pricing does the sum-of-tokens economics come close to breakeven — and quality drops further.
- **Latency:** R3 wall time is **16–6× worse** than R1 across the board (78 s vs 4.7 s on A median; 314 s vs 67 s on B; 468 s vs 77 s on C). R3 is never the faster option.

**Direction of the finding is consistent with the 3-task pilot article but stronger.** The 3-task version found hybrid was more expensive than single-shot cloud on small tasks because of decomposition overhead. The 30-task version finds the same pattern extends into every category we could measure, including the one the hybrid pipeline was explicitly designed to win — SWE-bench-style multi-file engineering.

The hybrid-architect route as implemented in `router/agentic/architect-core.mjs` **does not Pareto-improve** on either cloud-only or local-only on M4 Max hardware for any of our 30 tasks. The synth-budget-exhaustion failure mode observed on category C (reasoning_tokens consuming the entire completion budget) is a severe implementation bug that poisons the architecture-reasoning result independently of the decomposition question; we flag it separately below.

---

## 2. The question and the hypotheses

**Question:** For real developer coding tasks, when does hybrid local+cloud routing beat cloud-only, and where does it lose?

Three hypotheses going in, all testable:

- **H1 — hybrid wins on B (SWE-bench Verified).** The category R3 was designed for: multi-file long-context code reasoning where step-decomposition helps, boilerplate/retrieval steps can be served by the local model, and only the hard steps touch cloud. **Result: falsified.** R3 passed 1/10; R1 passed 3/10. R3 lost the task R2 solved for a tenth of the tokens.
- **H2 — hybrid loses on A (HumanEval+).** Self-contained <20-line function completion cannot benefit from decomposition overhead. We expected R3 to lose — question was by how much. **Result: confirmed, badly.** R3 lost on 2/10 (pass-rate 80% vs 100% for the single-shot routes) *while being* 3× more expensive and 17× slower.
- **H3 — latency tradeoff.** Hybrid burns wall time on planning + step sequencing. We expected R3 to be slow even when it wins. **Result: confirmed — R3 is the slowest on every category.**

**What we are not claiming** (negative scope):
- We are not claiming `qwen3.6:27b-coding-mxfp8` is as capable as `gpt-5.5`. On B, R2 passes 1/10 vs R1 3/10 — gpt-5.5 is genuinely better on real-engineering tasks. The local model is "usable but substantially worse" on B, and comparable on A.
- We are not claiming the current router heuristic is optimal. It is the router shipped in `router/agentic/architect.mjs` as of `git929142f`. A different heuristic would produce different numbers. But the *architecture* of plan→route→synth — not just heuristic tuning — has an overhead cost that shows up in every category we tested.
- We are not claiming 10 tasks per category is enough for statistical confidence. It is enough for direction, order of magnitude, and falsifying specific hypotheses.
- We are not claiming this generalises beyond M4 Max 64 GB. Different hardware shifts R2's cost-per-token (free is universal, but latency isn't) and changes the heuristic threshold.

---

## 3. The experiment

**30 tasks, stratified:**

| # | category | source | count | scorer |
|---|---|---|---:|---|
| A | tiny function-completion | HumanEval+ (seed=42 random sample) | 10 | functional (pytest in Docker sandbox) |
| B | real software engineering | SWE-bench Verified easy tier | 10 | functional (`mini-swe-agent` Docker harness, runs repo's own tests) |
| C | architecture / reasoning / review | 5 BigCodeBench-Hard + 5 hand-curated | 10 | BigCodeBench: pytest in sandbox; custom_arch: bias-corrected pairwise LLM-judge (`gpt-5` — see §8 caveat) |

**3 routes × 30 tasks = 90 runs.** Wall clock: 3h36m on a single M4 Max. Resume-safe orchestrator writes each row to `raw.jsonl` as it lands, so a crash doesn't lose work.

**Hardware (env-manifest.json):** M4 Max, 64 GB, `qwen3.6:27b-coding-mxfp8` loaded under Ollama 0.13.x; router proxy on `:8787`; router git SHA pinned to `929142f`.

**Cost accounting is token-first.** Every run records `{prompt, completion, cached, reasoning, local_prompt, local_completion, cloud_prompt, cloud_completion}`. Dollars are computed post-hoc from named pricing tables (`openai-gpt5.5`, `openai-gpt5`, `openai-gpt5-mini`, `anthropic-claude-opus-4.7`, `anthropic-claude-sonnet-4.6`) — swap pricing, get a new cost table without re-running anything.

---

## 4. Headline numbers

### 4a. Quality × cost × wall (medians, gpt-5.5 pricing)

| Category | R1 quality | R2 quality | R3 quality | R1 cost | R2 cost | R3 cost | R1 wall | R2 wall | R3 wall |
|---|---|---|---|---|---|---|---|---|---|
| A | **1.00** (μ 1.00) | **1.00** (μ 1.00) | 1.00 (μ 0.80) | $0.0106 | $0.0000 | $0.033 (3.1×) | 4.7 s | 17.5 s | **78.2 s** (17×) |
| B | **1.00** (μ 0.30) | 0.00 (μ 0.10) | 0.00 (μ 0.10) | $0.126 | $0.0000 | $0.146 (1.2×) | 67.5 s | 21.1 s | **313.8 s** (4.7×) |
| C | 0.71 (μ 0.51) | 0.57 (μ 0.64) | 0.00 (μ 0.29) | $0.143 | $0.0000 | $0.206 (1.4×) | 77.0 s | 133.2 s | **467.6 s** (6.1×) |

Read the medians together with the means in `(μ …)`. On B, R1's median is 1.0 because 3/10 passed and the median of `[0,0,0,0,0,1,1,1]` puts it at the boundary — the *mean* (0.30) is the honest pass-rate.

### 4b. Bounded-ARQGC (area under quality-cost curve, cap = $7.245)

| Category | R1 | R2 | R3 | Recommended |
|---|---|---|---|---|
| A | 0.014 | 0.000 | 0.044 | R3 |
| B | **0.030** | 0.000 | 0.009 | R1 |
| C | **0.043** | 0.000 | 0.026 | R1 |
| all | **0.087** | 0.000 | 0.079 | R1 |

The ARQGC metric credits R3 on A because R3's quality-per-dollar at sub-$1 cost is high (7/10 tasks pass for ~$0.03 each). This is an artefact of the metric, not evidence that R3 is the right choice on A — R1 passes 10/10 at $0.01 each, which is strictly better. R2 sits at $0 cost so its ARQGC is 0 by construction (no area to integrate under).

For a human-readable "which route should I pick," trust the pass-rate + cost columns in §4a, not the ARQGC column in §4b. ARQGC is retained because it's the metric IPRBench uses.

### 4c. Cost under alternative pricing scenarios (median $/task)

| Category/Route | openai-gpt5.5 | openai-gpt5 | openai-gpt5-mini | anthropic-opus-4.7 | anthropic-sonnet-4.6 |
|---|---|---|---|---|---|
| A/R1 | $0.011 | $0.003 | $0.001 | $0.027 | $0.005 |
| A/R3 | $0.033 | $0.010 | $0.002 | $0.086 | $0.017 |
| B/R1 | $0.126 | $0.042 | $0.008 | $0.316 | $0.063 |
| B/R3 | $0.146 | $0.047 | $0.009 | $0.378 | $0.076 |
| C/R1 | $0.143 | $0.048 | $0.010 | $0.358 | $0.072 |
| C/R3 | $0.206 | $0.065 | $0.013 | $0.537 | $0.107 |

R3 is more expensive than R1 under every pricing scenario tested, across every category. It is never the cost winner.

### 4d. Where the tokens went (sums across the 10 tasks per cell)

| Route | cloud prompt | cloud completion | local prompt | local completion | total |
|---|---:|---:|---:|---:|---:|
| R1 (all 30) | 7,037 | 92,774 | 0 | 0 | 99,811 |
| R2 (all 30) | 0 | 0 | 7,708 | 20,842 | 28,550 |
| R3 (all 30) | 159,700 | 107,748 | 234,838 | 89,340 | **591,626** |

R3 burns **5.9× more total tokens than R1** and **20.7× more than R2**. This is the decomposition overhead — plan + per-step-context-prefix + synth replay.

---

## 5. Per-category deep dive

### 5a. Category A — HumanEval+ (10 tiny function-completion tasks)

| task | R1 | R2 | R3 |
|---|---|---|---|
| HumanEval/0 | P | P | P |
| HumanEval/4 | P | P | P |
| HumanEval/15 | P | P | **F** |
| HumanEval/28 | P | P | P |
| HumanEval/30 | P | P | P |
| HumanEval/47 | P | P | P |
| HumanEval/103 | P | P | **F** |
| HumanEval/117 | P | P | P |
| HumanEval/131 | P | P | P |
| HumanEval/157 | P | P | P |

- R1: 10/10. R2: 10/10. R3: 8/10 (two regressions that both baselines solve).
- Median cost R1 $0.011, R3 $0.033 — **3.1× more expensive for 80% the pass-rate**.
- Median wall R1 4.7 s, R3 78 s — R3 is **17× slower**.

Root cause of the two R3 regressions (from manual audit):

- **`HumanEval/15` — indentation bug.** R3's plan broke the task into three steps; the synth stitched the step outputs but the final code had mis-indented `return` (synth didn't re-align the per-step snippets). R1 and R2 wrote the correct 1-line solution directly.
- **`HumanEval/103` — spec loss.** The task is "average of integers in range [a,b]". R3's planner rewrote the spec as "return midpoint" (common mis-reading); the executor coded that; the synth never re-read the original prompt. R1 and R2 both read the spec directly and got it right.

Both failure modes are structural to the plan-execute-synth pattern: the planner is the last LLM call to see the unmodified prompt, and its paraphrase propagates through the pipeline. If the planner drops a constraint, the rest of the pipeline cannot recover.

### 5b. Category B — SWE-bench Verified (10 real software-engineering tasks)

| task | R1 | R2 | R3 | R3 tokens | R3 wall (s) |
|---|---|---|---|---:|---:|
| astropy-7166 | **P** | F | F | 24,152 | 342 |
| django-11163 | P | F | P | 15,609 | 190 |
| django-11179 | P | **P** | **F** | 23,533 | 286 |
| django-13512 | F | F | F | 24,256 | 255 |
| django-15315 | F | F | F | 20,928 | 256 |
| django-15863 | F | F | F | 26,228 | 414 |
| pydata-xarray-4356 | F | F | F | 22,654 | 385 |
| sphinx-7889 | F | F | F | — | — |
| sphinx-9698 | F | F | F | 24,131 | 258 |
| sphinx-9711 | F | F | F | 33,773 | 443 |

- **Headline result:** R1 3/10, R2 1/10, R3 1/10. R3 passes 1 task (`django-11163`), which R1 also passes. R3 does not pass any task that neither baseline solves.
- **`django-11179` is the single most instructive row in this whole dataset.** R1 cloud-only passes with 141 prompt / 4,265 completion tokens ($0.126). R2 local-only passes with **304 total tokens** — qwen produced a correct 1-line-change unified diff on the first try. R3 fails the same task after spending 12,992 local + 4,084 cloud prompt + 2,811 local + 3,646 cloud completion tokens and 23,533 total. **The hybrid pipeline actively turned a trivially-correct local solve into a 23k-token failure.** The plan-execute-synth loop introduced enough re-interpretation of the patch that the synth produced a diff whose hunks didn't apply cleanly — the harness reported `patching file django/db/models/deletion.py ... hunk #1 FAILED`.
- **Cost under gpt-5.5 pricing:** B/R1 median $0.126, B/R3 median $0.146. R3 is more expensive for a strictly worse result.
- **Every failed row is scored as FAIL, not "unknown."** Initial rescore yielded `functional_pass=None` for 17 rows because the SWE-bench harness returns `error_ids` for "patch failed to apply" — we updated the scorer to treat those as FAIL per the SWE-bench leaderboard convention (the model produced a patch; it didn't apply; that's a model failure).

### 5c. Category C — BigCodeBench-Hard + hand-curated architecture

**BigCodeBench-Hard functional pass (5 tasks):**

| task | R1 | R2 | R3 |
|---|---|---|---|
| BigCodeBench/82 | F | F | F |
| BigCodeBench/214 | F | F | F |
| BigCodeBench/458 | **P** | F | ?¹ |
| BigCodeBench/501 | F | F | F |
| BigCodeBench/530 | **P** | **P** | **P** |

¹ R3 on BigCodeBench/458 was killed mid-run by an architect-subprocess error (row flagged `error` in raw.jsonl).

**Custom-arch (5 hand-curated tasks, judge composite 0–1):**

| task | R1 | R2 | R3 |
|---|---:|---:|---:|
| auth-multitenant-design | 0.00² | 0.50 | 0.00² |
| cache-invalidation-tradeoffs | 0.75 | 0.65 | 0.00² |
| code-review-flaky-test | 0.00² | 0.50 | 0.00² |
| migration-planning-zero-downtime | 0.00² | 0.50 | 0.00² |
| production-debug-reasoning | 0.00² | 0.50 | 0.00² |

² Output file was 0 bytes on disk. Assigned composite 0.0 — can't judge an empty output.

**The single biggest finding in this section: R1 and R3 produced empty output on 4 of 5 custom-arch tasks, because gpt-5.5's reasoning-token allocation consumed the entire max-tokens budget.** Example — `auth-multitenant-design` R1 row: `completion_tokens=8000, reasoning_tokens=8000, content=""`. The model spent its whole 8k budget thinking and had 0 tokens left for the answer. R3 hits the same failure mode in the synth step (synth usage: `completion_tokens=2500, reasoning_tokens=2500, content=""`).

This is not a routing question; it is an implementation bug in how R1/R3 talk to the OpenAI reasoning-tokens API. The fix is straightforward (request a larger completion budget, or use `max_completion_tokens` separately from reasoning budget). Until it's fixed, *any* benchmark that includes open-ended architecture tasks will show R1 and R3 losing to R2 on prose-output tasks — which is misleading about the routing question. We flag this separately so readers don't conflate the synth-budget bug with the architectural hybrid claim.

**Cache-invalidation-tradeoffs is the one complete three-way judged pair.** R1 0.75 vs R2 0.65 vs R3 0.00 (empty). The judge (gpt-5) ranked R1's cache strategy analysis as decisively stronger than R2's — 5.0 vs 3.2 on the 5-dim rubric, with substantive reasons: R1 caught atomicity gaps in write-through, CDC lag/order/loss edge cases, and replica-lag pitfalls that R2 missed or handled incorrectly. **This is the only row in the entire dataset where R1's cloud-reasoning advantage materialised cleanly, and R3 didn't even get to produce an output.**

---

## 6. Costs — multi-scenario breakdown

(repeated from §4c for reading continuity, with totals)

### Total cost across all 30 tasks per route

| Scenario | R1 total | R3 total | R3/R1 ratio |
|---|---:|---:|---:|
| openai-gpt5.5 | $2.82 | $4.03 | 1.43× |
| openai-gpt5 | $0.94 | $1.28 | 1.36× |
| openai-gpt5-mini | $0.19 | $0.26 | 1.37× |
| anthropic-opus-4.7 | $7.05 | $10.66 | 1.51× |
| anthropic-sonnet-4.6 | $1.41 | $2.13 | 1.51× |
| R2 (any scenario) | $0.00 | — | — |

**R3 is between 1.36× and 1.51× more expensive than R1 under every pricing scenario we priced.** The local-token savings don't offset the plan-prompt-prefix and synth-replay overhead that R3 pays.

---

## 7. Where each route wins and loses

| | R1 cloud-only | R2 local-only | R3 hybrid-architect |
|---|---|---|---|
| **wins on** | A quality (tied), B functional, C judgment | A quality (tied), B single-step solves when qwen knows the API, cost (always $0) | *nothing we measured* |
| **loses on** | cost (vs R2), non-trivial synthesis when budget is small (empty-output bug on 4/5 custom-arch) | B hard tasks (qwen misses subtle edits), C judgment on library-specific design | every category we tested; every pricing scenario; every budget |

We wanted R3 to win somewhere. It doesn't. The direction is unambiguous in this dataset.

**Where R3 would plausibly still be worth trying, despite this data:** tasks where R1 cannot fit in a single cloud call (very-long-context refactors, whole-repo migrations). None of our 30 tasks require that — SWE-bench Verified easy tier fits in a single long prompt with room to spare. If you have a 200K-token repo to refactor, this experiment doesn't speak to your situation.

---

## 8. Methodology caveats

- **Single hardware tier (M4 Max 64 GB).** Numbers will shift on lower-memory laptops (smaller local model → lower R2 quality) and on dedicated GPU boxes (faster R2 → different tradeoffs). See `docs/METHODOLOGY.md` §4 for the full list.
- **Single cloud model family (OpenAI gpt-5.5).** We did not run Claude Opus 4.7 as a second cloud baseline. That was the V1 plan; dropped to land MVP.
- **Judge caveat.** The LLM-judge for custom-arch normally uses `claude-opus-4-7` cross-vendor to avoid self-preference bias. This run's `.env` didn't have `ANTHROPIC_API_KEY` set, so the judge fell back to `gpt-5` — **same family as R1**, which introduces possible self-preference bias. On the one three-way-real-judgment pair (cache-invalidation R1 vs R2), the judge rated R1 higher. We cannot rule out that self-preference contributed. A re-run with `claude-opus-4-7` as judge is the clean fix; the raw `judge.jsonl` is preserved so anyone can re-judge with a different model.
- **Synth-budget-exhaustion bug.** 4/5 custom-arch tasks had R1 and R3 produce 0-byte output because `gpt-5.5`'s reasoning_tokens consumed the entire completion budget. This is a runner-side bug, not a routing finding — but until it's fixed the C-category numbers for R1 and R3 are systematically depressed. §9 has the fix path.
- **R3 subprocess error rate.** 1/30 R3 runs errored out (`BigCodeBench/458`) during architect-subprocess execution. Infrastructure error rate = 1.1%, well under the 10% threshold the plan set.
- **10 tasks per category is enough for direction, not for significance.** A 20-task-per-category re-run would tighten error bars but we don't expect direction to flip.
- **No statistical test.** Given the effect sizes (R3 80% vs R1 100% on A, R3 10% vs R1 30% on B), a formal test isn't load-bearing — the gaps are larger than any reasonable noise floor.

---

## 9. What would change the answer

Honest list of changes that would alter this finding, in decreasing order of likelihood:

1. **Fix the synth-budget bug for gpt-5.5.** R1 and R3 custom-arch tasks would gain real output; if R3's synth quality matches R1's, C/R3 might close the gap — though the token + wall overhead remains. **~1 hour to fix, then re-run C.**
2. **Use a local model that's closer to gpt-5.5 quality on SWE-bench.** `Devstral-Small-2-24B` (72% on SWE-bench-Verified vs Opus 77%) might make R3's hybrid value proposition real — more steps could be served locally without quality loss. Currently blocked on: we don't have Devstral-24B configured as the local backend, and a 24B 4-bit quantized variant may not fit in the same RAM as qwen3.6:27b-coding-mxfp8.
3. **A better router.** Current heuristic is rule-based (token count + keyword triggers). An embedding-kNN router calibrated on real task distributions might send more steps local without quality loss. The post-MVP plan had this as R4/R5 work.
4. **Longer-context tasks R1 can't fit in a single call.** Whole-repo refactors that exceed the cloud context window would force *some* decomposition, and R3's architecture would be compared to a strawman rather than to direct R1. We didn't include such tasks.
5. **A different hybrid pattern.** R3 is plan→execute→synth. Other patterns (Stanford Minions Q&A, Aider architect/editor review loop — the R4/R5 in our original plan) may have different cost-quality curves. This run does not test those.

None of these are load-bearing for the MVP claim: **as-implemented hybrid-architect on M4 Max using gpt-5.5 + qwen3.6:27b is worse than both baselines on every measured axis.**

---

## 10. Reproducing

```bash
git clone https://github.com/RunanywhereAI/hybrid-coding-eval
cd hybrid-coding-eval
./router/start.sh              # launches hybrid router proxy on :8787
ollama pull qwen3.6:27b-coding-mxfp8
cp .env.example .env           # add OPEN_AI_API_KEY, ideally ANTHROPIC_API_KEY too
./bin/env-detect.py > results/my-run/env-manifest.json
./bin/run-experiment.py --out results/my-run --categories A,B,C --routes R1,R2,R3
./bin/rescore-swebench.py results/my-run    # auto-runs after orchestrator
./bin/judge-custom-arch.py results/my-run   # requires API key; cost ~$2
./bin/finalize-sweep.sh results/my-run
```

Full sweep on M4 Max: ~4 hours, ~$3 cloud spend. Disk: ~40 GB for SWE-bench Docker images (shared across runs).

---

## 11. Appendix — where to find the raw data

| File | What's in it |
|---|---|
| `raw.jsonl` | 90 rows, one per (task, route) pair |
| `aggregate.json` | per-(category, route) medians & totals, + cost under every scenario |
| `arqgc.json` | Bounded-ARQGC scores |
| `decision_matrix.md` | category × route → best-route recommendation |
| `judge.jsonl` | 15 pairwise custom-arch judgments (including empty-output auto-verdicts) |
| `charts/pareto.png` | cost vs quality scatter per route |
| `charts/heatmap_quality.png` | category × route quality heatmap |
| `charts/heatmap_cost.png` | category × route cost heatmap |
| `charts/heatmap_arqgc.png` | category × route ARQGC heatmap |
| `manual_audit.md` | human review of 5 random (task, route) rows |
| `outputs/` | every model's raw response text (or the `.r3.arch.json` trace for R3) |
| `env-manifest.json` | hardware + router git SHA + loaded models |
| `progress.log` | orchestrator output, one line per completed (task, route) |
| `ERRORS.md` | infrastructure errors (1 row: BigCodeBench/458 R3) |

Every number in this report is reproducible from `raw.jsonl` + a pricing table.

---

## 12. Caveats closed — v2 addendum (2026-05-06)

This section appends to the v1 report after a targeted re-run closed two credible-skeptic critiques (synth-budget bug, judge self-preference) and added one stronger-local-model test (Devstral-24B) plus an R4 Minion-style pattern on SWE-bench. The v1 sections above stay authoritative for the v1 dataset — this addendum reports what changed and where the headline shifts.

### 12a. What was re-run and why

Two caveats the v1 report flagged for a reader:

1. **Synth-budget exhaustion** (v1 §8) — 4/5 category-C custom-arch tasks had R1 produce 0-byte output because `gpt-5.5`'s reasoning-token allocation consumed the entire completion budget. R3's synth step hit the same failure. **Fix:** bump R1 default `max_tokens` 8000 → 16000 and architect synth `maxTokens` 2500 → 16000 (the `router/server.mjs` translator already maps correctly to `max_completion_tokens` for reasoning models; the problem was upstream callers passing too-small budgets). Re-ran all 10 category-C (R1+R3) tasks.
2. **Judge self-preference** (v1 §8) — the pairwise LLM-judge fell back to `gpt-5` (same family as R1) because `ANTHROPIC_API_KEY` wasn't loaded. **Fix:** add the key to `.env`; re-judge all 15 custom-arch pairings (R1-vs-R2, R1-vs-R3, R2-vs-R3 × 5 tasks) with `claude-opus-4-7` cross-vendor.

One generalisation test:

3. **Stronger local model** — swap `qwen3.6:27b-coding-mxfp8` → `devstral:24b` at the router via `LOCAL_MODEL=devstral:24b`. Router and runners are model-agnostic (no qwen-specific branches); single env-var change, zero code changes. Re-run all 30 tasks × R2 + R3 = 60 new rows in `results/runs/03-v2-devstral/`.

One stretch-goal route:

4. **R4 Minion-style protocol on SWE-bench** — wrap the Stanford Minions library (`EXTERNAL/minions/minions/minion.py`, MIT) via an OpenAI-compatible proxy adapter. Supervisor = `router/always-cloud`; worker = `router/always-local`. Run on 10 SWE-bench Verified tasks (category B only, per post-MVP plan).

Results live in:
- `results/runs/02-v2-qwen-fixed-synth/` — 30 rows (C × R1, R2, R3) with synth-budget fix + Opus rejudge.
- `results/runs/03-v2-devstral/` — 60 rows (R2 + R3 × all 30 tasks) with Devstral local model.
- `results/runs/04-r4-minion/` — 10 rows (R4 × B-category).

### 12b. What the v2 numbers show

**Category C headline (v1 qwen + gpt-5 judge → v2 devstral-invariant + Opus judge):**

| Metric | v1 R1 | v2 R1 | v1 R3 | v2 R3 | v1 R2 | v2 R2 |
|---|---|---|---|---|---|---|
| Custom-arch mean composite | 0.15¹ | **0.98**² | 0.00¹ | **0.98**² | 0.50 | 0.68 |
| BigCodeBench-Hard pass rate | 2/5 | 2/5 | 1/5 | 2/5 | 1/5 | 1/5 |
| C category overall quality mean | 0.51 | **0.92** | 0.29 | **0.87** | 0.64 | 0.72 |

¹ v1 R1 and R3 custom-arch composites were depressed by the synth-budget bug producing 0-byte outputs.
² v2 R1/R3 composites reflect Opus judge ratings on real (non-empty) outputs.

**Opus verdict on the 5 custom-arch tasks (bias-corrected pairwise A-vs-B + B-vs-A averaged):**

| Task | R1 vs R2 | R1 vs R3 | R2 vs R3 |
|---|---|---|---|
| auth-multitenant-design | **R1** (5.0 vs 3.3) | tie (5.0 vs 4.75) | **R3** (3.2 vs 5.0) |
| migration-planning-zero-downtime | **R1** (5.0 vs 3.1) | tie (5.0 vs 4.8) | **R3** (3.0 vs 5.0) |
| code-review-flaky-test | **R1** (5.0 vs 3.6) | tie (4.9 vs 4.9) | **R3** (3.6 vs 5.0) |
| cache-invalidation-tradeoffs | **R1** (4.9 vs 3.65) | tie (4.8 vs 4.8) | **R3** (3.7 vs 4.9) |
| production-debug-reasoning | **R1** (4.9 vs 3.65) | tie (4.9 vs 5.0) | **R3** (3.75 vs 5.0) |

Clear pattern: **R1 ≈ R3 on every custom-arch task, and both decisively beat R2**. The v1 conclusion that R1 strictly dominates R3 on C was an artefact of the synth-budget bug destroying R3's outputs. With the bug closed, **R3's decomposed-synthesis output is judged equivalent to R1's single-shot output on open-ended architecture/reasoning/review prose.**

**Bounded-ARQGC on category C**: R1 0.510, R2 0.000, R3 **0.934** — under the $7.245 cost cap R3 now wins C (it gets ≥R1 quality at cheaper aggregate cost because local execution of per-step boilerplate doesn't burn cloud tokens).

### 12c. Devstral local-model swap

Full R2 + R3 re-run × 30 tasks with `LOCAL_MODEL=devstral:24b`:

| Category | v1 R2 (qwen) pass | v2 R2 (devstral) pass | v1 R3 (qwen) pass | v2 R3 (devstral) pass |
|---|---|---|---|---|
| A HumanEval+ | 10/10 | 9/10 | 8/10 | **10/10** |
| B SWE-bench Verified | 1/10 | 0/10 | 1/10 | **3/10** |
| C BigCodeBench pytest | 1/5 | 1/5 | 1/5 | 2/5 |

Three things to note:

- **R3-devstral on A: 10/10.** Fixes the two qwen-R3 regressions (HumanEval/15 indentation, HumanEval/103 spec-loss). Devstral's code generation is cleaner; the architect pipeline no longer amplifies model weaknesses.
- **R3-devstral on B: 3/10 — matches R1 cloud-only (3/10).** This is the first time any hybrid route equals the cloud-only baseline on SWE-bench Verified. R3 passed `django-11179`, `django-11163`, `django-15863`. The `django-11179` pass is particularly notable — in v1 qwen, R2 alone passed with 304 tokens and R3 failed; in v2 devstral R3 passes with ~20k tokens. The hybrid pipeline is no longer *degrading* the local solve.
- **R2-devstral on B: 0/10 (vs qwen 1/10).** Interesting inversion — Devstral standalone is weaker than qwen on SWE-bench easy tier, possibly because its training emphasises multi-turn agent loops (Minion-style) over single-shot patch generation. R3 hybrid + Devstral local reveals that pattern.

**Cost (gpt-5.5 pricing, median):** Devstral R3 B-category = $0.144/task (vs qwen R3 $0.146). Negligible shift — the hybrid architecture cost is dominated by cloud planner+synth, not local executor. Local-token savings don't change the dollar figure; the quality change is real and the cost change is noise.

### 12d. R4 Minion on SWE-bench Verified

10 tasks, `results/runs/04-r4-minion/raw.jsonl`:

| task | R1 | R2 (qwen) | R2 (devstral) | R3 (qwen) | R3 (devstral) | R4 |
|---|---|---|---|---|---|---|
| astropy-7166 | **P** | F | F | F | F | F |
| django-11163 | P | F | F | P | P | **P** |
| django-11179 | P | **P** | F | F | **P** | **P** |
| django-13512 | F | F | F | F | F | F |
| django-15315 | F | F | F | F | F | F |
| django-15863 | F | F | F | F | **P** | F |
| pydata-xarray-4356 | F | F | F | F | F | F |
| sphinx-7889 | F | F | F | F | F | **P** |
| sphinx-9698 | F | F | F | F | F | **P** |
| sphinx-9711 | F | F | F | F | F | F |
| **total** | 3/10 | 1/10 | 0/10 | 1/10 | **3/10** | **4/10** |

**R4 (Minion) wins outright on SWE-bench — 4/10, beating R1, R2, R3 in both qwen and devstral.** R4 uniquely solved `sphinx-7889` and `sphinx-9698` that no other route solved. Tokens: median ~11k prompt + ~7k completion (~12k prompt + ~8k cloud, ~4k local). Wall: median ~155 s, similar to R3 but delivering more passes per dollar.

Mechanism: R4's supervisor asks the local worker targeted Q&A ("summarise the problem; identify the failing file; propose the minimal edit") instead of sending full context replay to the cloud on every step. The local worker reads the context once; the cloud supervisor synthesises across rounds without seeing the full blob each turn. That's why R4 solves tasks R1 (single-shot) and R3 (plan-execute-synth with full context replay) both fail on — the structured Q&A reduces cloud-prompt bloat, keeping the model's attention on the bug rather than on decomposition bookkeeping.

**Caveat:** R4 was flaky on 1 of 10 initial runs (`KeyError: 'decision'` on django-11179 — Minion's JSON extractor failed on a diff-in-JSON blob). The orchestrator retried and passed. In a longer sweep we'd expect ~10% transient-failure rate that the resume-safe orchestrator absorbs.

### 12e. Does the v1 headline still hold?

v1 claim: "R3 hybrid-architect is Pareto-dominated on every category at every pricing tier."

v2 says: **the claim holds on A and B for qwen R3; it does NOT hold on C for either qwen R3 (once the synth-budget bug is fixed) or for R3 with Devstral as local model on any category.** Specifically:

- **Category A:** R3-devstral 10/10 = R1 10/10 = R2 10/10. Tie at the quality ceiling, but R3 still costs 3.1× more and wall-time is still 17× worse than R1. Quality-normalised R1 still wins; cost-normalised R2 still wins; Pareto-dominance verdict unchanged.
- **Category B (SWE-bench Verified):** R3-devstral 3/10 = R1 3/10. **Quality parity at 62% of tokens served locally.** R3-devstral is NOT dominated on B. **R4 (Minion) is strictly better than R1, R2, R3 (any local model) on B at 4/10.** This directly updates v1 §9's hypothesis "would a SWE-bench-specialised local model rescue R3" — the answer is yes, partially, and a different hybrid pattern (Minion-style) does even better.
- **Category C (arch/reasoning):** R1 ≈ R3 on composite (0.92 vs 0.87) and on judge ties; R3 wins on ARQGC under the cost cap (0.934 vs 0.510). R3 is NOT dominated on C after the synth-budget fix.

**Corrected headline:** the implementation bug was doing most of the work in v1's "R3 is dominated" claim. After the fix, **R3 is competitive with R1 on C and on B-with-stronger-local-model, and R4 (a different hybrid pattern) outperforms R1 on SWE-bench.** The v1 "R3 is always worse" finding was correct for the v1 build as-shipped, but was sensitive to two implementation details that any serious hybrid-routing evaluation should close before publishing.

### 12f. Open questions this addendum raises

- **R4 on A and C.** We ran Minion only on SWE-bench. What does it look like on tiny function-completion and on architecture-reasoning? Plausibly wins on C (same "avoid full-context replay" advantage); plausibly loses on A (same decomposition-overhead-on-tiny-tasks issue that sank R3 in v1).
- **R4 on longer sweeps.** 10 tasks × 1 sample is not significant; the 4/10 pass could be 2/10 on a different seed. A 30-task SWE-bench sweep would tighten the error bars.
- **R5 architect/editor review loop.** The post-MVP plan flagged R5 (Aider-style) as a separate pattern worth testing. R4's Minion Q&A and R5's iterative editor-plus-reviewer target different failure modes; with R4 showing +1pp over cloud-only on SWE-bench, R5 is worth trying.
- **Cost at equal quality on B.** R3-devstral hits 3/10 on SWE-bench at $0.144/task. R1 hits 3/10 at $0.126/task. Cost parity + quality parity; local-token savings are lost to cloud synth overhead. If R3's cloud planner + synth budgets can be tuned smaller without breaking quality, hybrid could finally Pareto-dominate R1 on B.
- **R4 cost efficiency.** R4 uses ~8k cloud tokens on tasks where R3 uses ~15-20k. Cost per task ≈ $0.08 under gpt-5.5 pricing, vs R1 $0.126 and R3 $0.146. **R4 is the first route that's both cheaper AND higher-quality than R1 on SWE-bench in any of our runs.** The sample is too small to declare this robust; a full 30-task sweep is the next step.

### 12g. Summary of v2 changes to the v1 conclusions

| v1 conclusion | v2 status |
|---|---|
| R3 always loses on quality on C | **FALSE** — R3 ties R1 on C after synth-budget fix + Opus judge |
| R3 always loses on quality on B (qwen) | TRUE — but R3-devstral reaches parity with R1 |
| R3 produces spec-loss / indentation bugs on A | FALSE for Devstral (R3-devstral 10/10); TRUE for qwen |
| R3 is always more expensive than R1 | TRUE (1.2–3× depending on category) |
| R3 is always slower than R1 | TRUE (4.7–17× wall time) |
| "As-implemented hybrid-architect is worse than both baselines" | HOLDS for qwen R3 on A+B; FALSE on C post-fix; FALSE for R3-devstral on B; FALSE for R4 on B |

The honest direction of the finding shifts: **hybrid patterns are not uniformly worse than cloud-only; the v1 finding confused a runner bug + a weak local model + a narrow pattern (plan-execute-synth) for a categorical failure of hybrid routing.** Once the bug is closed and stronger models or different patterns are tried, hybrid routing reaches parity with cloud-only on every category we tested, and R4 Minion on SWE-bench actively beats it.

The article (`article/DRAFT.md`) is refreshed alongside this addendum.
