# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **reproducible benchmark harness** (not a product) that compares local vs cloud vs hybrid LLM routing on coding tasks. One developer laptop, one cloud model, one local model, four routes, 30 tasks × 4 variants = 180 historical rows. Canonical article lives at `reports/ARTICLE.md` (written at T-18); the preserved MVP report is `results/REPORT.md`; the canonical dataset is `results/raw.jsonl`. Experimental runs are **preserved as-is** under `results/runs/NN-*/` — never edit rows after a sweep; re-score or re-judge produces new per-run directories.

**Status.** Mono-repo reorg in progress on branch `mono-repo-reorg`. Pre-reorg `main` is the MVP ship-point. See `docs/FINAL_REPORT_PLAN.md` for the 22-task plan. Anything under `docs/article-draft-v1.md` or `docs/PLAN.md` is archival narrative.

## Drop in a new model in 90 seconds

```bash
cp configs/variants/_template.yaml configs/variants/my-model.yaml
# edit two lines (variant_tag + models.cloud or models.local), then:
./bench run --config configs/variants/my-model.yaml
./bench analyze results/runs/my-variant/
./bench report article
```

Need to see what the config resolves to? `./bench show-config --config configs/variants/my-model.yaml` prints the merged config + SHA256. The same `./bench run … --dry-run` prints the plan without executing.

## Common commands

Python env is pinned at 3.11/3.12. Always use `.venv/bin/python` or `.venv/bin/pytest` (the repo installs editable via `pip install -e .`).

```bash
# one-time env setup
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -e .

# fast tests (SWE-bench Docker tests are marked slow)
.venv/bin/pytest tests/ -q -m 'not slow'

# one test file / one test
.venv/bin/pytest tests/test_r3_hybrid_architect.py -q
.venv/bin/pytest tests/test_aggregate.py::test_name -q

# ruff (repo-wide)
.venv/bin/ruff check src/ tests/

# start the router proxy (port 8787) — REQUIRED before R1/R3/R4 runs
(cd router && ./start.sh)
curl -s http://127.0.0.1:8787/healthz | jq .

# router's own test sweep (strategies × prompts matrix)
cd router && npm test                                 # writes tests/RESULTS.md

# the bench dispatcher — new mono-repo surface
./bench run --config configs/variants/04-r4-devstral-minion.yaml   # full variant run
./bench run --config configs/variants/_template.yaml --dry-run     # plan only
./bench run --config configs/variants/my.yaml --set models.cloud=gpt-5 --smoke
./bench show-config --config configs/variants/04-r4-devstral-minion.yaml
./bench env-detect --out results/my-run/env-manifest.json
./bench rescore  results/runs/03-v2-devstral/        # post-sweep SWE-bench rescore
./bench rejudge  results/runs/02-v2-qwen-fixed-synth/  # post-sweep Opus re-judge
./bench analyze  results/runs/03-v2-devstral/        # aggregate + ARQGC + charts
./bench schema --out configs/schema.json             # regen JSON Schema
./bench report article                               # after T-18 lands
```

The plain `bin/` scripts (`bin/run-experiment.py`, `bin/env-detect.py`, `bin/rescore-swebench.py`, …) are thin shims forwarding to `hybrid_coding_eval.cli.*`. Keep working for legacy shell invocations; prefer `./bench …` going forward.

## Architecture — the big picture

Four routes (R1–R4), one shared pricing + scoring + analysis pipeline, two languages glued through a local HTTP proxy.

### Directory layout (post-mono-repo-reorg)

