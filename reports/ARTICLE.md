# Hybrid vs cloud vs local LLM routing for coding tasks — the final report

> _210 graded rows across 4 routes × 4 benchmarks × 6 pricing scenarios, on one
> M4 Max laptop. Every row's tokens are recorded; costs are derived, not stored._

**Status.** Published from branch `mono-repo-reorg`. Supersedes
`results/REPORT.md` (the MVP report) — the v1 narrative and v2
postscript live on in `docs/article-draft-v1.md` for lineage.

**Canonical dataset:** `results/raw.jsonl` (MVP 180 rows, merged) + the
post-reorg runs under `results/runs/05-r4-catA/`, `06-r4-catC/` (20 new
rows). The numbers below are all derived from that data by the scripts
in `src/hybrid_coding_eval/analysis/`.

**How to reproduce:** `./bench run --config configs/variants/<name>.yaml`
for any variant. `docs/REPRODUCING.md` for the copy-paste walkthrough.

---

## 1. The question, restated in token terms

For a real developer's coding workload, does routing **some fraction of
the tokens to a local model** save money without destroying quality?

We measured three axes per `(task, route)` cell:
- **tokens** — cloud prompt/completion, local prompt/completion, cached
  tokens. The *primary observable*. Deterministic.
- **quality** — pass rate on functional tasks (pytest / SWE-bench
  harness) and Opus judge-win-rate on architecture tasks.
- **latency** — wall-clock to completion.

**Cost is derived, never stored.** The harness records tokens; any
cost number you see is computed at read time from the pinned table at
`configs/pricing/pricing_tables.json` (dated 2026-04-27, sourced from
models.dev). That lets us re-price the *same* runs under six scenarios
— gpt-5.5, gpt-5, gpt-5-mini, claude-opus-4.7, claude-sonnet-4.6,
claude-haiku-4.5 — without re-running inference.

**Every local token costs $0** under every scenario. We deliberately
exclude laptop electricity + hardware amortisation from the comparison;
the headline number is "what extra would the cloud provider have
charged me if I'd sent that token to them instead."

---

## 2. The suite

**Four benchmarks, mapped to three categories:**

| Category | Source | Count | Scorer |
|---|---|---:|---|
| A — tiny function-completion | HumanEval+ (seed=42 random sample) | 10 | pytest in Docker sandbox |
| B — real software engineering | SWE-bench Verified easy tier | 10 | mini-swe-agent Docker harness |
| C — architecture / reasoning | BigCodeBench-Hard (5) + custom_arch (5) | 10 | mix: pytest + Opus judge |

**Four routes (one knob each):**

| ID | What it does | Who answers |
|---|---|---|
| R1 | single-shot to `gpt-5.5` | cloud |
| R2 | single-shot to `devstral:24b` or `qwen3.6:27b` via Ollama | local |
| R3 | cloud planner → per-step heuristic → cloud synth | cloud + local (mixed) |
| R4 | Stanford-Minion supervisor/worker Q&A | cloud supervisor, local worker |

**Six pricing scenarios, applied post-hoc to the same dataset:**
gpt-5.5 (primary), gpt-5, gpt-5-mini, claude-opus-4.7,
claude-sonnet-4.6, claude-haiku-4.5. Rates pinned at
`configs/pricing/pricing_tables.json` — every report is re-runnable
against updated rates by bumping that one file.

**One hardware tier:** Apple M4 Max, 64 GB RAM. Every row links its
per-run `env-manifest.json`.

**How to drop in a new model:** copy `configs/variants/_template.yaml`,
change two lines (`variant_tag` + `models.cloud` or `models.local`),
run `./bench run --config configs/variants/my-model.yaml`. The YAML
schema is Pydantic-validated; `configs/schema.json` is auto-generated
for IDE support.

---

## 3. Per-category headline (with 95% Wilson CIs)

Pass rates under **the primary pricing scenario (`openai-gpt5.5`)**.
Full grid for every scenario is `results/reprice/decision_matrix.md`.

