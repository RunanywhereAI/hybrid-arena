# Token budget — where the tokens went

Generated from `results/raw.jsonl` at `2026-05-10T20:31:02Z`; cost is derived from tokens at read time using `configs/pricing/pricing_tables.json`.

Every row below is one `(task_id, route, variant)` run from the committed dataset. `cloud_fraction` is the share of prompt+completion tokens that left the laptop; local tokens cost $0 by construction. `cost_<scenario>_usd` is re-derived from the stored tokens against the pinned pricing table, so the same dataset can be re-priced under any scenario without re-running inference.

**Scenarios surfaced:** `openai-gpt5.5`, `openai-gpt5`, `openai-gpt5-mini`, `anthropic-claude-opus-4.7`, `anthropic-claude-sonnet-4.6`, `anthropic-claude-haiku-4.5`

## 1. Top-10 most-local-efficient passing tasks

Rows where `functional_pass = True`, sorted by `cloud_fraction` ascending (ties broken by fewer total tokens). These are the tasks the laptop actually solved mostly on its own — the routing wins.

| task_id | route | variant | cat | cloud_frac | tokens | $openai-gpt5.5 | $openai-gpt5 | $openai-gpt5-mini | $anthropic-claude-opus-4.7 | $anthropic-claude-sonnet-4.6 | $anthropic-claude-haiku-4.5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval-plus/HumanEval_15 | R2 | v1-qwen | A | 0% | 191 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| humaneval-plus/HumanEval_13 | R2 | v1-qwen | A | 0% | 205 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| humaneval-plus/HumanEval_121 | R2 | v1-qwen | A | 0% | 265 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| swebench-verified/django__django-11179 | R2 | v1-qwen | B | 0% | 304 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| humaneval-plus/HumanEval_77 | R2 | v1-qwen | A | 0% | 312 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| humaneval-plus/HumanEval_161 | R2 | v1-qwen | A | 0% | 319 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| humaneval-plus/HumanEval_154 | R2 | v1-qwen | A | 0% | 345 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| humaneval-plus/HumanEval_103 | R2 | v1-qwen | A | 0% | 395 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| humaneval-plus/HumanEval_99 | R2 | v1-qwen | A | 0% | 406 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| humaneval-plus/HumanEval_118 | R2 | v1-qwen | A | 0% | 547 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |

## 2. Per-(category, route) median table

One row per `(category, route)` cell. `median_cloud_frac` is the median across the runs in that cell; `pass_rate` ignores rows where `functional_pass` is null; each `med_$<scenario>` column is the median per-run cost under that scenario.

| cat | route | n_rows | median_cloud_frac | pass_rate | med_$openai-gpt5.5 | med_$openai-gpt5 | med_$openai-gpt5-mini | med_$anthropic-claude-opus-4.7 | med_$anthropic-claude-sonnet-4.6 | med_$anthropic-claude-haiku-4.5 |
|---|---|---|---|---|---|---|---|---|---|---|
| A | R1 | 10 | 100% | 100% | $0.0106 | $0.0035 | $0.0007 | $0.0269 | $0.0054 | $0.0018 |
| A | R2 | 20 | 0% | 95% | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| A | R3 | 20 | 39% | 90% | $0.0327 | $0.0102 | $0.0020 | $0.0861 | $0.0172 | $0.0057 |
| B | R1 | 10 | 100% | 30% | $0.1260 | $0.0419 | $0.0084 | $0.3155 | $0.0631 | $0.0210 |
| B | R2 | 20 | 0% | 5% | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| B | R3 | 20 | 36% | 20% | $0.1439 | $0.0465 | $0.0093 | $0.3688 | $0.0738 | $0.0246 |
| B | R4 | 10 | 89% | 40% | $0.2224 | $0.0701 | $0.0140 | $0.5801 | $0.1160 | $0.0387 |
| C | R1 | 20 | 100% | 29% | $0.1176 | $0.0391 | $0.0078 | $0.2947 | $0.0589 | $0.0196 |
| C | R2 | 20 | 0% | 20% | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0000 |
| C | R3 | 30 | 49% | 26% | $0.2430 | $0.0778 | $0.0156 | $0.6271 | $0.1254 | $0.0418 |

## 3. Decision matrix — cloud_fraction bands (costed under `openai-gpt5.5`)

Bucket every run by its `cloud_fraction` into 4 equal-width bands, then report how many tasks land in each band, their pass rate, and the mean USD cost under the primary pricing scenario.

| cloud_fraction band | n_tasks | pass_rate | mean $openai-gpt5.5/task |
|---|---:|---:|---:|
| 0-25% | 64 | 43% | $0.0010 |
| 25-50% | 45 | 44% | $0.1045 |
| 50-75% | 17 | 60% | $0.2979 |
| 75-100% | 54 | 47% | $0.1622 |

---

_n_rows=180 | scenarios=6 | derivation: tokens × pinned pricing_tables.json (sha256 pinned in `hybrid_coding_eval.core.pricing.PRICING_META`)._
