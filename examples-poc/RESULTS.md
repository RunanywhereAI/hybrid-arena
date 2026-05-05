# Hybrid vs cloud-only comparison — aggregate

Run at: 2026-04-29 (3 experiments)

- **Local model**: `qwen3.6:27b-coding-mxfp8` — Qwen team's coding-tuned 27 B dense in mxfp8, ~31 GB on disk, served via Ollama native API with `think:false`. ~10 tok/s on M4 Max.
- **Cloud model**: `gpt-5.5` — $5/M input, $30/M output, $0.50/M cached input (models.dev, 2026-04-27).
- **Methodology**: same prompt → (a) single-shot via `router/always-cloud`, (b) architect mode (planner cloud, executor `router/heuristic`, synthesizer `router/heuristic`).

## Headline

| experiment | cloud cost | hybrid cost | hybrid vs cloud-single | architect-all-cloud baseline | hybrid vs that baseline | cloud time | hybrid time |
|---|---:|---:|---:|---:|---:|---:|---:|
| **01 — wordcount CLI** | $0.0593 | $0.1903 | **3.2× more expensive** | $0.5051 | **62 % cheaper** | 26.5 s | 15 m 13 s |
| **02 — todo REST API** | $0.0667 | $0.1339 | 2.0× more expensive | $0.4221 | **68 % cheaper** | 24.1 s | 20 m 20 s |
| **03 — URL shortener** ⚠ | $0.1259 | $0.1629 | 1.3× more expensive | $0.4375 | **63 % cheaper** | 57.5 s | 18 m 04 s |
| **avg / sum** | $0.252 | $0.487 | — | $1.365 | — | 1 m 48 s | 53 m 37 s |

> ⚠ **exp 03 hybrid synth call returned 0 visible tokens** — gpt-5.5 spent all 2,500 completion tokens on hidden reasoning. Per-step outputs were produced (working code) but the synthesizer didn't emit a stitched answer. Discussed in the article.

## Per-experiment summary

### 01 — wordcount CLI

- **cloud-only**: $0.0593, 26.5 s, 205 in / 1,942 out (938 reasoning)
- **hybrid**: $0.1903, 15m 13s, 11 calls (8 local / 2 cloud + 1 cloud planner)
- routing pattern: planner cloud, 1 of 8 executor steps cloud (an `edit` step), synth cloud
- synth alone: $0.113 (8 510 in, 2 338 out)
- artefacts: `01-wordcount-cli/cloud-only/run.md`, `01-wordcount-cli/hybrid/run.md`, `01-wordcount-cli/comparison.md`

### 02 — todo REST API

- **cloud-only**: $0.0667, 24.1 s, 314 in / 2,172 out (512 reasoning)
- **hybrid**: $0.1339, 20m 20s, 12 calls (10 local / 1 cloud planner + synth)
- routing pattern: planner cloud, **all 10 executor steps local** (every step had hint=local from the planner), synth cloud
- synth: $0.084 (6 596 in, 1 710 out)
- artefacts: `02-todo-api/cloud-only/run.md`, `02-todo-api/hybrid/run.md`, `02-todo-api/comparison.md`

### 03 — URL shortener

- **cloud-only**: $0.1259, 57.5 s, 465 in / 4,120 out (2,048 reasoning) — produced full 5-file project including README design rationale
- **hybrid**: $0.1629, 18m 4s, 11 calls (9 local / 1 cloud planner + 1 cloud synth)
- routing pattern: planner cloud, all 9 executor steps local, synth cloud
- synth: $0.108 — but 0 visible tokens, all 2,500 completion budget consumed by reasoning
- per-step local outputs were produced (real working code) — see `03-url-shortener/hybrid/events.json` for each
- artefacts: `03-url-shortener/cloud-only/run.md`, `03-url-shortener/hybrid/run.md`, `03-url-shortener/comparison.md`

## Cross-cutting observations

1. **Single-shot cloud cost-dominates hybrid on simple-enough tasks.** The decomposition tax (steps re-receive accumulated context, prompt tokens grow ~100×) outweighs the per-step local savings on tasks small enough to fit one cloud roundtrip.
2. **Hybrid wins decisively against the same decomposition done all-cloud.** All three experiments saved 62–68 % vs an architect-all-cloud baseline. If you're going to decompose anyway, hybrid is the right way.
3. **The synth step is the single biggest line item.** Its input is the concatenation of all step outputs, so it grows with plan length. Across the three runs, synth was 26–66 % of total hybrid cost.
4. **`gpt-5.5` reasoning can blow the synth budget.** Exp 03's synth used all 2,500 completion tokens on reasoning before producing visible content. Either bump the synth ceiling, or use a less-aggressive-reasoning model for synth specifically.
5. **Latency: 25–35× slower for hybrid.** 24–58 s cloud → 15–20 min hybrid. The 27 B dense local at 10 tok/s × 10 sequential steps × steps generating 100–1500 tokens of code each.
