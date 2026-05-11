# Run 11 — triple-judge robustness audit (Category D, refactor + review)

_Not a sweep — re-judges the D3 (refactor) and D4 (review) pairings from `results/runs/07-v3-devstral-all-routes/` under three judges × two A/B orders. No inference re-run._

## Headline

**v3 sweep's D3/D4 verdicts survive triple-judge audit.** 96 verdicts = 16 pairings × 3 judges × 2 orders. **Every verdict is R1 wins.** Zero ties, zero flips, zero errors.

| result | count |
|---|---:|
| A-wins (R1) | **96 / 96** |
| B-wins (R3 or R4) | 0 / 96 |
| tie | 0 / 96 |
| error | 0 / 96 |

Aggregate agreement:

- **Unanimous pairings**: **16 / 16** (all 6 verdicts within the pairing agree).
- **Single-judge dissent pairings** (5 of 6 verdicts agree): 0 / 16.
- **Order-flip pairings** (at least one judge swapped its verdict when A/B order reversed): **0 / 16**.

This is the strongest robustness signal we've measured. For comparison, the MVP triple-judge audit on custom_arch (`../10-judge-robust/`) had 3 of 30 verdicts come back as a non-tie under order reversal — 1 of 5 pairings had a single-judge order-flip. Run 11's D3+D4 audit shows **zero flips out of 96 verdicts**.

## Per-pairing agreement

8 D-tasks × 2 pairings (R1-vs-R3, R1-vs-R4) = 16 pairings. Every cell is a unanimous A-win.

| task | pair | unanimous? | majority | order-swap flips |
|---|---|:-:|---|---:|
| `real-dev/d3-constants-to-enum` | R1_vs_R3 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d3-constants-to-enum` | R1_vs_R4 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d3-extract-validation-helper` | R1_vs_R3 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d3-extract-validation-helper` | R1_vs_R4 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d3-replace-try-except-with-contextmanager` | R1_vs_R3 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d3-replace-try-except-with-contextmanager` | R1_vs_R4 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d3-split-god-module` | R1_vs_R3 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d3-split-god-module` | R1_vs_R4 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d4-review-cache-invalidation` | R1_vs_R3 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d4-review-cache-invalidation` | R1_vs_R4 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d4-review-pagination` | R1_vs_R3 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d4-review-pagination` | R1_vs_R4 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d4-review-sql-injection` | R1_vs_R3 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d4-review-sql-injection` | R1_vs_R4 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d4-review-timezone-handling` | R1_vs_R3 | yes | **A** (6/6) | 0/3 judges |
| `real-dev/d4-review-timezone-handling` | R1_vs_R4 | yes | **A** (6/6) | 0/3 judges |

## Per-judge agreement and margin

All three judges always declare R1 the winner; the only variation is on the margin (the score gap between R1 and the hybrid response, normalised to [0, 1]).

| judge | n verdicts | mean margin | median margin |
|---|---:|---:|---:|
| `claude-opus-4-7` | 32 | 0.938 | 1.000 |
| `claude-sonnet-4-6` | 32 | 1.000 | 1.000 |
| `gpt-5.5` | 32 | 1.000 | 1.000 |

Sonnet-4-6 and gpt-5.5 give R1 the maximum margin on every single verdict (R1 score = 5.0, hybrid score = 1.0). Opus-4-7 is slightly more generous to the hybrid responses on 4 of its 32 verdicts (a margin of 0.6-0.85 instead of 1.0), but never enough to change the winner. Opus is the only judge that occasionally rates a hybrid composite above 1.0; the other two judges treat the hybrid responses as essentially failed task attempts.

By pair:

| pair | mean margin (across all 48 verdicts) |
|---|---:|
| R1_vs_R3 | 0.983 |
| R1_vs_R4 | 0.975 |

R3 and R4 lose to R1 with effectively identical margins on D3+D4. The hybrid routes don't differ at the judge level on these prose tasks — both produce outputs the judges rate as failed attempts.

## What this means for the v3 sweep

This audit was designed to test whether the D3+D4 verdict pattern observed in `../07-v3-devstral-all-routes/` ("R1 dominates prose; R3 and R4 lag by 0.2-0.5 composite") could be explained away by judge bias or A/B-position bias. It cannot:

- **Cross-vendor agreement**: Anthropic judges (opus-4-7, sonnet-4-6) and OpenAI judge (gpt-5.5) all agree on every verdict. No "same-family" bias (the sweep used opus-4-7; if the sweep had been judge-biased, gpt-5.5 — a different vendor entirely — would dissent).
- **A/B position independence**: every judge gives the same verdict whether R1 is shown first or second. The MVP audit had one judge flip on three of five custom-arch pairings under order reversal; that does not happen here.
- **Scale**: 96 verdicts is the largest robustness audit in this project (vs run 10's 30 verdicts).

So run 07's claim — "R1 cloud-only wins decisively on D3 refactors and D4 code reviews; hybrid routes lose 0.2-0.5 composite" — is judge-robust and order-robust on this 8-task slice.

## Config

- **Judges:** `claude-opus-4-7`, `claude-sonnet-4-6`, `gpt-5.5`.
- **Pairings:** R1_vs_R3 and R1_vs_R4 (R5 is not audited; on D3/D4 R5 has composite ≈ 0.00 so a triple-judge audit isn't likely to flip "R1 wins" there either, but the data isn't in this run).
- **Tasks:** 8 = the 4 D3 + 4 D4 tasks from `results/runs/07-v3-devstral-all-routes/raw.jsonl`.
- **Orders:** AB and BA per (task, pair, judge); the script canonicalises the recorded `winner` so A always = the first-named route in the `pair` field.
- **Source run:** `results/runs/07-v3-devstral-all-routes/`.
- **Script:** `bin/judge_robust_d3_d4.py`.

Re-run: `./.venv/bin/python bin/judge_robust_d3_d4.py`.

## What this run does NOT answer

- **No R2 or R5 audit.** This run audits only R3 and R4 against R1. R5 wasn't included because its D3/D4 composite is already 0.00 on the sweep — adding the audit would be expected to confirm R1 wins unanimously, but we haven't run it.
- **No custom_arch (C) audit on the v3 outputs.** Run 10 audited custom_arch under qwen (from run 02), not under devstral (from run 07). The v3 R3-vs-R1 custom_arch pairings are still single-judge single-order — they may or may not be order-robust.
- **No A or B audit.** Categories A and B are functionally scored, so an LLM-judge audit is not the right test for them (the test harness gives the verdict).
- **No D1/D2/D5 audit.** D1 and D5 use a functional scorer; D2 has no scorer (deferred). Only D3 and D4 are judge-only on the v3 sweep, so only D3+D4 needed this audit.
- **No effect-size CI.** This audit reports verdict counts and mean margin only; we don't compute a confidence interval on the per-judge agreement rate. With 32 verdicts per judge and 100% agreement, the lower 95% Wilson bound on the agreement rate is ~91% — interpret "100% unanimous" accordingly.

## Files

| file | notes |
|---|---|
| `judge.jsonl` | 96 verdicts. Each row has `task_id`, `pair`, `route_a`, `route_b`, `order` (AB or BA), `judge_model`, `winner` (canonicalised — A = first route in `pair`), `margin`, `a_score`, `b_score`, `a_dimensions`, `b_dimensions` (correctness / completeness / style / reasoning_depth / practicality), and `reasoning` (judge prose). |
| `run-notes.md` | This file. |

No `raw.jsonl` or `outputs/` — those live under `../07-v3-devstral-all-routes/`. This run consumed those outputs and produced only verdicts.
