# Appendix B — multi-scenario decision matrix

This appendix re-prices the full 200-row dataset under six official
per-million-token cloud-pricing scenarios. Cost is derived at read
time from `configs/pricing/pricing_tables.json` (SHA256 pinned); no
inference is re-run. The source table is `results/reprice/decision_matrix.md`
and the canonical raw data is `results/reprice/cost_by_scenario.csv`.

## How to read this

Each scenario has a 3×4 grid of (category × route) cells. Every cell
carries:

- **pass rate** with Wilson 95% CI — honest at small N, bounded to
  [0, 1], asymmetric.
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

---

## Full decision matrix

See `results/reprice/decision_matrix.md` for the 6 × 3×4 grids with
pass-rate CIs. The full JSON dump (for programmatic consumers) is at
`results/reprice/decision_matrix.json`.

---

## When does the winner change?

Sorting routes by $/correct on SWE-bench:

| Scenario | cheapest | 2nd | 3rd |
|---|---|---|---|
| gpt-5.5 | R1 ($0.42) | R4 ($0.56) | R3 ($0.72) |
| gpt-5 | R1 ($0.14) | R4 ($0.18) | R3 ($0.23) |
| gpt-5-mini | R1 ($0.028) | R4 ($0.035) | R3 ($0.047) |
| claude-opus-4.7 | R1 ($0.80) | R4 ($1.22) | R3 ($1.55) |
| claude-sonnet-4.6 | R1 ($0.18) | R4 ($0.24) | R3 ($0.32) |
| claude-haiku-4.5 | R1 ($0.06) | R4 ($0.08) | R3 ($0.10) |

**Under every scenario R1 is the cheapest per correct answer.** R4
consistently sits in the middle. R3 is always the most expensive.

**So why would anyone use R4?** Because its *pass rate* is higher
(4/10 vs R1's 3/10 on SWE-bench). If your workload values pass count
over cost-per-correct — for example you're paying a senior engineer
$100/h to review outputs and you'd rather have 4 correct patches than
3 — R4 is strictly better in that frame. That ROI argument isn't in
the $/correct column because $/correct ignores the cost of a failed
solution.

---

## Token-economics recap (from Appendix C)

See `results/reprice/token_share.md` for the full breakdown. The
one-line summary:

> R3 consumes 1.46M tokens across 69 rows; 51% routed local. R4
> consumes 321K tokens across 30 rows; 12% routed local. R2 is the
> $0 baseline. R1 is the $0.109/row baseline on gpt-5.5.
