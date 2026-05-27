# AGENTS.md

A single canonical guide for any AI coding agent (Claude Code, Aider, Cursor, Codex, etc.) working in this repository. Read this first.

## What this repo is

A **reproducible benchmark harness** that measures whether a coding task should run on local hardware, cloud, or via hybrid routing. It is **not a product**. It is a one-developer-laptop research artefact that publishes per-`(task-class, agent, strategy)` bootstrap-CI datasets comparing five agentic coding agents (**aider · opencode · mini-swe-agent · claude-code · cline**) across three task classes (**puzzles** = Exercism Python · **refactors** = real-developer D-tasks · **real-prs** = SWE-bench Verified) under six pricing scenarios.

**Top-level canonical surfaces:**

- `README.md` — OSS landing page (4-command quickstart)
- `docs/REPRODUCING.md` — copy-paste reproduction with a "how to read the results" cell→headline map
- `docs/BENCHMARK_NEW_MODEL.md` — add-a-new-local-model walkthrough
- `docs/release-notes/v1.4.0.md` + `docs/release-notes/v1.4.1.md` — tracked-in-git canonical findings
- `configs/v1.4-canonical-{gemma4,qwen3-coder,qwen3.6}.yaml` — the 3-model canonical sweep configs
- `CHANGELOG.md` — release history (Keep a Changelog format)
- `CONTRIBUTING.md` — how to add a model, task, or routing strategy
- `LICENSE` (MIT, code) + `LICENSE-DATA` (CC-BY-4.0, data) + `LICENSE.md` + `NOTICE.md`

> Maintainer-only article + iteration notes live under the gitignored `personal/` directory. The empirical record (tracked `results/runs/{01..04, 07, 11}/` immutable runs + `docs/release-notes/`) stays tracked. New per-tag datasets ship as GitHub release tarballs (e.g. `results-v1.4.1.tar.gz`).

**Status:** **v1.4.1** — 3-model agentic leaderboard. The agent-only surface (5 routes) is the sole sweep target. `bench sweep` auto-spawns the router proxy from `models.local`, so the canonical reproducer is four copy-paste commands. v1.4 combined dataset: **1,644 rows** across 3 local models × 3-5 agents × 4-8 strategies × 13 tasks × 3 seeds.

### v1.4.1 headline (the marquee cells)

| Cell | Pass-rate | Cloud-fraction |
|---|---|---|
| **cline + qwen3.6:35b + cascade + refactors** | **24/24 = 100% [100, 100]** | ~5–10% |
| aider + gemma4:31b + heuristic + refactors (v1.4 replicated) | 23/24 = 96% [88, 100] | 48% |
| cline + (gemma4 OR qwen3.6) + always-local + puzzles | 15/15 = 100% [100, 100] | 0% |
| opencode + gemma4:31b + heuristic + refactors (v1.1.x→v1.4 resurrection) | 17/24 = 71% | — |
| cline + qwen3-coder:30b + heuristic + refactors | 22/24 = 92% | ~7% |

**Top-line claims:** (i) cline + qwen3.6 + cascade is the new cleanest cell. (ii) the v1.3/v1.4 aider+gemma4 marquee replicates exactly under refreshed code. (iii) 30B local-only solves Exercism Python with cline. (iv) opencode resurrects on gemma4 but is gemma4-specific (qwen variants get 21–33%). (v) aider is also model-sensitive (96/50/33% on gemma4/qwen3.6/qwen3-coder).

## Drop in a new model

```bash
ollama pull <new-model>
./bench setup                                                          # first run only — Docker image, aux models, aider, cline
./bench sweep --config configs/v1.4-canonical-gemma4.yaml \
  --set models.local=<new-model> \
  --set out_dir=results/runs/v1.4-<new-model> \
  --strategies always-cloud,always-local,heuristic,cascade --seeds 42 --smoke
./bench analyze results/runs/v1.4-<new-model>/
```

`./bench show-config --config <yaml>` prints the merged config + SHA256.
`./bench sweep … --dry-run` prints each pass without running.

## Common commands