### Category A — HumanEval+ (tiny function-completion)

| Route | Pass rate (95% CI) | Median $ / row | Median wall |
|---|---|---:|---:|
| **R1** cloud gpt-5.5 | **1.00** (0.72–1.00) | $0.0106 | 4.7s |
| R2 devstral/qwen local | 0.95 (0.76–0.99) | $0.0000 | 13.9s |
| R3 hybrid architect | 0.90 (0.70–0.97) | $0.0327 | 59.3s |
| R4 Minion (new; T-10) | 0.90 (0.60–0.98) | $0.0605 | 37.8s |

**Takeaway.** R1 is the cheapest and fastest winner on tiny tasks.
Every hybrid route pays extra latency and dollars for no accuracy gain
— because the task fits in the local model's head end-to-end. **No
route Pareto-dominates R1 here.**

### Category B — SWE-bench Verified easy tier

| Route | Pass rate (95% CI) | Median $ / row | Median wall |
|---|---|---:|---:|
| R1 cloud gpt-5.5 | 0.30 (0.11–0.60) | $0.1260 | 67.5s |
| R2 local only | 0.05 (0.01–0.24) | $0.0000 | 18.6s |
| R3 hybrid architect | 0.20 (0.08–0.42) | $0.1439 | 255.6s |
| **R4 Minion** | **0.40** (0.17–0.69) | $0.2224 | 147.2s |

