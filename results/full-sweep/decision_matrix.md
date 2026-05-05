# Decision matrix — category × route

_Generated from `results/full-sweep/raw.jsonl` — 31 rows, default pricing: **openai-gpt5.5**._

_Bounded-ARQGC cost cap: **$0.1985** (p90 of R1's per-task cost × task count)._

## Quality × cost × wall time

| Category | R1 quality | R2 quality | R3 quality | R1 cost | R2 cost | R3 cost | R1 wall | R2 wall | R3 wall |
|---|---|---|---|---|---|---|---|---|---|
| A | 1.00 (μ 1.00) | 1.00 (μ 1.00) | 1.00 (μ 0.80) | $0.0106 (Σ $0.1028) | $0.0000 (Σ $0.0000) | $0.0327 (Σ $0.3635) | 4,680 ms | 17,468 ms | 78,237 ms |
| B | — (μ —) | — (μ —) | — (μ —) | $0.2123 (Σ $0.2123) | — | — | 96,680 ms | — | — |

## Bounded-ARQGC — area under quality-cost curve

| Category | R1 | R2 | R3 | Recommended |
|---|---|---|---|---|
| A | 0.518 | 0.000 | 0.790 | R3 |
| B | 0.000 | — | — | R1 |
| **all** | 0.518 | 0.000 | 0.790 | — |

## Alternative pricing scenarios — median cost per task

| Category/Route | openai-gpt5.5 | openai-gpt5 | openai-gpt5-mini | anthropic-claude-opus-4.7 | anthropic-claude-sonnet-4.6 |
|---|---|---|---|---|---|
| A/R1 | $0.0106 | $0.00347 | $0.00069 | $0.0269 | $0.00538 |
| A/R2 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| A/R3 | $0.0327 | $0.0102 | $0.00204 | $0.0861 | $0.0172 |
| B/R1 | $0.2123 | $0.0706 | $0.0141 | $0.5316 | $0.1063 |
| B/R2 | — | — | — | — | — |
| B/R3 | — | — | — | — | — |

## Interpretation

- **R1** wins on categories B (highest ARQGC under the $0.1985 budget).
- **R3** wins on categories A (highest ARQGC under the $0.1985 budget).

### Token totals per route (across all tasks)

| Route | Cloud prompt | Cloud completion | Local prompt | Local completion |
|---|---:|---:|---:|---:|
| R1 | 1,846 | 10,194 | 0 | 0 |
| R2 | 0 | 0 | 1,599 | 1,973 |
| R3 | 17,495 | 9,201 | 33,656 | 9,785 |
