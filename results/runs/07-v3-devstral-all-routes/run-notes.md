# Run 07 — v3-devstral-all-routes

**Date:** 2026-05-10 / 2026-05-11
**Purpose:** the v3 sweep. First time we ran all 5 routes (R1..R5) across the full category set, including the new **category D** (real-developer tasks), with `devstral:24b` as the local model for every hybrid route.

## What this run is

250 rows = **50 unique tasks × 5 routes**:

| category | n tasks | shape |
|---|---:|---|
| A — HumanEval+ | 10 | function-completion (functional) |
| B — SWE-bench Verified | 10 | repo-patch (functional, docker SWE-bench harness) |
| C — BigCodeBench-Hard + custom_arch | 5 + 5 | functional + LLM-judge prose |
| D — real-dev | 4 × D1..D5 = 20 | mixed: D1/D5 functional; D2 deferred; D3/D4 judge prose |

**Cloud:** `gpt-5.5`. **Local:** `devstral:24b`. **Judge:** `claude-opus-4-7` (cross-vendor). **Router classifier:** `qwen3:0.6b` (heuristic strategy, threshold null). Pricing primary scenario `openai-gpt5.5`; six scenarios stored in `aggregate.json` for re-pricing.

Wall total: **11.9 hours** across the 250 rows. Zero infra errors (`error=None` on every row). Total cost: **$39.34** under gpt-5.5 / **$100.77** under opus-4.7 across the whole sweep. Per-route wall split: R1 ≈ 0.64 h, R2 ≈ 0.22 h, R3 ≈ 2.52 h, R4 ≈ 1.51 h, R5 ≈ 7.05 h. R5 alone accounts for 59% of total wall.

## What changed since runs 03 + 04

- **Added R5** — DevMinion architect/editor review-loop (`runners/r5_devminion.py`). Cloud architect → local editor → cloud reviewer, up to 3 rounds. Distinct from R4 Minion's supervisor/worker Q&A. R5 calls both backends densely; median total calls = 8 per row (R4 median = 0; R3 median = 10.5).
- **Added category D** — 20 real-dev tasks across five shapes (4 tasks each):
  - **D1** — small from-scratch implementations (auth login, JSON schema, rate-limit, retry decorator)
  - **D2** — external GitHub-issue patches (click, jsonschema, pytest, werkzeug); functional scorer deferred, see below
  - **D3** — refactors (constants-to-enum, extract-helper, try-except→contextmanager, split-god-module)
  - **D4** — code reviews (cache invalidation, pagination, SQL injection, timezone handling)
  - **D5** — small functional one-shots (csv-dedupe, env-var-redactor, log-errors-today, todo-counter)
- **devstral:24b is now the local model everywhere.** Run 03 already showed devstral was the right local model for B; this run confirms it's also the right choice for A, C, and D.
- **Synth-budget fix from run 02 is still applied** (max_tokens 16000 on R1 and R3 synth calls).

## Headlines you can quote

- **R1 cloud-only is the across-categories quality leader.** R1's composite-median across all 250 rows is the highest of any route on three of four categories (A: tied 1.00; C: 0.99 vs R3's 0.90; D: 0.99 vs R3's 0.76). R3 wins on no quality-median cell; R3's win is on the cost-quality frontier (ARQGC), not the quality medians.
- **No hybrid route Pareto-improves on R1 for quality.** Across 250 rows, exactly one row has a hybrid composite strictly greater than R1's composite by more than 0.01: `real-dev/d1-json-schema`, where R3 = 1.00 and R1 = 0.00. Every other row is either a tie or an R1 win.
- **R3 is the cost-quality winner across-all** (Bounded-ARQGC 0.598 at the $8.465 cap, vs R1's 0.297 and R4's 0.396). R3 wins because it sits at the quality frontier on C and D *and* uses ~35% cloud tokens vs R1's 100%.
- **R4 holds parity with R1 on B and A**, under-performs on C (composite 0.72 median vs R1's 0.99), and is in the middle on D (0.59 vs R1's 0.99). R4 is the highest-cloud-fraction hybrid (87%) — its cost story is "R1 with a small local-side detour," not "majority-local."
- **R5 is the worst route on every category except A.** On A, R5 is 4/10 pass (vs every other route ≥ 9/10); on B it is 0/10 (vs R1/R3/R4 at 3/10); on C its composite median is 0.28; on D its composite median is 0.00. R5 is also 2-5× more expensive than R3 and the slowest by wall (median 535 s on D vs R3's 146 s, R4's 116 s).