```text
hybrid-coding-eval/
├── bench                          # top-level shell wrapper → bench.py
├── configs/
│   ├── pricing/pricing_tables.json  # shared source of truth (Python + Node)
│   ├── router/corpus.json          # embedding-kNN strategy training data
│   ├── schema.json                  # auto-generated from BenchConfig
│   └── variants/*.yaml              # one per sweep — the "drop in a new model" UX
├── src/hybrid_coding_eval/
│   ├── core/                        # metrics, pricing, results, experiment, sandbox, config/
│   ├── runners/                     # R1..R4 + _shared
│   ├── scorers/                     # functional_python, llm_judge, swebench
│   ├── benchmarks/                  # humaneval_plus, swebench_verified, bigcodebench_hard, custom_arch
│   ├── analysis/                    # aggregate, arqgc, cost_scenarios, decision_matrix
│   ├── viz/                         # pareto + heatmap
│   └── cli/                         # bench, run, env_detect, rescore, rejudge, analyze, report
├── router/                          # Node proxy (zero-deps)
│   ├── server.mjs, strategies.mjs, pricing.mjs
│   └── pipelines/architect/         # core.mjs + runner.mjs (Node shim R3 subprocesses)
├── vendor/                          # vendored third-party (Stanford minions, lm-eval-harness-judge)
├── bin/                             # shim scripts forwarding to cli/*
├── tests/                           # pytest suite
├── results/                         # read-only — preserved runs + canonical dataset
│   ├── raw.jsonl                    # 180 rows, bit-identical forever
│   ├── REPORT.md                    # MVP report (superseded by reports/ARTICLE.md at T-18)
│   └── runs/NN-*/                   # one dir per sweep; never edit rows in place
├── reports/                         # publish surface (ARTICLE + appendices; written at T-18/19/20)
├── docs/                            # archival + reference (ARCHITECTURE, METHODOLOGY, …)
└── examples/                        # POC 3-task comparisons (pre-MVP)
```

### Data flow for one experiment row

```text
./bench run --config X.yaml
  → hybrid_coding_eval.cli.bench._cmd_run
  → hybrid_coding_eval.cli.run.main   (dispatches via argv for backward compat)
  → hybrid_coding_eval.core.experiment.build_task_plan()   # (category, source, task, route)
  → hybrid_coding_eval.core.experiment.run_pair()           # runner per route
       ├── runners/r1_cloud_only.py      # → router/always-cloud → cloud
       ├── runners/r2_local_only.py      # → router/always-local → Ollama
       ├── runners/r3_hybrid_architect.py → subprocess router/pipelines/architect/runner.mjs
       │                                    → router/pipelines/architect/core.mjs
       │                                    → router proxy (planner/executor/synth)
       └── runners/r4_minion.py          # vendor/minions (Stanford protocol)
  → scorers/*                            # functional_python (Docker sandbox), swebench, llm_judge
  → core/results.append_row()            # one JSON line per (task, route) to <out>/raw.jsonl
```

Rows are flushed after each (task, route) so sweeps are crash-resumable via `--resume` (checks `(task_id, route)` pairs already in `raw.jsonl`).

### The router proxy (`router/`, Node zero-deps)

OpenAI-compatible HTTP proxy on `:8787` that every R1/R3/R4 call goes through. The `model` field of the request selects a routing strategy (`router/always-local`, `router/heuristic`, `router/cascade`, …; seven total in `router/strategies.mjs`). Append `!local`/`!cloud` to force a backend. Decisions are appended to `router/logs/decisions.jsonl` — historical file tracked, new per-run churn gitignored.

Config is env-driven (`LOCAL_BASE`, `LOCAL_MODEL`, `CLOUD_MODEL`, `CLOUD_API_KEY` resolving from `OPENAI_API_KEY` or `OPEN_AI_API_KEY`). `./router/start.sh` loads `../.env`. Binds `127.0.0.1` only; no auth — don't expose.

### R3 two-language boundary

R3 is the one place Python and Node cross: `runners/r3_hybrid_architect.py` subprocesses `router/pipelines/architect/runner.mjs` and parses its JSON stdout. The JS side returns `totals.hybridCostUsd` for cross-check only — **the Python aggregator re-derives cost from tokens** via `core/pricing.py` using `configs/pricing/pricing_tables.json` (2026-04-27, sourced from models.dev). **Cost is never persisted** in `raw.jsonl`; only tokens-per-backend. Same runs are re-priceable under any scenario by swapping `pricing.primary`.

