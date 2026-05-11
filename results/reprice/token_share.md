# Token-economics split — where the dollars went (T-16)

Totals across **every row** in the committed dataset — both the MVP 180-row sweep (`results/raw.jsonl`) and every post-reorg run under `results/runs/NN-*/raw.jsonl`.

Dollar columns priced under `openai-gpt5.5` using `configs/pricing/pricing_tables.json`. Local tokens cost **$0** by construction (laptop electricity / hardware amortisation excluded).

| route | cat | N | Σ cloud tokens | Σ local tokens | routed local | Σ $ cost | $ / row |
|---|---|---:|---:|---:|---:|---:|---:|
| **R1** | A | 10 | 4,630 | 0 | 0% | $0.1028 | $0.0103 |
| **R1** | B | 10 | 47,108 | 0 | 0% | $1.3468 | $0.1347 |
| **R1** | C | 20 | 102,063 | 0 | 0% | $2.9151 | $0.1458 |
| **R2** | A | 20 | 0 | 18,717 | 100% | $0.0000 | $0.0000 |
| **R2** | B | 20 | 0 | 22,972 | 100% | $0.0000 | $0.0000 |
| **R2** | C | 20 | 0 | 44,928 | 100% | $0.0000 | $0.0000 |
| **R3** | A | 20 | 51,499 | 79,145 | 61% | $0.7183 | $0.0359 |
| **R3** | B | 20 | 175,593 | 300,091 | 63% | $3.1348 | $0.1567 |
| **R3** | C | 29 | 488,056 | 368,490 | 43% | $8.3458 | $0.2878 |
| **R4** | A | 10 | 47,034 | 5,390 | 10% | $0.6531 | $0.0653 |
| **R4** | B | 10 | 135,281 | 20,125 | 13% | $2.0262 | $0.2026 |
| **R4** | C | 10 | 98,563 | 14,416 | 13% | $1.5158 | $0.1516 |

### Per-route totals (across all categories)

| route | N | Σ cloud tokens | Σ local tokens | routed local | Σ $ cost |
|---|---:|---:|---:|---:|---:|
| **R1** | 40 | 153,801 | 0 | 0% | $4.3647 |
| **R2** | 60 | 0 | 86,617 | 100% | $0.0000 |
| **R3** | 69 | 715,148 | 747,726 | 51% | $12.1990 |
| **R4** | 30 | 280,878 | 39,931 | 12% | $4.1951 |

### What to read from this

- R1 rows are pure cloud (local = 0). Any nonzero local on an R1 row would be a routing bug.
- R2 rows are pure local (cloud = 0). The dollar cost column for R2 is always $0 under every scenario — the cost baseline.
- R3 rows split planner+synth (cloud) from executor steps (mostly local when the heuristic sends a step there). The *routed local* percentage is R3's ability to offload — 100% means every step went local, 0% means every step went cloud.
- R4 rows put the supervisor in the cloud and the worker on the local model. The routed-local percentage grows with context size because the worker does most of the reading.