## Numbers — per (category, route) cell

Pass-rate is the count of `functional_pass=True` over the count of rows where a functional scorer ran (not all D and C rows are functionally scored — see denominators). Quality is `composite` median (functional pass = 1.0; judge composite for prose). Cost is median per-task under `openai-gpt5.5`; wall is median seconds. `cloud_frac_med` is the median across rows of cloud / (cloud + local) tokens. Source: `aggregate.json` regenerated 2026-05-11T16:40:53Z from `raw.jsonl`.

| cat / route | n rows | pass | qual_med | cost/task | wall_med (s) | cloud_frac_med |
|---|---:|---:|---:|---:|---:|---:|
| A / R1 | 10 | **10/10** | 1.00 | $0.012 | 5 | 100% |
| A / R2 | 10 | **9/10** | 1.00 | $0.000 | 5 | 0% |
| A / R3 | 10 | **10/10** | 1.00 | $0.038 | 58 | 38% |
| A / R4 | 10 | **10/10** | 1.00 | $0.066 | 37 | 90% |
| A / R5 | 10 | **4/10** | 0.00 | $0.249 | 263 | 50% |
| B / R1 | 10 | **3/10** | 0.00 | $0.106 | 62 | 100% |
| B / R2 | 10 | 0/10 | 0.00 | $0.000 | 10 | 0% |
| B / R3 | 10 | **3/10** | 0.00 | $0.137 | 166 | 35% |
| B / R4 | 10 | **3/10** | 0.00 | $0.203 | 139 | 87% |
| B / R5 | 10 | 0/10 | 0.00 | $0.390 | 381 | 54% |
| C / R1 | 10 | 1/5 (bcb) | 0.99 | $0.140 | 98 | 100% |
| C / R2 | 10 | 1/5 (bcb) | 0.53 | $0.000 | 33 | 0% |
| C / R3 | 10 | 0/5 (bcb) | 0.90 | $0.301 | 312 | 57% |
| C / R4 | 10 | 0/5 (bcb) | 0.72 | $0.120 | 95 | 89% |
| C / R5 | 10 | 0/5 (bcb) | 0.28 | $0.493 | 717 | 53% |
| D / R1 | 20 | 5/8† | 0.99 | $0.035 | 15 | 100% |
| D / R2 | 20 | 0/8† | 0.00 | $0.000 | 8 | 0% |
| D / R3 | 20 | 5/8† | 0.76 | $0.123 | 146 | 35% |
| D / R4 | 20 | 4/8† | 0.59 | $0.116 | 116 | 86% |
| D / R5 | 20 | 4/8† | 0.00 | $0.404 | 535 | 50% |

† D-pass denominator = 8 (D1's 4 + D5's 4), because **D2 functional scoring is deferred** (4 tasks × all 5 routes = 20 rows with `functional_pass=None` and `composite=None` by design) and D3/D4 (8 rows × 5 routes) use judge composite rather than a binary functional pass. See P2.1 documented gap in `reports/DECISION_TABLE.md`. The deferred D2 harness is the external github-issue / patch-apply pipeline — outputs were still generated and stored; only the verdict is missing.

C-pass denominator = 5 because only the BigCodeBench rows have a functional harness; custom_arch (5 rows) is judge-only.

### Bounded-ARQGC under the $8.465 cost cap (gpt-5.5)

| | R1 | R2 | R3 | R4 | R5 |
|---|---:|---:|---:|---:|---:|
| A | 0.012 | 0.000 | 0.046 | 0.076 | **0.185** |
| B | 0.026 | 0.000 | 0.041 | **0.069** | 0.000 |
| C | 0.185 | 0.000 | **0.342** | 0.090 | 0.175 |
| D | 0.073 | 0.000 | 0.190 | 0.160 | **0.229** |
| **all** | 0.297 | 0.000 | **0.598** | 0.396 | 0.111 |

R3 wins across-all under the cap. By category the recommendation flips: R5 on A and D, R4 on B, R3 on C — but these are within-cap optima that hide R5's terrible quality medians on A (0.00) and D (0.00). The ARQGC integrates quality over the cost budget; a route that scores 1.0 on one task and 0.0 on the other nine can still beat a route that scores 0.5 across the board if its costs sit inside the cap differently. Read the per-shape rows below before quoting ARQGC.