Python env is pinned at 3.11/3.12. Always use `.venv/bin/python` or `.venv/bin/pytest` — the repo installs editable via `pip install -e ".[dev]"`.

```bash
# one-time env setup
python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# fast tests (118 collected; SWE-bench Docker tests marked `slow`)
.venv/bin/pytest tests/ -q -m 'not slow'

# one test file / one test
.venv/bin/pytest tests/test_orchestrator.py -q
.venv/bin/pytest tests/test_aggregate.py::test_name -q

# ruff (repo-wide)
.venv/bin/ruff check src/ tests/

# router proxy — auto-spawned by `bench sweep`. Manual start (rarely needed):
(cd router && ./start.sh)
curl -s http://127.0.0.1:8787/healthz | jq .

# router's own test sweep (strategies × prompts matrix)
cd router && npm test                                                  # writes tests/RESULTS.md

# foreground sweep
./bench sweep --config configs/v1.4-canonical-gemma4.yaml \
  --strategies always-cloud,always-local,heuristic,cascade --seeds 42,7,13
./bench sweep --config configs/v1.4-canonical-gemma4.yaml --strategies heuristic --seeds 42 --dry-run

# inspection / one-shot helpers
./bench show-config --config configs/v1.4-canonical-gemma4.yaml
./bench env-detect --out results/my-run/env-manifest.json
./bench analyze     results/runs/v1.4-canonical-gemma4/                # aggregate + bootstrap CIs + charts
./bench token-budget results/runs/v1.4-canonical-gemma4/               # 6-scenario token + cost matrix
./bench schema --out configs/schema.json                               # regen JSON Schema
./bench setup                                                          # one-shot first-time setup
```

### v1.4 sweep lifecycle (background, pausable, resumable)

Long sweeps (10+ hours) are managed via a detached state file at `/tmp/hcev-sweep.json`:

```bash
./bench start  --config configs/v1.4-canonical-qwen3.6.yaml \
  --strategies always-cloud,always-local,heuristic,cascade --seeds 42,7,13
./bench status            # PID, config, log path, current row count
./bench pause             # kill orchestrator + agents + router; Ollama stays loaded
./bench resume            # relaunch with --resume; skips already-completed (task, agent) rows
./bench stop              # like pause + kill Ollama (frees ~19 GB). State file retained.
./bench stop --clear-state         # ...also wipe /tmp/hcev-sweep.json
./bench stop --keep-ollama-app     # only kill model runners; keep Ollama.app
```

The five lifecycle commands wrap `bench sweep` argv. State persists across reboots until you `--clear-state`.

> **Broken commands flagged:** `./bench rescore` and `./bench rejudge` are still registered as subparsers in `cli/bench.py` but their implementation modules (`cli/rescore.py`, `cli/rejudge.py`) were deleted in the v1.4 cleanup. Invoking either raises `ImportError`. Do not use them — analysis is now done through `./bench analyze` only.

## Folder-by-folder inventory

### Top level

| Path | What it is |
| --- | --- |
| `README.md` | OSS landing page |
| `AGENTS.md` | **this file** — canonical agent guide |
| `CHANGELOG.md` | Keep-a-Changelog release history |
| `CONTRIBUTING.md` | Dev setup, model/benchmark contribution flow, PR style |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1 |
| `LICENSE` | MIT (covers code under `src/`, `router/`, `tests/`, `configs/`) |
| `LICENSE-DATA` | CC-BY-4.0 (covers data under `results/`, charts, docs prose) |
| `LICENSE.md` | File-type breakdown of MIT vs CC-BY-4.0 |
| `NOTICE.md` | Third-party attribution |
| `bench` | Shell wrapper that execs `python -m hybrid_coding_eval.cli.bench` |
| `pyproject.toml` | Python package config — version `1.4.1`, deps, pytest, ruff. Declares `bench` console script |
| `requirements.txt` | Pip dependency pins (kept in sync with `[project.dependencies]`) |
| `examples/` | `drop-in-a-new-model.md` + Node `run-comparison.mjs` helper |

### `configs/` — sweep configs, pricing, router corpus, JSON schema

