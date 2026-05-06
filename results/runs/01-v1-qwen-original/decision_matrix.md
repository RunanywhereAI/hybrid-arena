# Decision matrix — category × route

_Generated from `results/full-sweep/raw.jsonl` — 90 rows, default pricing: **openai-gpt5.5**._

_Bounded-ARQGC cost cap: **$7.245** (p90 of R1's per-task cost × task count)._

## Quality × cost × wall time

| Category | R1 quality | R2 quality | R3 quality | R1 cost | R2 cost | R3 cost | R1 wall | R2 wall | R3 wall |
|---|---|---|---|---|---|---|---|---|---|
| A | 1.00 (μ 1.00) | 1.00 (μ 1.00) | 1.00 (μ 0.80) | $0.0106 (Σ $0.1028) | $0.0000 (Σ $0.0000) | $0.0327 (Σ $0.3635) | 4,680 ms | 17,468 ms | 78,237 ms |
| B | 0.00 (μ 0.30) | 0.00 (μ 0.10) | 0.00 (μ 0.10) | $0.1260 (Σ $1.347) | $0.0000 (Σ $0.0000) | $0.1462 (Σ $1.442) | 67,466 ms | 21,148 ms | 313,810 ms |
| C | 0.71 (μ 0.51) | 0.57 (μ 0.64) | 0.00 (μ 0.29) | $0.1431 (Σ $1.369) | $0.0000 (Σ $0.0000) | $0.2064 (Σ $2.225) | 77,044 ms | 133,165 ms | 467,616 ms |

## Bounded-ARQGC — area under quality-cost curve

| Category | R1 | R2 | R3 | Recommended |
|---|---|---|---|---|
| A | 0.014 | 0.000 | 0.044 | R3 |
| B | 0.030 | 0.000 | 0.009 | R1 |
| C | 0.043 | 0.000 | 0.026 | R1 |
| **all** | 0.087 | 0.000 | 0.079 | — |

## Alternative pricing scenarios — median cost per task

| Category/Route | openai-gpt5.5 | openai-gpt5 | openai-gpt5-mini | anthropic-claude-opus-4.7 | anthropic-claude-sonnet-4.6 |
|---|---|---|---|---|---|
| A/R1 | $0.0106 | $0.00347 | $0.00069 | $0.0269 | $0.00538 |
| A/R2 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| A/R3 | $0.0327 | $0.0102 | $0.00204 | $0.0861 | $0.0172 |
| B/R1 | $0.1260 | $0.0419 | $0.00839 | $0.3155 | $0.0631 |
| B/R2 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| B/R3 | $0.1462 | $0.0467 | $0.00934 | $0.3779 | $0.0756 |
| C/R1 | $0.1431 | $0.0476 | $0.00952 | $0.3583 | $0.0717 |
| C/R2 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| C/R3 | $0.2064 | $0.0653 | $0.0131 | $0.5372 | $0.1074 |

## Interpretation

- **R1** wins on categories B, C (highest ARQGC under the $7.245 budget).
- **R3** wins on categories A (highest ARQGC under the $7.245 budget).

### Token totals per route (across all tasks)

| Route | Cloud prompt | Cloud completion | Local prompt | Local completion |
|---|---:|---:|---:|---:|
| R1 | 7,037 | 92,774 | 0 | 0 |
| R2 | 0 | 0 | 7,708 | 20,842 |
| R3 | 159,700 | 107,748 | 234,838 | 89,340 |