### Token routing — median cloud_fraction per route

R1 = 100% cloud by construction. R2 = 0% cloud by construction. R3 median **35%** cloud across categories (the most local of the hybrid routes). R4 median **87%** cloud (the least local — the cloud supervisor still does most of the writing, since Minion's local worker is asked targeted questions rather than handed full drafting work). R5 sits in the middle around **50%**, but its absolute token counts are 3-5× higher than R3 or R4 because the review-loop replays context across rounds. From `reports/TOKEN_BUDGET.md`:

| route | cloud_prompt (Σ) | cloud_completion (Σ) | local_prompt (Σ) | local_completion (Σ) | total (Σ) |
|---|---:|---:|---:|---:|---:|
| R1 | 37,316 | 121,090 | 0 | 0 | 158,406 |
| R2 | 0 | 0 | 73,487 | 20,814 | 94,301 |
| R3 | 224,831 | 251,024 | 441,468 | 98,361 | 1,015,684 |
| R4 | 361,867 | 182,562 | 51,726 | 43,921 | 640,076 |
| R5 | 350,883 | 594,326 | 625,335 | 308,813 | 1,879,357 |

R5 burned ~1.88 M tokens total — about 1.85× R3 and 2.94× R4. R5 has a *higher* completion-token share than every other route (cloud completion alone = 594K), which tracks with the route producing long architect/reviewer rounds rather than terse answers.

### Wall-clock breakdown per (route, category)

Total wall, hours, summed across all tasks in that cell. Useful for reproduction planning: R5 dominates wall on every category; D is the longest single category because it has 20 tasks not 10.

| | A (h) | B (h) | C (h) | D (h) | Σ |
|---|---:|---:|---:|---:|---:|
| R1 | 0.01 | 0.19 | 0.31 | 0.13 | 0.64 |
| R2 | 0.02 | 0.04 | 0.10 | 0.06 | 0.22 |
| R3 | 0.16 | 0.47 | 0.89 | 1.00 | 2.52 |
| R4 | 0.10 | 0.42 | 0.26 | 0.73 | 1.51 |
| R5 | 0.99 | 1.06 | 1.91 | 3.08 | **7.05** |

R5 on C is 1.91 h for 10 tasks (median 717 s/task). The custom-arch tasks specifically run 449-613 s on R5 — review-loop replay turns 1-minute drafts into 8-minute saga.

### Per-shape D rollup

D1 and D5 are functional-scored (pass / 4 tasks); D3 and D4 are judge-composite (median across 4 tasks). D2 is deferred.

| D-shape | R1 | R2 | R3 | R4 | R5 |
|---|---:|---:|---:|---:|---:|
| D1 (small from-scratch) | 2/4 pass | 0/4 | 2/4 pass | 1/4 pass | 1/4 pass |
| D2 (gh-issue patches) | — deferred — | — | — | — | — |
| D3 (refactors, judge) | **1.00** | 0.00 | 0.84 | 0.72 | 0.00 |
| D4 (code reviews, judge) | **0.98** | 0.12 | 0.54 | 0.64 | 0.02 |
| D5 (small one-shots) | 3/4 pass | 0/4 | 3/4 pass | 3/4 pass | 3/4 pass |

The shape of D3/D4 matters: **R1 wins decisively on every refactor and every code-review task**, with composite ≥ 0.96 on 7 of 8 tasks (lowest is `d4-review-sql-injection` R1 = 0.98). Hybrid routes lose 0.20-0.46 absolute composite vs R1 on D3, and 0.34-0.86 on D4. R5 is the worst across the board on prose D.

### Custom-arch judge pairings (opus-only)

25 verdicts across 5 pairings × 5 tasks, single-order, single-judge (opus-4-7):

| pair | A-wins | B-wins | ties |
|---|---:|---:|---:|
| R1_vs_R2 | 5 | 0 | 0 |
| R1_vs_R3 | 2 | 0 | 3 |
| R2_vs_R3 | 0 | 5 | 0 |
| R3_vs_R4 | 5 | 0 | 0 |
| R3_vs_R5 | 5 | 0 | 0 |

R1_vs_R3 is the only competitive pairing — R3 ties R1 on three of five custom-arch tasks (`migration-planning-zero-downtime`, `code-review-flaky-test`, `cache-invalidation-tradeoffs`) and loses by small margins on `auth-multitenant-design` (0.15) and `production-debug-reasoning` (0.30). R4 and R5 lose decisively to R3. The R3-vs-R5 verdicts are unanimous A-wins — consistent with R5's 0.28 composite-median on C and 0.00 on D3/D4.

This judge file is single-order single-judge. For the triple-judge robustness audit, see `../11-judge-robust-D/judge.jsonl` (D3+D4 only, 96 verdicts).

## Three most-surprising findings

### 1. R5 (DevMinion review-loop) collapses on prose tasks despite spending the most tokens

R5 was added on the hypothesis that an architect/editor review loop would dominate D3 (refactors) and D4 (code reviews) — exactly the prose shapes where a multi-round review should pay. The opposite happened. **R5 composite median = 0.00 on every single D3 task and 3 of 4 D4 tasks**:

- `real-dev/d3-constants-to-enum`: R5 = 0.00 (R1 = 0.96, R3 = 0.54, R4 = 0.54)
- `real-dev/d3-extract-validation-helper`: R5 = 0.00 (R1 = 0.98, R3 = 0.74, R4 = 0.72)
- `real-dev/d3-replace-try-except-with-contextmanager`: R5 = 0.00 (R1 = 1.00, R3 = 0.84, R4 = 0.54)
- `real-dev/d3-split-god-module`: R5 = 0.00 (R1 = 1.00, R3 = 0.84, R4 = 0.74)
- `real-dev/d4-review-cache-invalidation`: R5 = 0.02 (R1 = 1.00, R3 = 0.54, R4 = 0.48)
- `real-dev/d4-review-sql-injection`: R5 = 0.00 (R1 = 0.98, R3 = 0.34, R4 = 0.48)
- `real-dev/d4-review-timezone-handling`: R5 = 0.00 (R1 = 0.98, R3 = 0.78, R4 = 0.64)

R5 burned a median **17 K cloud-prompt + 17 K cloud-completion** tokens, with **5 cloud calls + 3 local calls** per D-task — the most expensive route by far — and produced near-zero-quality outputs on refactor/review. The triple-judge audit in run 11 confirms this is not a judge artefact (all three judges agree on R1 wins across all 16 D3+D4 R1-vs-R3 and R1-vs-R4 pairings; see `../11-judge-robust-D/`). The likely failure mode: the architect/editor handoff loses spec fidelity each round; by the third round the artefact no longer reads as a faithful refactor of the original code, and the reviewer doesn't have the original spec on hand to catch the drift. R5 needs a redesign — likely shorter rounds, the spec re-injected each round, or both — before it earns its slot in the route lineup.

### 2. R3, R4, and R1 all converge to exactly 3/10 on SWE-bench — same three tasks

Every hybrid route that passes any SWE-bench task passes **exactly the same three Django tasks**: `swebench-verified/django__django-11163`, `django__django-11179`, `django__django-15863`. R1 cloud-only passes those three; R3-devstral passes those three; R4 Minion passes those three. Run 04 reported R4 uniquely solving two Sphinx tasks (`sphinx-doc/sphinx-7889` and `sphinx-doc/sphinx-9698`); **neither survives the v3 sweep** — R4's set of passes in run 07 is the same Django triple, no Sphinx. The most parsimonious explanation: the run 04 Sphinx passes were single-sample noise, and the SWE-bench ceiling under our prompt skeleton + devstral:24b is a deterministic 3/10 across all three hybrid routes. This collapses the "R4 beats R1 on SWE-bench" headline from run 04. We have not re-checked the run 04 raw artefacts — but with the v3 sweep using the same models and the same harness, the parsimony argument is strong. Variance bounds need at minimum a 30-task SWE-bench sweep with multiple seeds; we don't have that yet, and the article should hedge the "R4 wins B" claim accordingly.

### 3. Hybrid routes regress on a task the local model alone gets right — and R5 wins where R1 fails, twice

Two related surprises buried in the per-task tables:

(a) On `bigcodebench-hard/BigCodeBench/530` R1 cloud-only passes (composite 1.0) and **R2 local-only also passes** (composite 1.0). All three hybrid routes fail: R3 = 0.43, R4 = 0.86, R5 = 0.43 (none crosses the functional threshold). The cloud's planner appears to over-engineer a one-liner — the hybrid prompt structure introduces a regression on a task either backend solves on its own.

(b) On D1 and D5, R5 was the **only** route that solved `real-dev/d1-retry-decorator` (R5 = pass; R1, R2, R3, R4 all fail) and `real-dev/d5-log-errors-today` (same pattern). Both are small functional tasks where the review loop appears to catch a class of bug that single-shot routes miss. Two-task evidence isn't enough to claim R5 has a unique niche, but combined with finding 1 it sketches the shape of R5's failure mode: review-loops help on small, well-bounded functional tasks where each round can verify a concrete behaviour; they hurt on long-form prose where each round drifts further from the spec. A targeted follow-up: run R5 on 30 more D1/D5-shaped tasks; check if "uniquely solves" replicates above noise.

Also worth flagging in this finding: there's one task where any hybrid beats R1 on composite — `real-dev/d1-json-schema`, where R3 = 1.0 (functional pass) and R1 = 0.0. Across 250 rows, that is the only row where a hybrid route's composite strictly exceeds R1's composite by more than 0.01. The hybrid routes either match or under-perform R1; "Pareto improve on R1 for quality" is, on this dataset, a single-row phenomenon.

## Re-pricing the headline cost numbers

Cost at the run-time scenario (`openai-gpt5.5`) is **$39.34** total. The same token-counts re-priced under five other scenarios from `aggregate.json`:

| scenario | total cost across 250 rows |
|---|---:|
| openai-gpt5.5 | $39.34 |
| openai-gpt5 | $12.71 |
| openai-gpt5-mini | $2.54 |
| anthropic-claude-opus-4.7 | $100.77 |
| anthropic-claude-sonnet-4.6 | $20.15 |

Caveat: these re-priced totals are *cloud* costs only. Local-side tokens cost $0 by construction; wall + electricity costs aren't captured. The ranking between routes is invariant to the cloud scenario chosen (each scenario is a positive scalar on every cloud-token count), so the ARQGC ranking under any of the five scenarios is the same as the gpt-5.5 ranking shown above.

## What this run does NOT answer

Single seed (`seed=42`); no confidence intervals — the 3/10 SWE-bench ceiling, the R5 collapse on D3/D4, and the R5-uniquely-wins-twice finding are all "n ∈ {4, 8, 10} tasks × 1 sample" claims. D2 functional verdicts are missing across all routes (deferred external harness); the cost / cloud-fraction numbers on D2 are still informative but quality is not. R5's failure mode is not characterised — we don't know whether shrinking round count, re-injecting the spec each round, or tightening the editor prompt would fix it. Custom_arch judge verdicts from this sweep haven't been triple-audited (run 11 covers D3+D4 only; the earlier run 10 audited custom_arch from run 02 under qwen, not this run's devstral outputs). The "R1 wins prose" headline rests on opus-4.7 as the sole judge for the 25 custom-arch pairings here; the triple-judge audit lives in run 11 for D3+D4 only.

