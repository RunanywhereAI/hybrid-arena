# Run 02 — v2-qwen-fixed-synth

**Date:** 2026-05-05 / 2026-05-06
**Purpose:** close the synth-budget bug that v1 (run 01) flagged; re-judge with Claude Opus 4.7 cross-vendor.

## What changed since run 01

Two caveats run 01 flagged for a reader:

1. **Synth-budget bug.** Run 01's R1 and R3 custom-arch rows produced 0-byte outputs on 4/5 tasks because `gpt-5.5`'s reasoning_tokens consumed the entire completion budget. Fix: bump R1 default `max_tokens` 8000 → 16000 and architect synth `maxTokens` 2500 → 16000.
2. **Judge self-preference.** Run 01's judge fell back to `gpt-5` (same family as R1) because `ANTHROPIC_API_KEY` wasn't loaded. Fix: load the key; rejudge with `claude-opus-4-7` (cross-vendor, bias-clean).

## Scope

- Re-ran category C only (10 tasks × R1 + R3 = 20 rows) with the bugfix.
- Carried the R2 custom-arch rows forward from run 01 (qwen R2 unaffected by the bug).
- Ran `bin/rejudge-custom-arch.py` with `claude-opus-4-7` on all 15 pairings (R1-vs-R2, R1-vs-R3, R2-vs-R3 × 5 tasks).

**Dataset:** 30 rows total (20 new + 10 carried R2).

## Headline findings

- **R1 and R3 custom-arch outputs are now 17-30 KB prose** (vs 0 bytes in run 01). Synth-budget fix verified.
- **Opus judge verdict:** R1 ties R3 on 4 of 5 custom-arch tasks (R1 slight win on `auth-multitenant-design`). R3 decisively beats R2 on all 5. R1 decisively beats R2 on all 5.
- **Bounded-ARQGC on C:** R1 0.510, R2 0.000, R3 **0.934** — R3 wins C under the cost cap.

Per-pair Opus verdicts preserved in `judge.jsonl`.

## Files

| file | notes |
|---|---|
| `raw.jsonl` | 30 rows. Every R1 and R3 row has `reasoning_tokens < completion_tokens` (bug-signature check passes). |
| `outputs/custom-arch__*_R1.txt` | 17-30 KB each. Real prose, no empty outputs. |
| `outputs/custom-arch__*.r3.arch.json` + `.r3.answer.txt` | R3 full trace + final answer. answer.txt is 20-30 KB. |
| `judge.jsonl` | 15 Opus pairings. Every row's `judge_model: "claude-opus-4-7"`. |
| `aggregate.json`, `arqgc.json`, `decision_matrix.md`, `charts/` | Derived; regenerable via `python -m analysis.all results/runs/02-v2-qwen-fixed-synth`. |

## What this run does NOT answer

- R2-qwen performance on custom-arch is UNCHANGED from run 01 (we didn't re-run R2; qwen was not affected by the bug).
- No R4, no Devstral variant. Those land in runs 03 and 04.
- Category A and B were not re-run — the bug didn't affect them.
