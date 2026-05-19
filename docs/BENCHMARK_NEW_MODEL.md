# Benchmark a new local model

The production use case for **hybrid-coding-eval** is straightforward: a new local coding model drops on Ollama (or anywhere with an OpenAI-compatible endpoint) and you want to know, with statistical confidence, **whether it's good enough to run inside a real agent loop hybridized with the cloud**.

This guide takes you from "model exists" → "publishable cost/quality numbers vs the v1.1 canonical baseline" in 5 minutes of work + a few hours of wall time.

---

## 1. Pull the new model

```bash
ollama pull qwen3.7-coder:30b              # or wherever your model lives
```

The router proxy reads `LOCAL_MODEL` from its env at startup. If the new model isn't your default, restart the proxy with the override:

```bash
LOCAL_MODEL=qwen3.7-coder:30b (cd router && ./start.sh) &
```

Cloud baseline stays `gpt-5.5` unless you override `CLOUD_MODEL`. The v1.1 canonical numbers are against gpt-5.5; keep that constant to make the comparison meaningful.

## 2. Make a variant config

```bash
cp configs/variants/_template-agentic.yaml configs/variants/26-my-model.yaml
```

Edit two lines:

```yaml
variant_tag: my-model
models:
  local: qwen3.7-coder:30b                 # ← your new model
```

Leave everything else at defaults. The template is calibrated for v1.1-shape sweeps (R8 opencode, the four strategy axes, full benchmark mix).

## 3. Smoke first (~5 min)

```bash
./bench sweep --config configs/variants/26-my-model.yaml \
  --strategies heuristic --seeds 42 \
  --smoke
```

Smoke = 1 task per category × 1 strategy = 1 row. Verifies your model handles the agent loop end-to-end (returns valid tool calls; doesn't 400 on the function-call format).

If smoke fails the most common causes are:

- **400 on tool-call format**: your model's tokenizer can't handle opencode's tool schema. Tune the temperature or try a different model.
- **Timeout**: bump `DEFAULT_TIMEOUT_S` in `r8_opencode.py` or use a faster model.
- **No diff produced**: model's understanding of the harness is weak. Real-time judgment call.

## 4. Full canonical sweep (~6–10 h wall, ~$10–20 spend)

```bash
./bench sweep --config configs/variants/26-my-model.yaml \
  --strategies always-cloud,always-local,heuristic,cascade \
  --seeds 42,7,13
```

25 tasks × 4 strategies × 3 seeds = 300 rows. Per-cell subdirectories under `results/runs/26-my-model/`.

## 5. Analyze

```bash
./bench analyze results/runs/26-my-model/
```

Produces:

- `aggregate.json` — per-cell sums, means, medians (Categories × routes × strategies)
- `bootstrap_cis.json` — 95% percentile CIs for `pass_rate`, `cost_usd`, `cloud_fraction`, `wall_ms` per cell
- `decision_matrix.md` — human-readable summary
- `charts/pareto.png` + 3 heatmaps

## 6. Compare to the v1.1 canonical baseline

```bash
gh release download v1.1.K -p 'results-v1.1.K.tar.gz'
tar xzf results-v1.1.K.tar.gz -C /tmp/v1.1-baseline/
diff <(jq -S '.cells' results/runs/26-my-model/bootstrap_cis.json) \
     <(jq -S '.cells' /tmp/v1.1-baseline/.../bootstrap_cis.json)
```

The two `bootstrap_cis.json` files use the same cell-key shape (`<category>::<route>::<strategy>`), so you can compare CIs directly. Cells where your new model's CI is strictly better than the baseline's CI are real wins; cells where they overlap are statistically tied.

## 7. (Optional) Publish

Open a PR adding `configs/variants/26-my-model.yaml` to the repo. Maintainer reviews + merges. Your variant becomes a permanent benchmark recipe. If you also include `results/runs/26-my-model/bootstrap_cis.json` + `run-notes.md`, the maintainer can include your dataset in the next minor release's tarball.

---

## What the canonical sweep covers (v1.1)

The default `_template-agentic.yaml` runs against this benchmark mix:

| Benchmark | Category | Tasks | Why |
| --- | --- | --- | --- |
| SWE-bench Verified | B | 10 | The famous agent benchmark |
| HumanEval+ | A | 5 | The famous single-call benchmark (sanity check) |
| Exercism Python | X | 5 | Small functional tasks (v1.1 addition) |
| real-developer D1/D5 | D | 5 | Hand-crafted practical tasks |
| **Total** | | **25 tasks** | |

R8 opencode is the only route in scope for v1.1. R6/R7 are experimental — you can add them with `--set benchmark.routes=[R6,R7,R8]` but the canonical bootstrap CIs only include R8.

## Comparable canonical baselines

| Tag | Local model | Wall | Cost (gpt-5.5 cloud) | Notes |
|---|---|---|---|---|
| v1.1.K (latest) | qwen3-coder:30b | ~8 h | ~$15-25 | Bundled with `gh release v1.1.K` |
| v1.0.0 | devstral:24b | ~12 h | ~$40 | Non-agentic R1-R5 only — see results/runs/07-…/ on the v1.0.0 tag |

## When NOT to benchmark a new model with this harness

- **Non-coding domain.** This harness is calibrated for coding tasks; a creative-writing or math model will produce uninterpretable scores.
- **Pinned to a specific tool's chat format.** R8 invokes opencode which expects an OpenAI-compatible API with function-call support. Models without that won't work end-to-end.
- **You only care about throughput.** This harness measures quality and cost; raw tokens/sec belongs in lm-eval-harness or vLLM's own benchmarks.

---

## See also

- `docs/AGENTIC_ROUTES.md` — R6/R7/R8 design + correlation-id attribution
- `docs/ROUTING_STRATEGIES.md` — full strategy taxonomy
- `docs/REPRODUCING.md` — fresh-clone setup recipe
- `CONTRIBUTING.md` — how to propose new tasks / strategies / benchmarks
