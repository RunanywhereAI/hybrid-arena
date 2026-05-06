# Run 03 — v2-devstral

**Date:** 2026-05-06
**Purpose:** test whether a stronger, SWE-bench-specialised local model rescues R3's SWE-bench performance.

## What changed since run 01

- **Local model swapped** from `qwen3.6:27b-coding-mxfp8` → `devstral:24b` via `LOCAL_MODEL=devstral:24b` env var at router launch.
- No code changes. Router and runners are model-agnostic.
- Synth-budget fix from run 02 still applied.

## Scope

- All 30 tasks × R2 + R3 = 60 rows (R1 unchanged; carried from run 01).
- Runs category A, B, and C all fresh with Devstral as the local backend.

## Headline findings

### Category A (HumanEval+)

- R2-devstral: 9/10 (qwen was 10/10 — slightly worse).
- **R3-devstral: 10/10** (qwen was 8/10). The spec-loss regressions on HumanEval/103 and /15 don't recur — Devstral's code generation is cleaner; the architect pipeline no longer amplifies model weaknesses.

### Category B (SWE-bench Verified) — the headline

- R2-devstral: 0/10 (qwen was 1/10 — weaker in isolation).
- **R3-devstral: 3/10 — matches R1 cloud-only (3/10).**
- R3-devstral passes: `django-11163`, `django-11179`, `django-15863`.
- Per-task matrix lives in `decision_matrix.md` and `../../REPORT.md`.

This is the first time any hybrid route reaches quality parity with R1 on SWE-bench Verified.

### Category C (BigCodeBench-Hard + custom-arch)

- R3-devstral BigCodeBench pytest: 2/5 (same as qwen).
- Custom-arch composites similar to run 02's qwen R3 (high; ties R1 per Opus).

## Cost + wall

| route | B cost/task | B wall/task | B passes |
|---|---:|---:|---:|
| R1 | $0.126 | 67 s | 3/10 |
| R3-devstral | $0.144 | 194 s | 3/10 |

Quality parity, small cost premium on R3. Local-token savings don't offset cloud planner+synth overhead. Next optimisation: shrink the planner and synth prompt prefixes (prompt-caching, context truncation).

## Files

| file | notes |
|---|---|
| `raw.jsonl` | 60 rows. R3 rows' `routing.per_call_backends` mention `devstral:24b` (confirms the swap took effect). |
| `outputs/*_R2.txt` | Devstral answers; ~1-3 KB each on A/B, ~3 KB on C. |
| `outputs/*.r3.arch.json` + `.r3.answer.txt` | R3 hybrid traces with devstral as local executor. |
| `env-manifest.json` | Captures `router_proxy.local_model: devstral:24b`. |

## What this run does NOT answer

- R4 Minion is in run 04, not here.
- Single-sample per task — no confidence bounds.
- Devstral's specific weakness on SWE-bench in isolation (R2 = 0/10) vs its success in the hybrid R3 (3/10) isn't explained — a separate experiment would check which local-call patterns it's good vs bad at.
