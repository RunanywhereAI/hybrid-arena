# Reproducing the hybrid-coding-eval v3 sweep

**Copy-paste step-by-step instructions for reproducing the v3 benchmark on a fresh machine.** Every command below has been verified against the current codebase. If one fails, consult [§13 Troubleshooting](#13-troubleshooting).

See [`METHODOLOGY.md`](./METHODOLOGY.md) for *why* we chose these tasks, routes, and scoring pipelines. This document is the *how*.

> **Status (2026-05-11).** This document covers the **v3 sweep**: 250 rows (50 unique tasks × 5 routes × 1 seed). See [`../results/runs/07-v3-devstral-all-routes/`](../results/runs/07-v3-devstral-all-routes/) for the canonical dataset. For the MVP (3 routes, 90 rows), see [`../results/REPORT_v1_mvp.md`](../results/REPORT_v1_mvp.md).

---

## 1. What this reproduces

Running the steps below produces the **exact 250-row v3 dataset** published in [`../reports/ARTICLE.md`](../reports/ARTICLE.md) and [`../results/runs/07-v3-devstral-all-routes/`](../results/runs/07-v3-devstral-all-routes/).

| | Count | What it measures |
| --- | --- | --- |
| **Unique tasks** | 50 | across 8 category-shapes |
| **Routes tested** | 5 | R1 (cloud-only), R2 (local-only), R3 (hybrid-architect), R4 (hybrid-minion), R5 (hybrid-devminion) |
| **Total rows** | 250 | 50 tasks × 5 routes × 1 seed (42) |
| **Categories** | A, B, C, D | HumanEval+ (10), SWE-bench (10), BigCodeBench+custom-arch (10), real-dev D1–D5 (20) |
| **Time estimate** | 8–12 h | on M4 Max + devstral:24b local + gpt-5.5 cloud (wall clock) |
| **Cost estimate** | ~$40 | OpenAI API (gpt-5.5 primary scenario) + ~$0.50 Anthropic judge |

The v3 sweep used:

- **Local model**: `devstral:24b` (14 GB)
- **Cloud model**: `gpt-5.5`
- **Judge model**: `claude-opus-4-7` (for prose-scored categories C custom-arch, D3, D4)
- **Router classifier**: `qwen3:0.6b` (for R3's heuristic strategy)
- **Infrastructure**: M4 Max (12 perf cores, 64 GB RAM), Docker, Ollama

---

## 2. Prerequisites

### Hardware

| | Minimum | Recommended |
| --- | --- | --- |
| **CPU** | Apple M1 or Linux x86_64 with Docker | Apple M4 Max (12 perf cores) |
| **RAM** | 32 GB | 64 GB |
| **Disk** | 100 GB free | 150 GB (Ollama models + Docker + SWE-bench images) |
| **GPU** | none required | Metal (macOS) or CUDA (Linux) optional |

**Platform notes:**

- **macOS + Apple Silicon** (M1–M4): fully supported. SWE-bench Docker under Rosetta adds ~10 min per task. This is the primary tested platform.
- **Linux x86_64**: Docker images run natively (no emulation). Ollama works via package manager. Likely faster than Apple Silicon for SWE-bench.
- **Linux ARM64**: untested. Ollama works natively; Docker SWE-bench images may not have ARM64 builds.
- **Windows**: not supported. WSL2 with Docker + Ollama may work but is untested.

### Software

- **macOS 14+** or **Linux x86_64** (Ubuntu 22.04 LTS recommended)
- **Python 3.11 or 3.12** — the orchestrator
- **Node 20+** — for the router proxy
- **Docker Desktop** (running) — required for functional sandbox and SWE-bench harness
- **Ollama 0.4+** — local model serving
- **Git** — for cloning the repo

### API keys

- **OpenAI API key** (required): for R1 (cloud-only) and R3/R4/R5 (hybrid routes)
- **Anthropic API key** (optional): for LLM-judge scoring of prose-scored categories C and D. If unset, judge scores return `null` and judge-scored rows are skipped cleanly.

### Network access

- Downloads: Ollama models (~15 GB total), Docker images (~5 GB)
- API calls: OpenAI (gpt-5.5) + Anthropic (claude-opus-4-7)

---

## 3. One-time setup

### 3.1 Clone the repo

```bash
git clone https://github.com/RunanywhereAI/hybrid-coding-eval.git
cd hybrid-coding-eval
git checkout v3-public-candidate    # the canonical tag for these numbers
```

### 3.2 Python environment

```bash
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
```

Verify the install:

```bash
.venv/bin/pytest tests/ -q -m 'not slow'
# Expected: 180 passed
```

### 3.3 Install Ollama

**macOS**: download from <https://ollama.com/download>, launch `Ollama.app`.

**Linux**:

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable --now ollama
```

Verify:

```bash
curl -s http://127.0.0.1:11434/api/tags | jq '.models[].name'
```

### 3.4 Pull local models

```bash
ollama pull devstral:24b      # primary local model (14 GB, ~10 min)
ollama pull qwen3:0.6b        # router classifier for R3 heuristic (520 MB, instant)
```

Verify:

```bash
ollama list | grep devstral
# Expected: devstral:24b   14 GB
```

### 3.5 Build the functional-scoring Docker image

```bash
docker build -f src/hybrid_coding_eval/scorers/Dockerfile.functional_python \
  -t hybrid-eval-python:latest .
```

This image (`python:3.12-slim` + pytest) sandboxes generated code execution with `--network none`, memory caps, and wall-clock timeouts.

Verify:

```bash
docker image ls | grep hybrid-eval-python
# Expected: hybrid-eval-python   latest   ~150 MB
```

### 3.6 Environment variables

Create `.env` at the repo root:

```bash
cat > .env <<'EOF'
OPEN_AI_API_KEY=sk-proj-your-openai-key-here

# Optional — required only by LLM-judge scoring
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
EOF
chmod 600 .env
```

The router (`router/start.sh`) reads `../.env` automatically. Python readers use `os.environ`, so either export the variables for the shell or let your shell auto-load `.env`:

```bash
set -a && source .env && set +a
```

### 3.7 Clone vendored Minions library (R4 and R5 only)

**R4 (Minion) and R5 (DevMinion) routes require the Stanford Minions library**, which is gitignored under `vendor/` because of its size:

```bash
cd vendor && git clone https://github.com/HazyResearch/minions.git && cd ..
```

If you skip this and try to run R4/R5, the sweep fails cleanly with `ModuleNotFoundError: No module named 'minions'`. If you only need R1/R2/R3, you can skip this step.

### 3.8 Start the router proxy

In a **separate terminal** (it runs indefinitely):

```bash
cd router && ./start.sh
```

You should see:

```text
Starting hybrid router on http://127.0.0.1:8787
  local  : http://127.0.0.1:11434/v1  model=devstral:24b
  cloud  : https://api.openai.com/v1  model=gpt-5.5  key=present
```

Or run it in the background:

```bash
(cd router && nohup ./start.sh > /tmp/router.log 2>&1 &)
```

### 3.9 Verify health and record environment

```bash
curl -s http://127.0.0.1:8787/healthz | jq .
# Expected:
# {
#   "local":  { "reachable": true,  "model": "devstral:24b", ... },
#   "cloud":  { "reachable": true,  "key_present": true,     ... }
# }
```

Record the hardware/software environment for reproducibility audit:

```bash
./bench env-detect --out results/env-manifest.json
```

This captures chip, RAM, Python version, Ollama version, Docker version, git SHA.

---

## 4. Smoke test (~30 minutes)

Before running the full 250-row sweep, validate the harness with a tiny smoke run:

```bash
./bench run --config configs/variants/_template.yaml --smoke
```

This:

- Picks 1 task per category (A, B, C)
- Runs each through R1, R2, R3 (the template config's default routes)
- Scores inline
- Writes 9 rows to `results/runs/<variant_tag>/raw.jsonl`

Verify success:

```bash
wc -l results/runs/*/raw.jsonl
# Expected: 9 (one row per pair)

jq -s '[.[] | select(.error != null)] | length' results/runs/*/raw.jsonl
# Expected: 0 (no errors)
```

If the smoke test fails, see [§13 Troubleshooting](#13-troubleshooting) before proceeding.

---

## 5. Full v3 sweep (~8–12 hours)

Once the smoke test passes, run the canonical v3 configuration:

```bash
./bench run --config configs/variants/07-v3-devstral-all-routes.yaml
```

This runs:

- **50 unique tasks** across A, B, C, D
- **5 routes**: R1, R2, R3, R4, R5
- **1 seed**: 42
- **Total**: 250 rows
- **Wall time**: 8–12 h on M4 Max
- **Cost**: ~$40 OpenAI + ~$0.50 Anthropic

Output goes to `results/runs/07-v3-devstral-all-routes/`. Rows are flushed to `raw.jsonl` after each `(task, route)` completes, so you can monitor progress:

```bash
# In another terminal:
watch -n 30 'wc -l results/runs/07-v3-devstral-all-routes/raw.jsonl'

# or tail individual results:
tail -f results/runs/07-v3-devstral-all-routes/raw.jsonl | \
  jq -c '{task_id, route, error, wall: .latency.wall_ms}'
```

### Wall time breakdown (from the canonical v3 run)

| Route | Wall time | % of total |
| --- | ---: | ---: |
| R1 (cloud-only) | 0.6 h | 5% |
| R2 (local-only) | 0.2 h | 2% |
| R3 (hybrid-architect) | 2.5 h | 21% |
| R4 (hybrid-minion) | 1.5 h | 13% |
| R5 (hybrid-devminion) | 7.1 h | 59% |
| **Total** | **11.9 h** | **100%** |

R5 dominates wall time because of its multi-round architect→editor→reviewer loops.

---

## 6. Resume a crashed sweep

If the sweep crashes partway, resume without re-running completed `(task_id, route)` pairs:

```bash
./bench run --config configs/variants/07-v3-devstral-all-routes.yaml --resume
```

The orchestrator reads `raw.jsonl`, skips any pair already present, and continues. Pairs with `error != null` are also skipped — re-run them by manually removing the row first.

---

## 7. Subset sweeps (optional)

### 7.1 Single category

```bash
./bench run --config configs/variants/07-v3-devstral-all-routes.yaml \
  --set benchmark.categories='[A]'
# Result: 10 tasks × 5 routes = 50 rows, ~1 h
```

### 7.2 Single route

```bash
./bench run --config configs/variants/07-v3-devstral-all-routes.yaml \
  --set benchmark.routes='[R1]'
# Result: 50 tasks × 1 route = 50 rows, ~40 min
```

### 7.3 Dry run (plan only)

```bash
./bench run --config configs/variants/07-v3-devstral-all-routes.yaml --dry-run
# Prints the task plan + config SHA256; does not execute
```

---

## 8. Post-sweep: re-scoring, analysis, reports

### 8.1 Re-score SWE-bench (category B only)

If you ran with `--skip-scoring` or want to re-run the Docker harness:

```bash
./bench rescore results/runs/07-v3-devstral-all-routes/
```

### 8.2 Re-judge prose-scored rows

For categories C custom-arch + D3 + D4, with a fresh `ANTHROPIC_API_KEY`:

```bash
./bench rejudge results/runs/07-v3-devstral-all-routes/
```

### 8.3 Aggregate, ARQGC, decision matrix, charts

```bash
./bench analyze results/runs/07-v3-devstral-all-routes/
```

Produces:

- `aggregate.json` — per-(category, route) means, medians, sums
- `arqgc.json` — bounded area-under-quality-cost curve per route
- `decision_matrix.md` — category × route quality/cost grid
- `charts/pareto.png`, `heatmap_quality.png`, `heatmap_cost.png`

### 8.4 Token budget (6-scenario re-pricing)

Re-price the sweep under alternate pricing scenarios without re-running inference:

```bash
./bench token-budget results/runs/07-v3-devstral-all-routes/
```

Produces `token_budget.csv` + a per-task matrix under 6 scenarios (gpt-5.5, gpt-5, gpt-5-mini, opus-4.7, sonnet-4.6, haiku-4.5).

### 8.5 Regenerate the article and appendices

```bash
./bench report article
```

Regenerates `reports/ARTICLE.md`, `reports/DECISION_TABLE.md`, `reports/TOKEN_BUDGET.md`, and the three appendices.

---

## 9. Reproducing the article numbers exactly

To match the numbers in `reports/ARTICLE.md`:

```bash
git checkout v3-public-candidate
./bench run --config configs/variants/07-v3-devstral-all-routes.yaml
```

Same hardware + same models + same seed (42) + same pricing table → identical token counts, identical costs, identical functional pass/fail. Judge scores are deterministic at `temperature=0.0`. Latencies vary with system load and network.

Cross-check your output against the published dataset:

```bash
diff <(jq -c '. | {task_id, route, tokens, quality}' \
       results/runs/07-v3-devstral-all-routes/raw.jsonl | sort) \
     <(jq -c '. | {task_id, route, tokens, quality}' \
       results/runs/07-v3-devstral-all-routes/raw.jsonl | sort)
# (compare your fresh run to the committed dataset; should be byte-identical
#  on tokens + quality.functional_pass; minor wall-clock drift is expected)
```

---

## 10. Drop in a new model (90 seconds)

```bash
cp configs/variants/_template.yaml configs/variants/my-model.yaml
# Edit:
#   variant_tag: my-model
#   models.cloud: gpt-4o            # or your new cloud model
#   models.local: ollama-new:70b    # or your new local model

ollama pull ollama-new:70b          # if it's a new Ollama model

./bench run --config configs/variants/my-model.yaml
./bench analyze results/runs/my-model/
./bench report article
```

See `examples/drop-in-a-new-model.md` for a full walkthrough.

---

## 11. Platform notes

### macOS + Apple Silicon

Fully supported. M1/M2/M3/M4 all work. SWE-bench Docker images are x86_64 only; enable Rosetta 2 emulation in Docker Desktop:

> Docker Desktop → Settings → General → ✅ **Use Rosetta for x86/amd64 emulation on Apple Silicon**

Then restart Docker. Expect ~10 min per SWE-bench task under emulation.

### Linux x86_64

```bash
# Ubuntu 22.04
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER && newgrp docker
curl -fsSL https://ollama.com/install.sh | sh
```

Docker SWE-bench images run natively. Likely 3× faster than Apple Silicon under Rosetta.

### Linux ARM64 / Windows

Untested. Use at your own risk; file an issue if you make it work.

---

## 12. Cost breakdown (canonical v3 run)

### API costs under the gpt-5.5 primary scenario

| Route | Σ cloud tokens | Cost |
| --- | ---: | ---: |
| R1 | 158 K | $3.82 |
| R2 | 0 K | $0.00 |
| R3 | 476 K | $8.65 |
| R4 | 544 K | $7.29 |
| R5 | 945 K | $19.59 |
| **Total OpenAI** | **2.1 M** | **$39.34** |

### Anthropic judge

Categories C (5 tasks) + D3 (4) + D4 (4) = 13 prose-scored tasks × 5 routes = 65 judgments. With opus-4-7 at temperature 0: ~$0.50 total.

### Re-pricing under other scenarios

The same token counts re-priced under `./bench token-budget`:

| Scenario | Total cost | Ratio to gpt-5.5 |
| --- | ---: | ---: |
| openai-gpt5.5 (primary) | $39.34 | 1.00× |
| openai-gpt5 | $12.71 | 0.32× |
| openai-gpt5-mini | $2.54 | 0.06× |
| anthropic-opus-4.7 | $100.77 | 2.56× |
| anthropic-sonnet-4.6 | $20.15 | 0.51× |
| anthropic-haiku-4.5 | $8.31 | 0.21× |

The R1 < hybrid cost ranking is invariant across all six scenarios.

---

## 13. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'minions'` | Stanford Minions is gitignored; R4/R5 need it. | `cd vendor && git clone https://github.com/HazyResearch/minions.git && cd ..` |
| `curl http://127.0.0.1:8787/healthz` → `Connection refused` | Router not running. | `(cd router && ./start.sh)` in a separate terminal. |
| `healthz` says `cloud.key_present=false` | `.env` missing or wrong var name. | Confirm `.env` has `OPEN_AI_API_KEY=sk-...` (not `OPENAI_API_KEY`). Restart router after fixing. |
| `docker: permission denied` (Linux) | User not in `docker` group. | `sudo usermod -aG docker $USER && newgrp docker` |
| `docker: ...permission denied` (macOS) | Docker Desktop not running. | Launch Docker Desktop. |
| SWE-bench harness: `exec format error` (Apple Silicon) | Rosetta emulation not enabled for x86_64 images. | Docker Desktop → Settings → General → ✅ Rosetta. Restart Docker. |
| SWE-bench harness: `No space left on device` | Docker images fill disk (~50 GB per category B run). | `docker image prune -a` |
| Local model OOMs or is very slow | devstral:24b doesn't fit in available RAM/VRAM. | Try a smaller variant (e.g. `ollama pull devstral:7b`) or reduce `num_ctx` in your Modelfile. |
| `ANTHROPIC_API_KEY not set` (warning only) | Opus judge is optional. | Expected if you skip the judge. Rows have `judge_win_rate=null`. |
| `"error": "..."` in `raw.jsonl` | Per-task infra failure (Docker, API rate-limit, timeout). | Read the row's `error` field. Re-run with `--resume` to retry. |
| Pytest `test_r3_hybrid_architect` times out | R3 subprocess test needs the router proxy. | Start router; tests auto-skip cleanly if router is down. |
| Sweep hangs on a single task | Long SWE-bench task or upstream API hang. | `Ctrl-C`, then resume with `--resume`. Inspect `progress.log` for the stalled `(task, route)`. |

---

## 14. Verifying a clean run

After a full sweep, sanity-check:

```bash
SWEEP=results/runs/07-v3-devstral-all-routes

# (a) Row count
wc -l "$SWEEP/raw.jsonl"
# Expected: 250 (or 9 if smoke)

# (b) No errors
jq -s 'map(select(.error != null)) | length' "$SWEEP/raw.jsonl"
# Expected: 0

# (c) R2 has zero cloud tokens (routing bug if non-zero)
jq 'select(.route=="R2" and (.tokens.cloud_prompt + .tokens.cloud_completion) > 0)' \
   "$SWEEP/raw.jsonl"
# Expected: empty

# (d) R1 has positive cloud tokens
jq 'select(.route=="R1" and (.tokens.cloud_prompt + .tokens.cloud_completion) == 0)' \
   "$SWEEP/raw.jsonl"
# Expected: empty

# (e) Functional categories have non-null scores
jq 'select((.category=="A" or .category=="B") and .quality.functional_pass==null)' \
   "$SWEEP/raw.jsonl"
# Expected: empty

# (f) Repo tests pass
.venv/bin/pytest tests/ -q -m 'not slow'
# Expected: all 180 pass
```

---

## 15. Known deferred or partially-working features

### D2 functional scorer (20 of 250 rows have `functional_pass=None`)

**Status**: deferred. External GitHub-issue patches (click, jsonschema, pytest, werkzeug) need a per-task harness; the current SWE-bench scorer hard-codes princeton-nlp's HF dataset. D2 rows still have valid token counts, cost, and judge scores (where applicable) — only `functional_pass` and `composite` are `None`.

To compute D2 yourself, implement a per-task harness under `src/hybrid_coding_eval/scorers/` and wire it into `core/experiment.run_pair`.

### R5 DevMinion JSON-extraction fragility

The DevMinion architect/editor protocol's `_extract_json` in `vendor/minions/minions/minion_code.py` has a brittle JSON parser. Our R5 wrapper at `src/hybrid_coding_eval/runners/r5_devminion.py` patches it to be more forgiving, but residual failures may still bias R5 down on tasks with malformed model JSON.

### SWE-bench Verified non-replication

In v1 (run 04), R4 was claimed to solve 4/10 (a Sphinx win over R1's 3/10). In v3 (run 07), same models + same harness: R1 = R3 = R4 = 3/10 on the same three Django tasks. The Sphinx wins did not replicate — almost certainly single-sample noise on a 10-task slice. The v3 article documents this honestly; it is not a bug to be reproduced.

---

## 16. Data redistribution and licensing

**Results** (raw.jsonl, charts, decision matrix, article, appendices) are licensed under **CC-BY-4.0**. You may republish and cite; please include attribution.

**Code** (harness, router, runners, scorers, analysis) is **MIT-licensed**.

**Third-party code** (vendor/minions, vendor/lm-eval-harness-judge) — see `NOTICE.md`.

Suggested citation:

> Monga, Sanchit and contributors. *hybrid-coding-eval: reproducible cost/latency/quality benchmark for local vs cloud vs hybrid LLM routing on coding tasks.* 2026. <https://github.com/RunanywhereAI/hybrid-coding-eval>. Tag `v3-public-candidate`.

---

## 17. See also

- [`../reports/ARTICLE.md`](../reports/ARTICLE.md) — the canonical v3 article (start here for interpretation)
- [`../reports/DECISION_TABLE.md`](../reports/DECISION_TABLE.md) — per-shape × route grid
- [`../reports/TOKEN_BUDGET.md`](../reports/TOKEN_BUDGET.md) — token-first cost matrix
- [`../reports/APPENDIX_ROUTES.md`](../reports/APPENDIX_ROUTES.md) — worked example per R1..R5
- [`./METHODOLOGY.md`](./METHODOLOGY.md) — scoring rubrics + biases acknowledged
- [`./ARCHITECTURE.md`](./ARCHITECTURE.md) — code layout + data flow
- [`./ROUTING_STRATEGIES.md`](./ROUTING_STRATEGIES.md) — deep dive on the 7 router strategies
- [`../results/runs/07-v3-devstral-all-routes/run-notes.md`](../results/runs/07-v3-devstral-all-routes/run-notes.md) — per-run findings
- [`../examples/drop-in-a-new-model.md`](../examples/drop-in-a-new-model.md) — 5-step walkthrough for a new model

Questions or reproducibility issues? File an issue: <https://github.com/RunanywhereAI/hybrid-coding-eval/issues>
