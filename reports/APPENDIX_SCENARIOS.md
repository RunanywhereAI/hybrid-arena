# Appendix B — multi-scenario decision matrix

This appendix re-prices the full dataset under six official
per-million-token cloud-pricing scenarios. Cost is derived at read
time from `configs/pricing/pricing_tables.json` (SHA256 pinned); no
inference is re-run. The source table is `results/reprice/decision_matrix.md`
and the canonical raw data is `results/reprice/cost_by_scenario.csv`.

The v3 sweep adds **category D (real-developer tasks)** and a
**fifth route, R5 (Stanford DevMinion)** to the historical
200-row dataset. Both extensions are surfaced as their own column
groups below; the MVP numbers (R1/R3/R4 on A/B/C) are preserved
verbatim and the v3 numbers are appended without overwriting.

## How to read this

Each scenario has a 4×5 grid of (category × route) cells. Every cell
carries:

- **pass rate** with Wilson 95% CI — honest at small N, bounded to
  [0, 1], asymmetric. For category D the pass denominator is **8**
  (D1's 4 + D5's 4); D2/D3/D4 are judge-scored or deferred and
  contribute zero to the functional-pass count.
- **cloud tok / local tok** — medians per row in this cell.
- **wall** — median wall-clock per row.
- **$ cost** — median USD per row under this scenario.