### Metrics schema (`core/metrics.py`)

One `ResultRow` per (task, route, seed). Tokens split into `local_*` / `cloud_*` (R2 must always have `cloud_*` = 0; non-zero = routing bug). New optional metadata fields from T-08: `variant`, `cloud_model_id`, `local_model_id`, `judge_model_id`, `router_classifier_model_id`, `router_strategy`, `seed`, `config_sha`. All Optional for backward-compat.

### Scorers

- `scorers/functional_python.py` runs generated code in a `python:3.12-slim` Docker sandbox (image `hybrid-eval-python:latest`, built from `scorers/Dockerfile.functional_python`) with `--network none`, mem caps, wall-clock timeout.
- `scorers/swebench.py` shells out to the SWE-bench harness (x86_64 images, ~10 min/task under Rosetta on Apple Silicon).
- `scorers/llm_judge.py` uses Anthropic Opus as the judge for Category C. Judge model is configurable per call; default `claude-opus-4-7`. Skips cleanly if `ANTHROPIC_API_KEY` unset.

### Benchmarks

Four adapters under `src/hybrid_coding_eval/benchmarks/`, each exposing `load_tasks(n=...)` → Task dataclasses with stable `id`. Pinned `tasks.jsonl` committed; `datasets`/`evalplus` only needed to refresh.

### Analysis

`analysis.all` runs: `aggregate` (means/medians per category × route) → `arqgc` (bounded area-under-quality-cost curve, capped at p90 of R1 cost per category) → `decision_matrix` → `cost_scenarios` (re-price under alternate scenarios) → charts.

## Conventions and gotchas

- **Always call Python via `.venv/bin/python` or `.venv/bin/pytest`**, not bare `python`. The repo installs editable.
- **The router must be running** before any R1/R3/R4 runner or integration test. Tests call `runners._shared.proxy_health()` and `pytest.skip` cleanly when it's down.
- **`tests/test_*` marked `slow`** invoke the SWE-bench Docker harness (minutes per test). Skip with `-m 'not slow'`.
- **Preserved runs are read-only.** `results/raw.jsonl` and `results/runs/01-*/` through `04-*/` never change bytes. New sweeps go to `05-*/` and up.
- **Cost is derived, not stored.** Any `cost_usd_*` field in `raw.jsonl` is a bug. Cost is computed on read via `core/pricing.py`.
- **Env keys:** `OPENAI_API_KEY` / `OPEN_AI_API_KEY` accepted. `ANTHROPIC_API_KEY` required for the Opus judge path.
- **Task adapters vs categories:** A=HumanEval+, B=SWE-bench Verified, C=BigCodeBench-Hard + custom_arch. See `core.experiment.CATEGORY_SOURCES`.
- **`vendor/`** is vendored third-party source (Stanford `minions` for R4, `lm-eval-harness-judge` reference). Read-only. See `NOTICE.md` for licenses.
- **YAML configs under `configs/variants/` are the canonical way to define a sweep.** Override fields on the CLI with `--set key.path=value` rather than editing the YAML if you're doing a one-shot.

## Where to read next

- `reports/ARTICLE.md` — **the canonical article** once T-18 lands (check with `ls reports/`).
- `results/REPORT.md` — MVP report (frozen; will be renamed `REPORT_v1_mvp.md` at T-18).
- `docs/FINAL_REPORT_PLAN.md` — the active 22-task plan driving this branch.
- `docs/ARCHITECTURE.md` — full code layout + data flow (long).
- `docs/METHODOLOGY.md` — scoring rubrics, contamination analysis, what the eval does and doesn't claim.
- `docs/REPRODUCING.md` — copy-paste reproduction on a fresh machine.
- `docs/ROUTING_STRATEGIES.md` — deep dive on the seven router strategies.
