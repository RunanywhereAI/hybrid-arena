# Decision table — per (task_shape × route) cell

_Generated from `results/runs/07-v3-devstral-all-routes/raw.jsonl` (250 rows) and `reports/token_budget.csv`. Primary pricing scenario: **openai-gpt5.5** (cheap floor: **openai-gpt5-mini**). Shapes derived per `bin/judge_robust_d3_d4.py:_JudgeFacade.shape`._

**Pass-rate semantics.** Where a functional scorer exists (A-he, B-swe, C-bcb, D1, D5), `pass_rate` is the share of `functional_pass=True` rows. Judge-scored shapes (C-arch, D3, D4) have no functional pass; their cells use `composite >= 0.5` as a pass proxy and are flagged with `*`. **Pass rate for D2 is `None/N` by design** — D2 covers external GitHub-issue tasks whose functional scorer is not implemented yet, so the dataset deliberately holds `functional_pass=null` and `composite=null` there. Treat D2 cost/cloud-fraction columns as tokens/latency observations only, not quality signals.

## Category A — HumanEval+ (functional, easy)

| shape | route | N | pass_rate | med cloud_frac | med $ gpt-5.5 | med $ gpt-5-mini | med wall ms |
|---|---|---:|---|---:|---:|---:|---:|
| A-he | R1 | 10 | 100% (10/10) | 100% | $0.0119 | $0.0008 | 5,364 |
| A-he | R2 | 10 | 90% (9/10) | 0% | $0.0000 | $0.0000 | 5,244 |
| A-he | R3 | 10 | 100% (10/10) | 37% | $0.0380 | $0.0024 | 57,524 |
| A-he | R4 | 10 | 100% (10/10) | 90% | $0.0659 | $0.0041 | 37,345 |
| A-he | R5 | 10 | 40% (4/10) | 50% | $0.2488 | $0.0162 | 262,695 |

## Category B — SWE-bench Verified (functional, hard)

| shape | route | N | pass_rate | med cloud_frac | med $ gpt-5.5 | med $ gpt-5-mini | med wall ms |
|---|---|---:|---|---:|---:|---:|---:|
| B-swe | R1 | 10 | 30% (3/10) | 100% | $0.1058 | $0.0070 | 61,586 |
| B-swe | R2 | 10 | 0% (0/10) | 0% | $0.0000 | $0.0000 | 9,700 |
| B-swe | R3 | 10 | 30% (3/10) | 34% | $0.1369 | $0.0088 | 166,103 |
| B-swe | R4 | 10 | 30% (3/10) | 86% | $0.2025 | $0.0127 | 139,083 |
| B-swe | R5 | 10 | 0% (0/10) | 53% | $0.3902 | $0.0256 | 381,303 |

## Category C — BigCodeBench-hard + custom-arch (mixed)

| shape | route | N | pass_rate | med cloud_frac | med $ gpt-5.5 | med $ gpt-5-mini | med wall ms |
|---|---|---:|---|---:|---:|---:|---:|
| C-bcb | R1 | 5 | 20% (1/5) | 100% | $0.0433 | $0.0029 | 21,998 |
| C-bcb | R2 | 5 | 20% (1/5) | 0% | $0.0000 | $0.0000 | 22,159 |
| C-bcb | R3 | 5 | 0% (0/5) | 41% | $0.0862 | $0.0054 | 77,120 |
| C-bcb | R4 | 5 | 0% (0/5) | 89% | $0.0906 | $0.0057 | 52,238 |
| C-bcb | R5 | 5 | 0% (0/5) | 50% | $0.4429 | $0.0286 | 645,402 |
| C-arch | R1 | 5 | 100%* | 100% | $0.2963 | $0.0197 | 180,594 |
| C-arch | R2 | 5 | 60%* | 0% | $0.0000 | $0.0000 | 47,568 |
| C-arch | R3 | 5 | 100%* | 70% | $0.4876 | $0.0316 | 523,641 |
| C-arch | R4 | 5 | 80%* | 89% | $0.1612 | $0.0104 | 119,873 |
| C-arch | R5 | 5 | 20%* | 53% | $0.4957 | $0.0325 | 876,316 |

## Category D — real-dev (synthetic + GitHub issues + refactor + review)

| shape | route | N | pass_rate | med cloud_frac | med $ gpt-5.5 | med $ gpt-5-mini | med wall ms |
|---|---|---:|---|---:|---:|---:|---:|
| D1 | R1 | 4 | 50% (2/4) | 100% | $0.0304 | $0.0018 | 12,940 |
| D1 | R2 | 4 | 0% (0/4) | 0% | $0.0000 | $0.0000 | 2,834 |
| D1 | R3 | 4 | 50% (2/4) | 31% | $0.0976 | $0.0062 | 127,042 |
| D1 | R4 | 4 | 25% (1/4) | 86% | $0.1183 | $0.0073 | 102,956 |
| D1 | R5 | 4 | 25% (1/4) | 46% | $0.4318 | $0.0280 | 582,035 |
| D2 | R1 | 4 | None/4 | 100% | $0.0409 | $0.0026 | 25,728 |
| D2 | R2 | 4 | None/4 | 0% | $0.0000 | $0.0000 | 7,795 |
| D2 | R3 | 4 | None/4 | 32% | $0.1282 | $0.0083 | 154,903 |
| D2 | R4 | 4 | None/4 | 86% | $0.1714 | $0.0111 | 130,993 |
| D2 | R5 | 4 | None/4 | 53% | $0.3387 | $0.0222 | 398,319 |
| D3 | R1 | 4 | 100%* | 100% | $0.0354 | $0.0022 | 13,667 |
| D3 | R2 | 4 | 0%* | 0% | $0.0000 | $0.0000 | 3,036 |
| D3 | R3 | 4 | 100%* | 37% | $0.1509 | $0.0097 | 219,453 |
| D3 | R4 | 4 | 100%* | 86% | $0.1637 | $0.0100 | 125,883 |
| D3 | R5 | 4 | 0%* | 55% | $0.4043 | $0.0266 | 461,580 |
| D4 | R1 | 4 | 100%* | 100% | $0.0861 | $0.0056 | 46,556 |
| D4 | R2 | 4 | 0%* | 0% | $0.0000 | $0.0000 | 19,088 |
| D4 | R3 | 4 | 50%* | 81% | $0.4067 | $0.0262 | 270,419 |
| D4 | R4 | 4 | 50%* | 83% | $0.1968 | $0.0120 | 158,609 |
| D4 | R5 | 4 | 0%* | 50% | $0.4355 | $0.0283 | 597,710 |
| D5 | R1 | 4 | 75% (3/4) | 100% | $0.0158 | $0.0010 | 12,026 |
| D5 | R2 | 4 | 0% (0/4) | 0% | $0.0000 | $0.0000 | 13,200 |
| D5 | R3 | 4 | 75% (3/4) | 33% | $0.0706 | $0.0045 | 91,331 |
| D5 | R4 | 4 | 75% (3/4) | 88% | $0.0729 | $0.0046 | 63,739 |
| D5 | R5 | 4 | 75% (3/4) | 45% | $0.4230 | $0.0273 | 750,461 |

---

_n_rows=250 | shapes=9 | routes=5 | pricing pinned via `configs/pricing/pricing_tables.json` (sha256 `adbf24618010…`). Cell values: median across the runs in that `(shape, route)` cell. `*` on a pass_rate means "composite ≥ 0.5" was used as the pass proxy (judge-scored shape with no functional scorer)._
