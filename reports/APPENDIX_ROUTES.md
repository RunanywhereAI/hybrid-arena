# Appendix C — per-route worked examples

A single worked example per route, showing the full path from problem
statement → prompt sent → model output → score. Complements
`reports/APPENDIX_TASKS.md` which covers *every* row.

---

## R1 — cloud-only (gpt-5.5)

**How it works.** Single `chat.completions` call to gpt-5.5 via the
router's `always-cloud` pseudo-model. No planning, no routing
decisions. Fastest to implement, fastest to respond.

**Worked example: `humaneval-plus/HumanEval_99` (Cat A).**

- Problem: complete `def closest_integer(value: str) -> int` that
  rounds a decimal string to the nearest integer, with half-to-even
  wrong and half-away-from-zero right.
- Prompt: the full docstring-adorned function stub wrapped in the
  R1 template (see `APPENDIX_TASKS.md` for the prompt reconstruction).
- Output: a single fenced Python block with the completion.
- Score: **PASS** (1/1 pytest).
- Tokens: cloud=527 (prompt=175, completion=352, reasoning=163).
- $ under gpt-5.5: $0.0114.

**Where R1 shines.** Cat A — every HumanEval+ row passes under R1 in
the MVP dataset. Small tasks fit in one cloud call. No hybrid
overhead justifies itself here.

**Where R1 loses.** Cat B at 3/10. Real software-engineering tasks
need multi-turn exploration; a single-shot prompt to gpt-5.5 often
misses the required file context.

---

## R2 — local-only (devstral:24b / qwen3.6:27b)

**How it works.** Single call to the local Ollama model via
`router/always-local`. 100% local, $0 cloud cost.

**Worked example: `humaneval-plus/HumanEval_13` (Cat A).**

- Problem: greatest common divisor of two ints.
- Prompt: same R1 template, but routed to devstral:24b.
- Output: devstral's completion. Structurally clean because it's a
  small self-contained task.
- Score: PASS (all HumanEval+ tests pass).
- Tokens: local=621 (prompt=182, completion=439).
- $ under every scenario: $0.00.

**Where R2 shines.** Cat A matches R1 at 9/10 — the local model is
fully capable on small function-completion tasks. Zero cost.

**Where R2 loses.** Cat B at 1/20 across both local models. The
24B / 27B models don't have enough reasoning context for real SWE-bench
issues. Also weaker on novel library APIs in Cat C BigCodeBench.

---

## R3 — hybrid architect (cloud planner → executor → cloud synth)

**How it works.** Three-phase pipeline:

1. **Planner** — gpt-5.5 decomposes the task into a JSON array of
   steps. Each step has `router_hint: auto|local|cloud`.
2. **Executor** — for each step, the heuristic router picks cloud or
   local based on the step's content (complexity keywords, token
   count, tool use). Most steps go local.
3. **Synth** — gpt-5.5 takes the step outputs and writes the final
   deliverable.

**Worked example: `custom-arch/auth-multitenant-design` (Cat C,
Opus-judged).**

- Problem: design a multi-tenant auth system with Postgres RLS,
  hybrid JWT+refresh, and named pitfalls.
- Planner output: 8 steps (analyse requirements, schema, RLS, JWT,
  login flow, refresh flow, pitfalls, assemble).
- Router trace: steps 1–6 routed local; step 7 + synth routed cloud.
- Output: 8 KB of prose with inline SQL + JWT claim diagrams.
- Score (Opus judge, T-14 triple-verify): **tie** with R1.
- Tokens: cloud=24,561 (planner+synth), local=19,382 (exec steps).
- $ under gpt-5.5: $0.72 / row.

**Where R3 shines.** Cat C custom_arch — ties R1 on 4/5 prose tasks
under Opus judge, confirmed under Sonnet + gpt-5.5 judges (T-14). The
local executor handles the schema/JWT generation; cloud planner +
synth hold the plan together.

**Where R3 loses.** Cat B at 4/20 (both local models). The heuristic
router sends too many steps local on SWE-bench, where even the easy
tier needs cloud-grade reasoning at each step. The cost also piles up
— R3 is the most expensive route in absolute dollars ($12.20 total
across 69 rows on gpt-5.5).

