# results/runs/ — four experimental runs, preserved

Each subdirectory here is one complete, self-contained run. They're numbered in chronological + causal order (each run reacted to findings from the previous).

**If you just want the answer:** read `../REPORT.md` (one directory up). It summarises all four runs.

**If you want per-run detail:** each directory below has its own `raw.jsonl`, `outputs/`, `progress.log`, `env-manifest.json`. Drop in, understand that variant in isolation.

## The four runs

| # | directory | when | dataset | the finding |
|---|---|---|---|---|
| 01 | `01-v1-qwen-original/` | 2026-05-05 | 90 rows, all 30 tasks × R1, R2, R3, qwen local, gpt-5 judge | **The v1 sweep.** Reported "R3 is Pareto-dominated on every category." Later invalidated — driven by a synth-budget bug + weak local model on SWE-bench. |
| 02 | `02-v2-qwen-fixed-synth/` | 2026-05-05 | 20 rows, category C × R1, R3, qwen local, **Claude Opus 4.7 judge** | **Closed the synth-budget bug.** R1 and R3 no longer produce 0-byte outputs on reasoning-heavy tasks. Opus (cross-vendor) judge rates R3 ≈ R1 on 4/5 custom-arch tasks. |
| 03 | `03-v2-devstral/` | 2026-05-06 | 60 rows, all 30 tasks × R2, R3, **devstral:24b local** | **Local-model swap test.** R3-devstral hits 3/10 on SWE-bench Verified — matches R1 cloud-only. Also fixes the qwen R3 regressions on HumanEval+. |
| 04 | `04-r4-minion/` | 2026-05-06 | 10 rows, SWE-bench × R4 (Stanford Minion protocol) | **R4 beats R1 on SWE-bench.** 4/10 pass, cheaper + more accurate than cloud-only. First route to Pareto-improve on R1. |

## What each run directory contains

Common structure (not every file is present in every run):

```
runs/NN-*/
├── raw.jsonl            ← THE data rows for this run (one JSON per (task, route))
├── outputs/             ← raw model-generated text for each (task, route)
├── progress.log         ← orchestrator's per-row progress line
├── run.log              ← orchestrator stdout (pre-scoring)
├── env-manifest.json    ← hardware + software snapshot at run time
├── aggregate.json       ← per-cell medians/means (regenerable via analysis.all)
├── arqgc.json           ← Bounded-ARQGC per (category, route) (regenerable)
├── decision_matrix.md   ← category × route → recommendation (regenerable)
├── charts/              ← Pareto, heatmaps, per-category (regenerable)
├── judge.jsonl          ← LLM-judge pairings (for category C runs only)
├── manual_audit.md      ← 5-row human spot-check (run 01 only)
├── ERRORS.md            ← infrastructure errors log (run 01 only)
└── REPORT.md / run-notes.md  ← per-run write-up (run 01 has the full v1 report)
```

**Which files are data, and which are derived:**

- `raw.jsonl`, `outputs/`, `judge.jsonl`, `env-manifest.json`, `progress.log` → SOURCE DATA. Cannot be regenerated.
- `aggregate.json`, `arqgc.json`, `decision_matrix.md`, `charts/*.png` → DERIVED. Regenerate any time via `python -m analysis.all results/runs/NN-*/`.

## How runs relate to the merged dataset

`../raw.jsonl` (one level up) is a merge of all four runs, with a `"variant"` field added to each row:

| run | variant tag in `results/raw.jsonl` | rows |
|---|---|---:|
| 01 | `v1-qwen` | 90 |
| 02 | `v2-qwen-fixed` | 20 |
| 03 | `v2-devstral` | 60 |
| 04 | `r4-minion` | 10 |
| **total** | | **180** |

For any analysis, filter `results/raw.jsonl` by variant; or drop into the specific `runs/NN-*/raw.jsonl` if you want that variant in isolation.

## A note about run 01's REPORT.md

`runs/01-v1-qwen-original/REPORT.md` is kept verbatim (with a deprecation banner) to preserve the v1 narrative for history. **Its main-body claims about R3 being Pareto-dominated are wrong** — that conclusion did not survive the v2 runs (02–04). The v1 file stays because:

- It records what we thought at the end of the v1 sweep.
- Its §12 addendum documents the caveats and forecasted where v2 would change things — which is exactly what happened.
- Deleting it erases the reasoning trail a reader needs to understand why the canonical `../REPORT.md` says what it says.

Always prefer `../REPORT.md` for current claims.