```
configs/
├── v1.4-canonical-gemma4.yaml       # canonical v1.4.0 baseline (gemma4:31b)
├── v1.4-canonical-qwen3-coder.yaml  # v1.4.1 sweep (qwen3-coder:30b MoE)
├── v1.4-canonical-qwen3.6.yaml      # v1.4.1 sweep (qwen3.6:35b dense)
├── v1.4-opencode-fairness.yaml      # opencode-only fairness slice
├── v1.4-strategy-sweep.yaml         # all 8 strategies on aider/gemma4 for explainer
├── v1.4-real-prs.yaml               # SWE-bench Verified replay (real-prs class)
├── v1.4-smoke.yaml                  # 1-task-per-class smoke check
├── pricing/pricing_tables.json      # 6 pricing scenarios, SHA256-pinned
├── router/corpus.json               # 50-example hand-labelled corpus for embedding-kNN
└── schema.json                      # auto-generated JSON Schema for BenchConfig
```

YAML configs are the canonical sweep-definition surface. The schema at `configs/schema.json` is auto-generated from `src/hybrid_coding_eval/core/config/schema.py` — never hand-edit. Override fields on the CLI with `--set key.path=value` rather than editing the YAML for one-shot runs. The legacy `configs/variants/` directory and 32 pre-v1.4 YAMLs were deleted in the v1.4 cleanup.

### `src/hybrid_coding_eval/` — the Python package

```
src/hybrid_coding_eval/
├── cli/                          # ./bench dispatcher and subcommands
│   ├── bench.py                  # top-level CLI — all subparsers + lifecycle (start/pause/resume/stop/status)
│   ├── run.py                    # ./bench run — single-pass sweep orchestrator
│   └── env_detect.py             # ./bench env-detect — captures hardware + software snapshot
│
├── core/                         # shared dispatcher + I/O + config
│   ├── experiment.py             # build_task_plan, run_pair — the dispatcher loop (internal R6..R10 ids)
│   ├── metrics.py                # ResultRow + TokenUsage + Latency + Quality + Routing dataclasses
│   ├── pricing.py                # token → cost derivation against pricing_tables.json
│   ├── results.py                # append_row + pair_already_done (raw.jsonl I/O)
│   ├── sandbox.py                # Docker sandbox helper for functional scorer
│   ├── paths.py                  # repo-root resolver
│   └── config/                   # YAML config schema + loader + variable resolver
│       ├── schema.py             # Pydantic BenchConfig model (source of truth for configs/schema.json)
│       ├── loader.py             # YAML → BenchConfig with env-var ${ENV:VAR} expansion
│       └── resolve.py            # config flag overrides (--set key.path=value)
│
├── agents/                       # one module per agentic route (v1.4 dropped the Rn prefix)
│   ├── aider.py                  # aider — architect/editor protocol (R7 internally)
│   ├── opencode.py               # opencode — free-form tool-use ReAct (R8)
│   ├── mini_swe.py               # mini-swe-agent — bash-only ReAct (R6)
│   ├── claude_code.py            # Anthropic claude-code CLI (R9)
│   ├── cline.py                  # cline VSCode agent, headless (R10)
│   └── attribution.py            # correlation-id token attribution for the proxy
│
├── scorers/                      # one scorer per quality dimension
│   ├── functional_python.py      # extracts code, runs pytest in a Docker sandbox
│   ├── swebench.py               # shells out to upstream `swebench.harness.run_evaluation`
│   └── Dockerfile.functional_python  # python:3.12-slim + pytest sandbox image
│
├── tasks/                        # task-source adapters (was `benchmarks/` pre-v1.4)
│   ├── puzzles/                  # Exercism Python (Aider polyglot benchmark, MIT)
│   ├── refactors/                # real-developer D-tasks
│   │   ├── tasks-d1.jsonl, tasks-d2.jsonl, tasks-d3-d4.jsonl, tasks-d5.jsonl
│   │   ├── scorers.py            # per-task scorer dispatcher
│   │   └── fixtures/             # per-task fixture dirs (d1-*, d5-*)
│   └── real_prs/                 # SWE-bench Verified replay
│       ├── adapter.py, tasks.jsonl, verify_harness.py
│
├── analysis/                     # post-sweep number-crunching
│   ├── all.py                    # entry-point; runs everything below
│   ├── aggregate.py              # per-(task_class, agent, strategy) means/medians/sums
│   ├── bootstrap.py              # 95% percentile CIs per cell
│   ├── arqgc.py                  # ARQGC summary table
│   ├── decision_matrix.py        # task_class × agent → recommendation
│   ├── decision_matrix_v2.py     # v1.4 decision-matrix refresh
│   ├── cost_scenarios.py         # re-price under 6 scenarios
│   ├── token_budget.py           # ./bench token-budget — token-first matrix
│   ├── token_share.py            # cloud_fraction analysis
│   └── reprice.py                # standalone re-pricing helper
│
└── viz/                          # chart generators
    ├── cost_quality_pareto.py    # Pareto scatter (cost vs quality)
    └── decision_heatmap.py       # task_class × agent quality/cost heatmaps
```

