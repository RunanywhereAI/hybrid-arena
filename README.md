# hybrid-coding-eval

> *A benchmark + harness that answers, with reproducible numbers, the question:*
> ***For my coding task and my hardware — should I run it local, hybrid, or cloud?***

**Status: v3 sweep complete.** 250 graded rows across 5 routes (R1, R2, R3, R4, R5) and 8 task shapes (A HumanEval+, B SWE-bench Verified, C BigCodeBench + custom-arch, D1-D5 real-developer-tasks). M4 Max + devstral:24b local + gpt-5.5 cloud + claude-opus-4-7 judge. Plus a 96-verdict triple-judge robustness audit on D3+D4.

## 👉 Start here

- **[`reports/ARTICLE.md`](./reports/ARTICLE.md) — the canonical article. Read this.**
- [`reports/DECISION_TABLE.md`](./reports/DECISION_TABLE.md) — per-shape × route pass / cost / cloud-fraction grid.
- [`reports/TOKEN_BUDGET.md`](./reports/TOKEN_BUDGET.md) — token-first headline; every cost is derived from stored tokens × pinned pricing.
- [`reports/APPENDIX_TASKS.md`](./reports/APPENDIX_TASKS.md) — every `(task, route, variant)` row verbatim: problem, prompt, output, score, judge reasoning.
- [`reports/APPENDIX_SCENARIOS.md`](./reports/APPENDIX_SCENARIOS.md) — multi-scenario decision matrix + $/correct under every pricing tier.
- [`reports/APPENDIX_ROUTES.md`](./reports/APPENDIX_ROUTES.md) — worked example per R1/R2/R3/R4/R5 with full trace.
- [`results/runs/07-v3-devstral-all-routes/`](./results/runs/07-v3-devstral-all-routes/) — the v3 sweep: 250 rows, run-notes, raw.jsonl, outputs, charts, aggregate.json.
- [`results/runs/11-judge-robust-D/`](./results/runs/11-judge-robust-D/) — 96 triple-judge verdicts; D3+D4 robustness audit.
- [`results/runs/`](./results/runs/) — index of all runs (MVP 01-06 + v3 sweep 07 + robustness audits 10-11).

## What the five routes are

| route | what it does |
|---|---|
| **R1 cloud-only** | one shot to `gpt-5.5` |
| **R2 local-only** | one shot to `devstral:24b` via Ollama |
| **R3 hybrid-architect** | cloud plans → per-step heuristic routing → cloud synth |
| **R4 hybrid-minion** | Stanford Minion-style supervisor/worker Q&A; cloud never re-sees raw context |
| **R5 hybrid-devminion** | Stanford DevMinion architect/editor review loop, up to 3 rounds; cloud architect → local editor → cloud reviewer |

## The headline

Per-shape decision distilled from [`reports/DECISION_TABLE.md`](./reports/DECISION_TABLE.md) (8 shapes × 5 routes, 250 rows, gpt-5.5 cloud / devstral:24b local).

| Shape | Best route | Why |
|---|---|---|
| A — HumanEval+ (10) | **R2** (or R1) | R2 9/10 at $0.000; R1 10/10 at $0.012. Every hybrid pays 3-20× for no quality gain. |
| B — SWE-bench Verified (10) | **R1** | R1 = R3 = R4 = 3/10 (same 3 Django tasks). Hybrid pays 1.3-3.7× for parity. R5 = 0/10. |
| C-bcb — BigCodeBench-Hard (5) | **R1** or **R2** | R1 = R2 = 1/5. Hybrid regresses to 0/5. |
| C-arch — custom-arch prose (5) | **R1** | R1 5/5\* at $0.30; R3 5/5\* at $0.49 (1.6×); R4 4/5\*; R5 1/5\*. |
| D1 — small features (4) | **R2** fall-through to **R1** | R1 = R3 = 2/4; hybrid pays 3-14× per task. R2 = 0/4 — use only if R2 first try works. |
| D2 — GitHub-issue patches (4) | **R1** | Functional scorer deferred; cost / cloud-fraction observable only. |
| D3 — refactor prose (4) | **R1** | R1 = R3 = R4 = 4/4\*. Triple-judge audit (96 verdicts) confirms R1 wins all 8 D3+D4 pairings vs R3/R4 unanimously, zero order-flips. R5 = 0/4\*. |
| D4 — code-review prose (4) | **R1** | R1 4/4\*; R3 / R4 2/4\*; R5 0/4\*. R1 4.7× cheaper than R3 on this shape. |
| D5 — small one-shots (4) | **R1** (or **R2** first try) | R1 = R3 = R4 = R5 = 3/4. R5 wins `d5-log-errors-today` alone — niche evidence. |