## Files

| file | notes |
|---|---|
| `raw.jsonl` | 250 rows. Every row has `error: None`. Routes balanced (50 each); categories balanced per the table above. |
| `aggregate.json` | Regenerated 2026-05-11T16:40Z. Per-route, per-category, per-(category, route) medians + sums; six pricing scenarios. |
| `arqgc.json` | Bounded-ARQGC at the $8.465 cost cap (p90 of R1's per-task cost × task count, default scenario gpt-5.5). |
| `decision_matrix.md` | Category × route quality / cost / wall table; per-category ARQGC recommendation. |
| `judge.jsonl` | 25 single-order opus pairings for custom-arch (5 tasks × 5 pair shapes: R1_vs_R2, R1_vs_R3, R2_vs_R3, R3_vs_R4, R3_vs_R5). For the triple-judge robustness audit of D3+D4, see `../11-judge-robust-D/judge.jsonl`. |
| `outputs/` | Per-(task, route) raw model output. R5 outputs include `.r5.arch.json` trace + final `.txt`. ~400 files. |
| `progress.log` | Orchestrator per-row progress; useful for wall-clock spot checks. |
| `bench-config.json` | Variant tag `v3-devstral-all-routes`, models, router config, scoring config, sha256 of the config payload. |
| `env-manifest.json` | Hardware + ollama snapshot at run time: M4 Max 64 GB, ollama 0.23.2, devstral:24b 14 GB present. |
| `charts/` | Pareto plot + heatmaps for quality / cost / ARQGC. Regenerable via `python -m hybrid_coding_eval.analysis.all results/runs/07-v3-devstral-all-routes`. |