> **v1.4 renames:** `runners/` → `agents/`, `benchmarks/` → `tasks/`, all `Rn_<name>.py` → `<name>.py`. The orchestrator (`core/experiment.py`) still uses internal `R6..R10` route ids — the user-facing surface in `BenchConfig.benchmark.agents` accepts the friendly names (`aider`, `opencode`, `mini-swe-agent`, `claude-code`, `cline`).

> **v1.4 deletions:** `cli/judge.py`, `cli/rescore.py`, `cli/rejudge.py`, `cli/report.py`, `cli/analyze.py` (folded into bench dispatcher + analysis modules), and `scorers/llm_judge.py` are all gone. Legacy R1–R5 routes deleted entirely.

### `router/` — zero-deps Node hybrid proxy

OpenAI-compatible HTTP proxy on `:8787`. **Auto-spawned by `bench sweep`** in v1.4 — manual start is rarely needed. The `model` field of each request selects a routing strategy (`router/always-local`, `router/heuristic`, `router/cascade`, etc.; 8 total). Append `!local`/`!cloud` to force a backend.

```
router/
├── server.mjs                    # the HTTP server; entry point
├── strategies.mjs                # 8 routing strategies (alwaysLocal/alwaysCloud/rules/heuristic/
│                                 #   llmClassifier/embeddingKnn/cascade/phaseAware)
├── pricing.mjs                   # shared pricing table reader (in sync with configs/pricing)
├── start.sh                      # manual starter — loads ../.env, binds 127.0.0.1
├── package.json                  # minimal — declares "node-test" runner only
├── agentic/architect.mjs         # architect-call helper (Aider/opencode driver pattern)
├── pipelines/architect/          # historical R3 planner/executor/synth pipeline (legacy)
├── tests/                        # router's own test sweep (prompts × strategies)
└── logs/decisions.jsonl          # historical routing decisions (tracked through .gitignore exception)
```

Config is env-driven. Required: `LOCAL_BASE`, `LOCAL_MODEL`, `CLOUD_MODEL`, `CLOUD_API_KEY` (resolves from `OPENAI_API_KEY` or `OPEN_AI_API_KEY`). v1.4.1 added three local-call guards in `fetchLocalOllamaAsOpenAI()`:

| Env var | Default | What it does |
| --- | --- | --- |
| `ROUTER_LOCAL_NUM_PREDICT_CAP` | `4096` | Caps Ollama `num_predict` per local call. `-1` disables. |
| `ROUTER_LOCAL_REQUEST_TIMEOUT_MS` | `180000` | 3-min hard wall-clock timeout per local request via `AbortSignal.timeout`. |
| `ROUTER_LOCAL_REPEAT_PENALTY` | `1.1` | Overrides weak model defaults (e.g. qwen3-coder ships with `1.05`). |

These three guards were added in commit `c7392db` after qwen3-coder's weak `repeat_penalty=1.05` + unbounded `num_predict` (cline doesn't set `max_tokens`) caused a 34 MB / 2.6h runaway repetition that crashed Ollama. Full RCA: `personal/iterations/v1.4.1/qwen3-coder-timeout-rca.md` (gitignored; also in the v1.4.1 release tarball). Two earlier knobs also exist: `ROUTER_LOCAL_TOOL_USE_NUDGE` and `ROUTER_LOCAL_POST_TOOL_REMINDER`.