The pass rates do not change across scenarios (it's the same dataset),
only the $ cost column moves.

---

## Scenarios covered

1. **`openai-gpt5.5`** — the primary scenario (matches the actual
   cloud leg used during inference). Input $5/M, output $30/M.
2. **`openai-gpt5`** — 4× cheaper; input $1.25/M, output $10/M.
3. **`openai-gpt5-mini`** — 20× cheaper than gpt-5.5; input
   $0.25/M, output $2/M.
4. **`anthropic-claude-opus-4.7`** — frontier-Anthropic; input $15/M,
   output $75/M (2.5× more than gpt-5.5).
5. **`anthropic-claude-sonnet-4.6`** — mid-tier Anthropic; input $3/M,
   output $15/M.
6. **`anthropic-claude-haiku-4.5`** — cheapest Anthropic; input $1/M,
   output $5/M.

---

## The headline table

$/correct under each scenario, for Category B (SWE-bench Verified),
where hybrid routing has the clearest ROI signal:

| Route | gpt-5.5 | gpt-5 | gpt-5-mini | claude-opus-4.7 | claude-sonnet-4.6 | claude-haiku-4.5 |
|---|---:|---:|---:|---:|---:|---:|
| R1 | $0.42 | $0.14 | $0.028 | $0.80 | $0.18 | $0.06 |
| R3 | $0.72 | $0.23 | $0.047 | $1.55 | $0.32 | $0.10 |
| **R4** | **$0.56** | $0.18 | $0.035 | $1.22 | $0.24 | $0.08 |

Wall-clock doesn't change with pricing (obviously). It's in the cell
table below.

### v3 update — category B, all five routes

Run 07 (`results/runs/07-v3-devstral-all-routes/`) re-priced under
the same scenarios. R5 has zero correct rows on B so $/correct is
undefined; R4 lost the v1 "beats R1" advantage and ties R1/R3 at
3/10 functional pass.

| Route | gpt-5.5 | gpt-5 | gpt-5-mini | claude-opus-4.7 | claude-sonnet-4.6 | claude-haiku-4.5 |
|---|---:|---:|---:|---:|---:|---:|
| R1 | $0.39 | $0.13 | $0.026 | $0.98 | $0.20 | $0.07 |
| R2 | — | — | — | — | — | — |
| R3 | $0.53 | $0.17 | $0.034 | $1.36 | $0.27 | $0.09 |
| R4 | $0.74 | $0.23 | $0.046 | $1.93 | $0.39 | $0.13 |
| R5 | — | — | — | — | — | — |

---

## Category D headline — $/correct under each scenario

For category D (real-developer tasks), denominator = 8 (D1 + D5
functional). D2 is deferred; D3/D4 are judge-only. R2 and R5 have
zero functional passes on D2/D3/D4 by construction:

| Route | gpt-5.5 | gpt-5 | gpt-5-mini | claude-opus-4.7 | claude-sonnet-4.6 | claude-haiku-4.5 |
|---|---:|---:|---:|---:|---:|---:|
| **R1** | **$0.17** | **$0.055** | **$0.011** | **$0.45** | **$0.089** | **$0.030** |
| R2 | — | — | — | — | — | — |
| R3 | $0.69 | $0.22 | $0.045 | $1.78 | $0.36 | $0.12 |
| R4 | $0.78 | $0.24 | $0.048 | $2.05 | $0.41 | $0.14 |
| R5 | $2.04 | $0.67 | $0.13 | $5.18 | $1.04 | $0.35 |

**R5 is the most expensive route on D by a factor of ~3×.** The
review-loop replays context across rounds and produces few correct
answers (4/8 pass — matching R4 — but at ~3× R4's cost). On every
pricing scenario R1 cloud-only is the $/correct winner on D.

### Category D median $/row (no pass-rate normalization)

This is the raw per-row cost, useful for budgeting bursts of
real-dev tasks where you can't predict the pass rate up front:

| Route | gpt-5.5 | gpt-5 | gpt-5-mini | claude-opus-4.7 | claude-sonnet-4.6 | claude-haiku-4.5 |
|---|---:|---:|---:|---:|---:|---:|
| R1 | $0.035 | $0.011 | $0.0022 | $0.093 | $0.019 | $0.0062 |
| R2 | $0.000 | $0.000 | $0.000 | $0.000 | $0.000 | $0.000 |
| R3 | $0.123 | $0.039 | $0.0079 | $0.317 | $0.063 | $0.021 |
| R4 | $0.161 | $0.049 | $0.0097 | $0.433 | $0.087 | $0.029 |
| R5 | $0.404 | $0.133 | $0.027 | $1.021 | $0.204 | $0.068 |

### Per-shape (D1–D5) — gpt-5.5 only

D2 (functional pass = deferred external-issue scorer) and D3/D4
(judge-scored prose) contribute None to the pass counter. Below the
`pass/n` column is the **functional-pass denominator** (only D1 and
D5 are functionally scored; D2/D3/D4 show `—/4`).

| Shape | Route | n | $/row | $/correct | pass/n |
|---|---|---:|---:|---:|---:|
| D1 | R1 | 4 | $0.030 | $0.061 | 2/4 |
| D1 | R2 | 4 | $0.000 | — | 0/4 |
| D1 | R3 | 4 | $0.098 | $0.195 | 2/4 |
| D1 | R4 | 4 | $0.118 | $0.473 | 1/4 |
| D1 | R5 | 4 | $0.432 | $1.727 | 1/4 |
| D2 | R1 | 4 | $0.041 | — | —/4 (deferred) |
| D2 | R2 | 4 | $0.000 | — | —/4 (deferred) |
| D2 | R3 | 4 | $0.128 | — | —/4 (deferred) |
| D2 | R4 | 4 | $0.171 | — | —/4 (deferred) |
| D2 | R5 | 4 | $0.339 | — | —/4 (deferred) |
| D3 | R1 | 4 | $0.035 | — | —/4 (judge-only) |
| D3 | R2 | 4 | $0.000 | — | —/4 (judge-only) |
| D3 | R3 | 4 | $0.151 | — | —/4 (judge-only) |
| D3 | R4 | 4 | $0.164 | — | —/4 (judge-only) |
| D3 | R5 | 4 | $0.404 | — | —/4 (judge-only) |
| D4 | R1 | 4 | $0.086 | — | —/4 (judge-only) |
| D4 | R2 | 4 | $0.000 | — | —/4 (judge-only) |
| D4 | R3 | 4 | $0.407 | — | —/4 (judge-only) |
| D4 | R4 | 4 | $0.197 | — | —/4 (judge-only) |
| D4 | R5 | 4 | $0.436 | — | —/4 (judge-only) |
| D5 | R1 | 4 | $0.016 | $0.021 | 3/4 |
| D5 | R2 | 4 | $0.000 | — | 0/4 |
| D5 | R3 | 4 | $0.071 | $0.094 | 3/4 |
| D5 | R4 | 4 | $0.073 | $0.097 | 3/4 |
| D5 | R5 | 4 | $0.423 | $0.564 | 3/4 |

---

## Full decision matrix

See `results/runs/07-v3-devstral-all-routes/decision_matrix.md` for
the v3 4×5 grids with pass-rate medians. Full numbers in
`results/runs/07-v3-devstral-all-routes/aggregate.json`. Historical
v1+v2 200-row matrix preserved at `results/reprice/decision_matrix.md`.

---

## When does the winner change?

Sorting routes by $/correct on **SWE-bench (Category B)** — original
MVP dataset, R4-only hybrid sample:

| Scenario | cheapest | 2nd | 3rd |
|---|---|---|---|
| gpt-5.5 | R1 ($0.42) | R4 ($0.56) | R3 ($0.72) |
| gpt-5 | R1 ($0.14) | R4 ($0.18) | R3 ($0.23) |
| gpt-5-mini | R1 ($0.028) | R4 ($0.035) | R3 ($0.047) |
| claude-opus-4.7 | R1 ($0.80) | R4 ($1.22) | R3 ($1.55) |
| claude-sonnet-4.6 | R1 ($0.18) | R4 ($0.24) | R3 ($0.32) |
| claude-haiku-4.5 | R1 ($0.06) | R4 ($0.08) | R3 ($0.10) |

**Under every scenario R1 is the cheapest per correct answer on B.**
R4 consistently sits in the middle. R3 is always the most expensive.

### v3 re-sort on B + D — with R5 included

Sorting routes by $/correct on **Category D** (real-developer
tasks):

| Scenario | cheapest | 2nd | 3rd | 4th |
|---|---|---|---|---|
| gpt-5.5 | **R1 ($0.17)** | R3 ($0.69) | R4 ($0.78) | R5 ($2.04) |
| gpt-5 | **R1 ($0.055)** | R3 ($0.22) | R4 ($0.24) | R5 ($0.67) |
| gpt-5-mini | **R1 ($0.011)** | R3 ($0.045) | R4 ($0.048) | R5 ($0.13) |
| claude-opus-4.7 | **R1 ($0.45)** | R3 ($1.78) | R4 ($2.05) | R5 ($5.18) |
| claude-sonnet-4.6 | **R1 ($0.089)** | R3 ($0.36) | R4 ($0.41) | R5 ($1.04) |
| claude-haiku-4.5 | **R1 ($0.030)** | R3 ($0.12) | R4 ($0.14) | R5 ($0.35) |

R5 is dominated in every cell. R3 has a quality-ceiling argument on
the D3/D4 judge-scored rows (see `decision_matrix.md`) but the
$/correct column doesn't credit it — because the judge-only rows
are excluded from the functional pass denominator.

**So why would anyone use R4 or R5?** Same caveat as before:
$/correct ignores pass *count* and the value of avoiding failures.
On v3 the case is weaker than on v1 — R4 ties R1 at 3/10 on B,
loses to R1 on D, and R5 loses everywhere. The pass-count argument
that justified R4 on the original 30-row sample has not replicated.

---

## Token-economics recap (from Appendix C)

See `reports/TOKEN_BUDGET.md` for the v3 breakdown. The one-line
summary:

> R3 consumes 1.02M tokens across 50 v3 rows; **65%** routed local.
> R4 consumes 640K tokens across 50 v3 rows; **13%** routed local
> (median 87% cloud — the smallest local-routed share of any hybrid).
> R5 consumes **1.88M tokens across 50 v3 rows; 50% local on
> median**, but in absolute terms uses more tokens than R3 and R4
> combined. R2 is the $0 baseline. R1 is the $0.109/row baseline on
> gpt-5.5 (MVP) and $0.035/row on category D (v3).