**The prompt-caching claim.** §6 of the article explains why
enabling `router.prompt_cache: true` doesn't actually reduce cost:
OpenAI's cache needs a 1024-token prefix match and R3's static
prompts are 400 + 80 tokens. See `docs/T-13-analysis.md`.

---

## R4 — Minion (cloud supervisor asks local worker targeted questions)

**How it works.** Port of Stanford's Minion protocol
(`vendor/minions/minions/minion.py`). Two agents:

1. **Supervisor** — cloud (gpt-5.5) — sees the *task* (not the full
   context) and decides what to ask the worker.
2. **Worker** — local (devstral:24b) — sees the *full context* (the
   repo / problem statement / long prose), answers the supervisor's
   questions, provides the final answer when the supervisor says
   `provide_final_answer`.

Supervisor never re-reads the full context. Local worker never
re-asks the task. This is the key token-economy win: context stays
local, queries go over the cloud.

**Worked example: `swebench-verified/sphinx-doc__sphinx-7889` (Cat B).**

- Problem: Django-style issue in Sphinx. Bug report ~2 KB.
- Minion round 1: supervisor reads the short problem statement, asks
  worker "what's the current behavior when generic-types are used as
  argument defaults? Show me the relevant code path."
- Worker round 1: reads the repo + commit, answers with the specific
  lines + ~50 tokens of explanation.
- Minion round 2: supervisor asks for a patch proposal.
- Worker round 2: generates a unified diff.
- Minion round 3: supervisor says `provide_final_answer` with the diff.
- Score: **PASS** (one of the 4/10 R4 victories).
- Tokens: cloud=14,965 (supervisor back-and-forth), local=1,908
  (worker's full-context reads).
- $ under gpt-5.5: $0.22 / row.

See `results/runs/04-r4-minion/minion_logs/` for the verbatim
multi-round Q&A transcripts on every row.

**Where R4 shines.** Cat B — 4/10 pass, one more than R1. Specifically
wins on `sphinx-doc/sphinx-7889` and `sphinx-doc/sphinx-9698` that no
other route solves. The targeted-question pattern works when the
problem hides inside a long repo context.

**Where R4 loses.** Cat A — matches R2 at 9/10, loses to R1 at 10/10.
Cat C BigCodeBench — 1/5, worst of any route. The Minion protocol
has no advantage when the answer is a library-API choice the local
model doesn't know anyway. custom_arch rows come out as unscored
prose in T-11's run (judge-pending); T-14 didn't re-judge Cat C
custom_arch from run 06 separately — future work.

---

## Comparison at a glance

| | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| cloud calls | 1 | 0 | 1 (plan) + 1 (synth) | 1+ per round |
| local calls | 0 | 1 | 0–N (per step) | 1 per round |
| tokens routed local | 0% | 100% | 51% | 12% |
| Cat A pass (MVP + Wave 2) | 10/10 | 19/20 | 18/20 | 9/10 |
| Cat B pass | 3/10 | 1/20 | 4/20 | **4/10** |
| Cat C pass (functional tier) | 10/20 | 7/15 | 10/24 | 1/5 |
| $ per correct Cat B (gpt-5.5) | $0.42 | — | $0.72 | $0.56 |
| Strong suit | small tasks, $/correct ceiling | $0 cost floor | architectural prose | context-heavy SWE |

---

## Where each route lives in the codebase

| Route | Python runner | Node helpers |
|---|---|---|
| R1 | `src/hybrid_coding_eval/runners/r1_cloud_only.py` | `router/server.mjs` |
| R2 | `src/hybrid_coding_eval/runners/r2_local_only.py` | `router/server.mjs` |
| R3 | `src/hybrid_coding_eval/runners/r3_hybrid_architect.py` | `router/pipelines/architect/runner.mjs`, `router/pipelines/architect/core.mjs` |
| R4 | `src/hybrid_coding_eval/runners/r4_minion.py` | `vendor/minions/minions/minion.py` (vendored) |

All four runners expose the same `run(task, …) → ResultRow` surface
so the orchestrator (`hybrid_coding_eval.core.experiment.run_pair`) is
route-agnostic.