Binds 127.0.0.1 only; no auth — don't expose.

### `tests/` — pytest suite

**118 fast tests collected** (run `.venv/bin/pytest --collect-only -q -m 'not slow'` to recount). SWE-bench Docker tests are marked `slow`.

```
tests/
├── agents/test_{claude_code,cline,mini_swe}.py     # per-agent unit tests
├── analysis/test_token_budget.py
├── scorers/test_real_dev_scorers.py
├── tasks/test_refactors_scaffold.py
├── test_aggregate.py, test_arqgc.py, test_bootstrap.py
├── test_config.py, test_env_detect.py
├── test_metrics_new_fields.py
├── test_orchestrator.py, test_results.py
├── test_pricing_parity.py, test_pricing_path_parity.py
├── test_sandbox.py
└── test_viz.py
```

Subprocess-based tests `pytest.skip` cleanly if the router proxy is down. The legacy `test_humaneval_plus.py` / `test_bigcodebench_hard.py` / `test_custom_arch.py` / `test_llm_judge.py` were deleted in v1.4.

### `vendor/` — third-party (read-only)

```
vendor/
├── README.md                     # explains what's vendored
└── opencode/                     # opencode fork for the opencode agent (cloned via BENCH_SETUP_OPENCODE=1)
```

`vendor/minions/` and `vendor/lm-eval-harness-judge/` were deleted in v1.4. Treat `vendor/` as immutable — patch our wrapper in `agents/`, not the vendored source.

### `results/` — canonical research data (CC-BY-4.0)

```
results/
├── raw.jsonl                     # MVP merged dataset (180 rows, bit-identical forever)
├── REPORT_v1_mvp.md              # MVP report (frozen)
├── env-manifests/                # 01–04 hardware snapshots
└── runs/                         # one dir per preserved sweep
    ├── README.md                 # run-by-run index
    ├── 01-v1-qwen-original/      # MVP v1 sweep
    ├── 02-v2-qwen-fixed-synth/   # MVP v2 (Opus judge)
    ├── 03-v2-devstral/           # MVP v2 with devstral local
    ├── 04-r4-minion/             # MVP R4 Minion sweep (preserved data)
    ├── 07-v3-devstral-all-routes/ # v3 canonical 250-row sweep (legacy R1–R5)
    └── 11-judge-robust-D/        # 96-verdict triple-judge audit on D3+D4
```

**`results/runs/` is gitignored going forward.** v1.4+ per-tag datasets are GitHub release tarballs (`results-v1.4.K.tar.gz`). Pre-existing tracked runs (01–04, 07, 11) are immutable. Local working dirs (e.g. `v1.4-canonical-*`, `p6-classifier-*`, `p7-cascade-*`) live under `results/runs/` but are gitignored.

### `docs/` — reference documentation (CC-BY-4.0)

```
docs/
├── REPRODUCING.md                # v1.4 reproducer + how-to-read-results cell→headline map
├── BENCHMARK_NEW_MODEL.md        # add-a-new-local-model walkthrough
├── METHODOLOGY.md                # scoring rubrics + biases + what we do/don't claim
├── ARCHITECTURE.md               # long-form code layout + data flow
├── ROUTING_STRATEGIES.md         # deep dive on the 8 router strategies
├── AGENTIC_ROUTES.md             # 5-agent design + correlation-id attribution
├── HYBRID_ROUTER_DESIGN.md       # router architecture deep-dive
├── PRIOR_ART.md                  # 2026 research synthesis
├── audits/T-22-v3-publish-readiness.md   # historical pre-public audit
└── release-notes/                # tracked-in-git release notes
    ├── v1.4.0.md                 # 708-row gemma4 canonical
    └── v1.4.1.md                 # 936 new rows (qwen3-coder + qwen3.6) — 1,644 row leaderboard
```

ARCHITECTURE.md is the longest doc — read it if you need to understand the code in depth. METHODOLOGY.md is the doc to read before interpreting any number in `results/runs/`.

## Architecture — the big picture