`*` = judge-scored shape, pass proxy is `composite ≥ 0.5`.

**Hybrid routes reach quality parity with R1 on most categories but cost 2-5× more per task** because the actual token routing keeps 80%+ of conversation on the cloud (R4 median cloud_fraction is 87%, not the 20-40% the protocol predicted). R5 (DevMinion review-loop) burned the most tokens (1.88 M total, 5.13× R1's per-row cost) and collapsed on every D3 + 3 of 4 D4 prose tasks. The v3 sweep also reversed run 04's "R4 beats R1 on SWE-bench" headline: that Sphinx win did not replicate. Full story in [`reports/ARTICLE.md`](./reports/ARTICLE.md); v3 dataset at [`results/runs/07-v3-devstral-all-routes/raw.jsonl`](./results/runs/07-v3-devstral-all-routes/raw.jsonl); MVP report preserved at [`results/REPORT_v1_mvp.md`](./results/REPORT_v1_mvp.md).

## Repo layout

```
hybrid-coding-eval/
├── README.md                      ← you are here
├── reports/
│   ├── ARTICLE.md                 ← 👉 the canonical v3 article
│   ├── DECISION_TABLE.md          ← per-shape × route grid
│   ├── TOKEN_BUDGET.md            ← token-first cost derivation
│   ├── APPENDIX_TASKS.md          ← every (task, route, variant) row
│   ├── APPENDIX_SCENARIOS.md      ← multi-scenario $/correct
│   └── APPENDIX_ROUTES.md         ← R1..R5 worked examples
├── results/
│   ├── raw.jsonl                  ← MVP merged dataset (180+20 = 200 rows)
│   ├── REPORT_v1_mvp.md           ← MVP report (preserved, frozen)
│   ├── env-manifests/             ← hardware profile per variant
│   └── runs/
│       ├── README.md              ← index of all runs
│       ├── 01-v1-qwen-original/    ← v1 sweep (superseded)
│       ├── 02-v2-qwen-fixed-synth/ ← synth-budget fix + Opus judge
│       ├── 03-v2-devstral/         ← local-model swap
│       ├── 04-r4-minion/           ← R4 Minion on SWE-bench
│       ├── 05-r4-catA/             ← R4 on HumanEval+
│       ├── 06-r4-catC/             ← R4 on BigCodeBench + custom-arch
│       ├── 07-v3-devstral-all-routes/ ← the v3 sweep (250 rows, R1..R5)
│       ├── 10-judge-robust/        ← triple-judge audit on custom-arch (30 verdicts)
│       └── 11-judge-robust-D/      ← triple-judge audit on D3+D4 (96 verdicts)
├── docs/
│   ├── PLAN.md                    ← original multi-phase plan
│   ├── METHODOLOGY.md             ← how the eval works, biases acknowledged
│   ├── REPRODUCING.md             ← copy-paste instructions for a fresh machine
│   ├── ARCHITECTURE.md            ← code layout + data flow
│   ├── ROUTING_STRATEGIES.md      ← deep-dive on each route
│   ├── PRIOR_ART.md               ← May 2026 research synthesis
│   ├── OSS_REVIEW.md              ← pre-public audit record
│   ├── RUNANYWHERE_INTEGRATION.md ← future-work design doc
│   ├── article-draft-v1.md        ← long-form article (v1 narrative + v2 postscript)
│   └── history/                   ← pre-MVP archival notes
├── router/                        ← hybrid proxy (Node.js, zero deps, port 8787)
├── runners/                       ← R1/R2/R3/R4/R5 Python runners
├── scorers/                       ← pytest + SWE-bench harness + LLM-judge
├── benchmark/                     ← 5 task adapters (HumanEval+, SWE-bench, BigCodeBench, custom-arch, real-dev D1-D5)
├── analysis/                      ← aggregate / ARQGC / decision-matrix / charts
├── lib/                           ← pricing tables, sandbox, metrics schema
├── bin/                           ← CLIs (run-experiment, rescore, rejudge, env-detect)
└── EXTERNAL/
    ├── minions/                   ← Stanford Minion library (MIT, vendored for R4)
    └── lm-eval-harness-judge/     ← MT-Bench judge reference (Apache 2.0)
```

## Quick start

```bash
git clone https://github.com/RunanywhereAI/hybrid-coding-eval
cd hybrid-coding-eval
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

cp .env.example .env                         # add OPEN_AI_API_KEY (+ ANTHROPIC_API_KEY if you want the Opus judge)
ollama pull devstral:24b                     # or qwen3.6:27b-coding-mxfp8

./router/start.sh                            # launches the hybrid router proxy on :8787

# smoke sweep (1 task × 3 routes ≈ 10 min)
./bench run --config configs/variants/04-r4-devstral-minion.yaml --smoke

# full sweep — 30 tasks × 4 routes ≈ 4-5h
./bench run --config configs/variants/04-r4-devstral-minion.yaml
./bench rescore  results/runs/04-r4-minion/       # post-sweep SWE-bench rescore
./bench rejudge  results/runs/04-r4-minion/       # post-sweep Opus re-judge (ANTHROPIC_API_KEY)
./bench analyze  results/runs/04-r4-minion/
```

### Drop in a new model

```bash
cp configs/variants/_template.yaml configs/variants/my-model.yaml
# edit variant_tag + models.cloud or models.local, then:
./bench run --config configs/variants/my-model.yaml
./bench analyze results/runs/my-variant/
```

Full instructions in [`docs/REPRODUCING.md`](./docs/REPRODUCING.md). Wall ~5h on M4 Max, ~$15 API spend.

## Where to read next

1. **[`reports/ARTICLE.md`](./reports/ARTICLE.md)** — the canonical v3 article. Read this first.
2. [`reports/DECISION_TABLE.md`](./reports/DECISION_TABLE.md) — per-shape × route grid (pass / cost / cloud-fraction).
3. [`reports/TOKEN_BUDGET.md`](./reports/TOKEN_BUDGET.md) — token-first headline; every cost is derived from tokens at read time.
4. [`reports/APPENDIX_TASKS.md`](./reports/APPENDIX_TASKS.md) — forensic record: every task × route × variant with its problem, prompt, output, score.
5. [`reports/APPENDIX_SCENARIOS.md`](./reports/APPENDIX_SCENARIOS.md) — multi-scenario decision matrix.
6. [`reports/APPENDIX_ROUTES.md`](./reports/APPENDIX_ROUTES.md) — worked examples per R1/R2/R3/R4/R5.
7. [`results/runs/07-v3-devstral-all-routes/run-notes.md`](./results/runs/07-v3-devstral-all-routes/run-notes.md) — v3 sweep, per-run findings.
8. [`results/runs/11-judge-robust-D/run-notes.md`](./results/runs/11-judge-robust-D/run-notes.md) — triple-judge robustness audit (96 verdicts).
9. [`examples/drop-in-a-new-model.md`](./examples/drop-in-a-new-model.md) — 5-step walkthrough for benchmarking a new model.
10. [`results/REPORT_v1_mvp.md`](./results/REPORT_v1_mvp.md) — the MVP report, preserved verbatim.
11. [`results/runs/README.md`](./results/runs/README.md) — index of the experimental runs.
12. [`docs/METHODOLOGY.md`](./docs/METHODOLOGY.md) — how the eval works, biases acknowledged.
13. [`docs/REPRODUCING.md`](./docs/REPRODUCING.md) — copy-paste reproduction on a fresh machine.
14. [`docs/ROUTING_STRATEGIES.md`](./docs/ROUTING_STRATEGIES.md) — deep-dive on each route.
15. [`docs/PRIOR_ART.md`](./docs/PRIOR_ART.md) — research synthesis.
16. [`docs/article-draft-v1.md`](./docs/article-draft-v1.md) — v1 narrative (superseded).
17. [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — code layout + data flow.
18. [`docs/PLAN.md`](./docs/PLAN.md), [`docs/FINAL_REPORT_PLAN.md`](./docs/FINAL_REPORT_PLAN.md), `docs/T-12-deferred.md`, `docs/T-13-analysis.md`, `docs/audits/T-21-publish-readiness.md` — planning artefacts.

## License and attribution

- **Code** (harness, router, runners, scorers, analysis, viz): MIT — see [`LICENSE`](./LICENSE).
- **Results, metrics, figures, article**: CC-BY-4.0 — see [`LICENSE-DATA`](./LICENSE-DATA).
- **Third-party code and research we build on**: see [`NOTICE.md`](./NOTICE.md) and [`EXTERNAL/README.md`](./EXTERNAL/README.md).

Suggested citation (if you use our numbers):

> Monga, Sanchit and contributors. *hybrid-coding-eval: reproducible cost/latency/quality benchmark for local vs cloud vs hybrid LLM routing on coding tasks.* 2026. https://github.com/RunanywhereAI/hybrid-coding-eval
