# Run 06 — R4 Minion on Category C (BigCodeBench-Hard + custom_arch)

## Headline

**R4 on Category C: weak on functional C-tasks, unscored on prose C-tasks.**

| source | rows | pass / score |
|---|:-:|:-:|
| bigcodebench-hard | 5 | **1/5 PASS** |
| custom-arch | 5 | unscored — needs LLM-judge (T-14 will re-judge in a triple-judge audit) |

Reference (MVP dataset):
 - R1 cloud-only on BigCodeBench-Hard: 2/5
 - R3-devstral on BigCodeBench-Hard: 2/5
 - R4 (this run) on BigCodeBench-Hard: 1/5 — **under-performs**

This matches the plan's guardrail expectation: Minion's Q&A protocol
was designed for extractive-style SWE tasks where the worker reads a
long context and the supervisor asks targeted questions. BigCodeBench
tasks are library-intensive implementations where the supervisor's
questions don't buy much — the worker's local model (devstral:24b)
would benefit from more direct context and less round-trip.

**No ``error=protocol-mismatch`` rows** — every task ran to completion
and produced output. The Minion loop *does* produce prose for the
custom-arch tasks; whether that prose is judge-equivalent to R1/R3
outputs is what T-14 will tell us.

## BigCodeBench-Hard failures

| task | outcome | notes |
|---|---|---|
| BigCodeBench/214 | FAIL | generation syntactically valid, semantically wrong |
| BigCodeBench/82  | FAIL | same pattern |
| BigCodeBench/530 | **PASS** | only winner |
| BigCodeBench/501 | FAIL |  |
| BigCodeBench/458 | FAIL |  |

Worth noting: these tasks import specific third-party libraries. The
supervisor's question-ask format doesn't help the worker decide
which library API to call. Cloud supervisor can see the task spec
but not the worker's intermediate attempts.

## Token economics

- total cloud tokens: **98,563**
- total local tokens: **14,416**
- local share: **13%** — much lower than Cat B (where Minion shines)
- wall clock total: **1068s** ≈ 18 min, median 195s for custom_arch and 60s for bigcodebench

custom-arch rows consume 3× more tokens per task than bigcodebench
because the prose deliverable runs longer.

## custom-arch — judge-pending

The 5 rows have output but no composite score. T-14 (triple-judge
robustness audit) will score these against R1/R3 pairs from the MVP
dataset, giving the first honest "does R4 match R3 on architectural
prose?" number.

## Config

- variant: `r4-catC`
- cloud: gpt-5.5
- local: devstral:24b
- router strategy: heuristic (pinned to always-cloud/always-local by R4)

## Next

- T-12 runs extra seeds on Cat B to give CIs on R4's SWE-bench headline
- T-14 scores these custom-arch rows with the triple-judge audit