Five agents, one shared pricing + scoring + analysis pipeline, two languages glued through a local HTTP proxy that is auto-spawned by `bench sweep`.

### Data flow for one experiment row

```text
./bench sweep --config configs/v1.4-canonical-gemma4.yaml --strategies heuristic --seeds 42
  → hybrid_coding_eval.cli.bench._cmd_sweep
  → spawn router/server.mjs (LOCAL_MODEL=<config.models.local>, PORT=<config.router.port>)
    → for each (strategy, seed):
      → hybrid_coding_eval.cli.bench._cmd_run
      → hybrid_coding_eval.cli.run.main                  # argv shim (back-compat)
      → hybrid_coding_eval.core.experiment.build_task_plan()
      → hybrid_coding_eval.core.experiment.run_pair()    # dispatches per agent
           ├── agents/aider.py
           ├── agents/opencode.py
           ├── agents/mini_swe.py
           ├── agents/claude_code.py
           └── agents/cline.py
      → scorers/functional_python.py  OR  scorers/swebench.py
      → core/results.append_row()                         # one JSON line per (task, agent) to <out>/raw.jsonl
```

Rows are flushed after each `(task, agent)` completes, so sweeps are crash-resumable (`pair_already_done(raw.jsonl, task_id, route)` skips completed pairs on resume).

### The router proxy (`router/`, Node zero-deps)

OpenAI-compatible HTTP proxy on `:8787`. The `model` field of each request selects a routing strategy. Append `!local`/`!cloud` to force a backend.

Strategies (defined in `router/strategies.mjs:STRATEGIES`):

1. `always-cloud` — control baseline; every request goes cloud
2. `always-local` — control baseline; every request goes local
3. `rules` — keyword + regex rules
4. `heuristic` — agent-aware composite-score classifier
5. `llm-classifier` — `qwen3:0.6b` returns SIMPLE/COMPLEX (~50–150 ms overhead)
6. `embedding-knn` — top-5 cosine-similar examples from a 50-example labelled corpus
7. `cascade` — heuristic first; on borderline confidence, llm-classifier tiebreaks
8. `phase-aware` (v1.4) — deterministic aider role-marker split (architect→cloud, editor→local); falls back to legacy heuristic for non-aider agents

Decisions are appended to `router/logs/decisions.jsonl` and correlated back to rows via the `bench_run_id` in the `model` field.

### Auto-spawn-router (v1.4)

`bench sweep` reads `models.local` from the config and spawns `node router/server.mjs` with:

- `LOCAL_MODEL=<config.models.local>`
- `CLOUD_MODEL=<config.models.cloud>` (default `gpt-5.5`)
- `OPEN_AI_API_KEY=...` (loaded from `.env`)
- `PORT=<config.router.port>` (default 8787)

…then waits for `/healthz` 200 before running the first pass. Tears down on completion. Pass `--external-router` to opt out (e.g. for debugging). For `--cascade-thresholds`, the router is respawned once per threshold value with `ROUTER_CASCADE_THRESHOLD` injected on top of `LOCAL_MODEL`.

### Metrics schema (`core/metrics.py`)

One `ResultRow` per (task, agent, seed). Tokens split into `local_*` / `cloud_*` (always-local must always have `cloud_* = 0`; non-zero is a routing bug). Metadata fields: `variant`, `cloud_model_id`, `local_model_id`, `judge_model_id`, `router_classifier_model_id`, `router_strategy`, `seed`, `config_sha`. All optional for back-compat with v1.0–v1.3 datasets.

### Scorers

- `scorers/functional_python.py` — extracts the first Python code block from the agent output, runs pytest in a `python:3.12-slim` Docker sandbox (image `hybrid-eval-python:latest`) with `--network none`, memory caps, 60 s wall-clock timeout. Used by `puzzles` and `refactors`.
- `scorers/swebench.py` — shells out to upstream `swebench.harness.run_evaluation` for `real-prs` (one Docker container per instance). Does not reimplement SWE-bench scoring.