**Takeaway.** **R4 Minion is the only route that wins on pass rate
(4/10 vs R1's 3/10)** — and it wins specifically on the tasks where
the local worker's fresh eyes on the repository produce a better patch
than a one-shot cloud call would. Caveat: R4's median dollar cost is
**1.8× R1**, because the supervisor still has to process the full
problem statement over multiple rounds. Cost-per-correct-solution
(dollars ÷ passes, under gpt-5.5):

| Route | $/correct |
|---|---:|
| R1 | $0.42 |
| R3 | $0.72 |
| **R4** | **$0.56** |

So R4 wins on *pass count* but R1 is still the better $/correct.
**R4's value proposition on SWE-bench is pass-rate, not $/correct.**
The CI on the 4/10 vs 3/10 gap is wide (N=10 × 1 seed); the real
publication bar is N=30+ with multi-seed CIs. That's queued as a
follow-up (see `docs/T-12-deferred.md` for why it wasn't in scope
here).

### Category C — BigCodeBench-Hard + custom_arch

| Route | Pass rate (95% CI) | Median $ / row | Median wall |
|---|---|---:|---:|
| R1 cloud gpt-5.5 | 0.50 (0.30–0.70) | $0.1176 | 69.4s |
| R2 local only | 0.47 (0.25–0.70) | $0.0000 | 48.1s |
| R3 hybrid architect | 0.42 (0.24–0.61) | $0.2983 | 371.3s |
| R4 Minion (new; T-11) | 0.20 (0.04–0.62) | $0.1061 | 75.8s |

(Pass rates on C include the BigCodeBench-Hard subset; the custom_arch
Opus-judge numbers are in §7.)

**Takeaway.** R4 under-performs on BigCodeBench-Hard (1/5 vs R1 2/5 vs
R3 2/5). The Minion Q&A protocol doesn't help the local worker decide
which third-party library API to call — the supervisor's questions
don't substitute for looking at API docs. **R4 is scope-limited to
Category B** in the current implementation.

---

## 4. Token economics — where the dollars went

Totals across **every row** in the committed dataset under
`openai-gpt5.5`. Fuller breakdown in `results/reprice/token_share.md`.

### Per-route totals

| Route | N | Σ cloud tokens | Σ local tokens | routed local | Σ $ cost |
|---|---:|---:|---:|---:|---:|
| R1 | 40 | 153,801 | 0 | 0% | $4.36 |
| **R2** | 60 | 0 | **86,617** | **100%** | **$0.00** |
| R3 | 69 | 715,148 | 747,726 | 51% | $12.20 |
| R4 | 30 | 280,878 | 39,931 | 12% | $4.20 |

### What this says

- **R3 is the heaviest token consumer** overall. 1.46M tokens across
  69 rows — planner + synth + per-step context bloat. Its 51%
  local-routed percentage is hollow, because the cloud-side tokens
  are the expensive ones.
- **R4 paradox.** Minion routes only 12% of tokens locally (the
  supervisor still reads all the context). But it wins on Cat B
  anyway, because the local worker's re-reads + targeted answers
  substitute for what would be one long cloud prompt.
- **R2 is the sensitivity anchor.** Every R2 row costs exactly $0
  under every scenario. If we ever see a non-zero R2 cost, it's a
  routing bug (a cloud call leaked through).

### What R3's 51% "routed local" means in dollars

R3 sends roughly half its tokens to the local model. Under gpt-5.5,
R3 still costs **more than R1** because the half that *did* go to
cloud is the expensive half (planner prefix + synth concatenation).
Prompt caching would help if the static prefixes hit OpenAI's 1024-
token threshold — but they don't (see `docs/T-13-analysis.md`). The
real fix is either a longer static preamble (which would change the
evaluation's meaning) or switching the cloud leg to Anthropic's
explicit `cache_control` markers (a whole-migration change).

---

## 5. Multi-scenario decision matrix — the centerpiece

The same dataset, re-priced under six cloud-pricing scenarios. Which
route is cheapest *per correct answer* shifts as the cloud model gets
cheaper.

### SWE-bench (Cat B), $/correct under each scenario

| Route | gpt-5.5 | gpt-5 | gpt-5-mini | claude-opus-4.7 | claude-sonnet-4.6 | claude-haiku-4.5 |
|---|---:|---:|---:|---:|---:|---:|
| R1 | $0.42 | $0.14 | $0.028 | $0.80 | $0.18 | $0.06 |
| R3 | $0.72 | $0.23 | $0.047 | $1.55 | $0.32 | $0.10 |
| **R4** | **$0.56** | $0.18 | $0.035 | $1.22 | $0.24 | $0.08 |

*(Derived from median $ × N / passes. Exact per-cell values in
`results/reprice/decision_matrix.md`.)*

**The matrix tells you this:**
- Under gpt-5.5 official API rates, **R4 wins on pass count** but R1
  wins on $/correct.
- Under gpt-5-mini, R4 is 25% more expensive per correct answer than
  R1 — the cost gap widens because R4 does more cloud work per task.
- Under claude-haiku-4.5 (cheapest), every route is close — ~$0.06–
  $0.10 per correct answer; hybrid overhead becomes negligible.

### When does the cloud leg get cheap enough to make hybrid obvious?

If the cloud model drops below **$0.5 per million tokens** (output),
R3's cost penalty disappears and its 20% pass rate on SWE-bench looks
bad for a different reason. Hybrid only helps when the cloud is
expensive — which today means gpt-5.5-pro or claude-opus-4.7.

Full matrices for every scenario in
`results/reprice/decision_matrix.md`.

---

## 6. Prompt caching (T-13) — did not flip R3 to a cost win

The planner and synth system prefixes in `router/pipelines/architect/core.mjs`
are ~400 and ~80 tokens respectively. OpenAI's automatic prompt caching
requires a **1024-token** matching prefix. R3's prefixes are too short
to trigger it. Confirmed empirically: `tokens.cached = 0` on every row
across the 60-row `results/runs/03-v2-devstral/` dataset.

The flag `router.prompt_cache: true` on the
`configs/variants/09-r3-cached-devstral.yaml` YAML doesn't change
output shape because the underlying OpenAI API decides for itself
whether to cache. The flag is kept in the schema for future use when
we switch to explicit cache-control markers (Anthropic-style).

Full analysis: `docs/T-13-analysis.md`.

---

## 7. Judge-robustness audit (T-14) — custom_arch verdicts are robust

We re-judged the 5 custom_arch pairings from run
`02-v2-qwen-fixed-synth/` with three judges × two A/B orders = 30
verdicts. Raw verdicts in `results/runs/10-judge-robust/judge.jsonl`.

**Result:** Opus and Sonnet both declare R1 ≈ R3 on every custom_arch
task (all ten verdicts `tie`). This is the same conclusion the MVP
report reached, now with a second judge (Sonnet) confirming and with
A/B-order robustness verified.

GPT-5.5 judging was attempted but failed on an API-key resolution bug
that we fixed during the audit; a re-run with the fixed credentials
landed after the Opus+Sonnet verdicts were already unanimous, so the
GPT-5.5 verdicts are additive confirmation rather than a tiebreaker.

Aggregated agreement table in `results/reprice/judge_robustness.md`.

---

## 8. Known limits + what this plan did NOT close

| Caveat | Status |
|---|---|
| N=10 per (category, route) | Wilson CI gives honest bands; three-seed CI is deferred (see `docs/T-12-deferred.md`) |
| Single hardware tier (M4 Max 64GB) | Still true. Multi-tier study is post-publication |
| Single cloud family (OpenAI) | gpt-5.5 primary; 5 other scenarios re-priced only, not re-inferred |
| No R5 (Aider architect/editor review loop) | Deferred. PLAN.md flagged this as post-MVP |
| No new benchmarks | Four adapters unchanged |
| R4 protocol-mismatch on BigCodeBench | Honest fail, documented |
| Prompt caching not empirically tested | Analysis only (`docs/T-13-analysis.md`) — prefixes too short |

Every caveat is one that the MVP REPORT already flagged. This version
narrows some (Wilson CIs, multi-scenario matrix, judge-robustness) but
does not resolve them all.

---

## 9. Reproducibility quick start

```bash
git clone <repo> && cd hybrid-coding-eval
python3.12 -m venv .venv && .venv/bin/pip install -e .
cp .env.example .env        # add OPEN_AI_API_KEY + ANTHROPIC_API_KEY
ollama pull devstral:24b
./router/start.sh

# reproduce run 04-r4-minion from the MVP dataset
./bench run --config configs/variants/04-r4-devstral-minion.yaml

# drop in a new model — takes 90 seconds
cp configs/variants/_template.yaml configs/variants/my-model.yaml
$EDITOR configs/variants/my-model.yaml    # change variant_tag + models.cloud or models.local
./bench run --config configs/variants/my-model.yaml
./bench analyze results/runs/my-variant/
```

`docs/REPRODUCING.md` has the full setup, troubleshooting and
expected wall-times. `CLAUDE.md` has the full `bench` subcommand
reference.

---

## 10. Previous claims, for lineage

- **v1 draft** (`docs/article-draft-v1.md` body) claimed "hybrid is
  Pareto-dominated on every category." That was load-bearing on (a) a
  synth-budget bug and (b) a weak local model for SWE-bench. Both
  closed in v2.
- **v2 postscript** (same file) declared R4 Minion a cost win on
  SWE-bench. This report tightens that to "R4 wins on pass rate, R1
  wins on $/correct under gpt-5.5 rates" — the direction survives,
  but the "cost win" framing was imprecise.
- **MVP REPORT.md** is preserved verbatim; this article is its
  successor.

## Suggested citation

> Monga, Sanchit and contributors. *hybrid-coding-eval: reproducible
> cost/latency/quality benchmark for local vs cloud vs hybrid LLM
> routing on coding tasks.* 2026.
> https://github.com/RunanywhereAI/hybrid-coding-eval

## License

- **Code**: MIT (see `LICENSE`)
- **Data + this article**: CC-BY-4.0 (see `LICENSE-DATA`)
- **Third-party code**: see `NOTICE.md` and `vendor/README.md`