`scorers/llm_judge.py` was deleted in v1.4 — pairwise LLM-judge scoring is no longer part of the canonical pipeline. (Pre-v1.4 datasets that have it stay valid; new runs don't produce judge rows.)

### Analysis pipeline

`analysis.all` runs (in order): `aggregate` → `bootstrap` → `arqgc` → `decision_matrix_v2` → `cost_scenarios` → `token_budget` → `viz/cost_quality_pareto` + `viz/decision_heatmap`.

## Conventions and gotchas

- **Always call Python via `.venv/bin/python` or `.venv/bin/pytest`**, not bare `python`. The repo installs editable via `pip install -e ".[dev]"`.
- **The router proxy is auto-spawned by `bench sweep`.** You no longer need a separate `(cd router && ./start.sh) &` terminal. If you're running individual tests or scripts that need the proxy, start it manually.
- **`bench rescore` and `bench rejudge` are dead.** Their subparsers exist; their implementation modules don't. Don't call them.
- **`tests/test_*` marked `slow`** invoke the Docker harness (minutes per test). Skip with `-m 'not slow'`.
- **Preserved runs are read-only.** `results/raw.jsonl` and the tracked `results/runs/{01..04, 07, 11}/` dirs never change bytes.
- **Cost is derived, not stored.** Any `cost_usd_*` field in `raw.jsonl` is a bug. Cost is computed on read via `core/pricing.py`. The 6 pricing scenarios live in `configs/pricing/pricing_tables.json`.
- **Env keys**: `OPENAI_API_KEY` / `OPEN_AI_API_KEY` accepted (router checks both). `ANTHROPIC_API_KEY` only used by `claude_code` agent — no longer required for any scorer.
- **Task classes**: `puzzles` (Exercism Python), `refactors` (real-developer D-tasks), `real-prs` (SWE-bench Verified). The v1.4 names appear in `BenchmarkConfig.task_classes` and in `bootstrap_cis.json` cell keys.
- **Agent names** (`BenchmarkConfig.agents`): `aider`, `opencode`, `mini-swe-agent`, `claude-code`, `cline`. Internally the orchestrator maps these to `R6..R10` (only seen in code comments and `decisions.jsonl`).
- **Local guards on by default** (v1.4.1): every local call is capped at 4096 `num_predict`, 180 s wall-clock, `repeat_penalty=1.1`. If a new local model needs different knobs, override via `ROUTER_LOCAL_*` env vars.
- **`vendor/`** is read-only. Long-term fix for vendored bugs is an upstream PR.
- **YAML configs** are the canonical sweep-definition surface. Override fields on the CLI with `--set key.path=value`.
- **Legacy R1–R5 routes deleted in v1.4.** Historical 250-row v3 dataset stays at its commit; new sweeps go through the 5 agents only.

## Where to read next

In priority order:

1. `docs/REPRODUCING.md` — copy-paste v1.4 reproducer + how-to-read-results cell→headline map
2. `docs/release-notes/v1.4.1.md` — latest canonical findings (3-model leaderboard)
3. `docs/release-notes/v1.4.0.md` — v1.4.0 708-row sweep results
4. `docs/BENCHMARK_NEW_MODEL.md` — add-a-new-local-model walkthrough
5. `docs/METHODOLOGY.md` — scoring rubrics, biases acknowledged
6. `docs/ROUTING_STRATEGIES.md` — deep dive on the 8 router strategies
7. `docs/AGENTIC_ROUTES.md` — 5-agent design + correlation-id attribution
8. `docs/ARCHITECTURE.md` — long-form code layout + data flow
9. `docs/PRIOR_ART.md` — 2026 research synthesis
10. `CONTRIBUTING.md` — for anyone adding a model, benchmark, or strategy
11. `CHANGELOG.md` — v1.0 → v1.4.1 lineage

## License + attribution

- **Code** (`src/`, `router/`, `tests/`, `configs/`, `bench`): MIT — see `LICENSE`.
- **Data + figures + docs prose** (`results/`, `docs/`, charts): CC-BY-4.0 — see `LICENSE-DATA`. See `LICENSE.md` for the file-type breakdown.
- **Third-party**: see `NOTICE.md` and `vendor/README.md`.

Suggested citation: BibTeX entry in `README.md`.
