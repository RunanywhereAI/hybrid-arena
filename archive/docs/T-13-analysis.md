# T-13: prompt caching for R3-devstral — analysis (not a sweep)

_Part of the mono-repo-reorg plan; substitutes the originally-planned
sweep because the investigation showed the sweep would not produce
useful signal._

## What T-13 was supposed to test

Whether OpenAI's prompt caching, applied to the R3 architect pipeline's
planner + synth system prefixes, would flip R3-devstral from cost-parity
with R1 on SWE-bench (the finding load-bearing on the MVP REPORT) to
a Pareto cost win.

## What we found instead

### 1. OpenAI's cache threshold is 1024 tokens of matching prefix.

(See https://platform.openai.com/docs/guides/prompt-caching.) The cache
only triggers on prompt-prefix matches of **at least 1024 tokens**.

### 2. R3's static prefixes are well below 1024 tokens.

Measured on the current ``router/pipelines/architect/core.mjs``:

| prefix | content | approx tokens |
|---|---|---:|
| ``PLAN_SYSTEM`` | planner system prompt | ~400 |
| ``SYNTH_SYSTEM`` | synth system prompt | ~80 |
| ``executorSystem(prev)`` | per-step dynamic | ≤ ~250 |

None of these reach the cache threshold on their own, and the
`executorSystem` varies per step by design (it embeds the previous
step's output), so it would never hit the cache anyway.

### 3. Confirming from the committed data.

Across the 60 rows of ``results/runs/03-v2-devstral/raw.jsonl``, the
``tokens.cached`` column is **zero on every row**. The router + python
do forward ``prompt_tokens_details.cached_tokens`` correctly (verified
in ``router/pipelines/architect/core.mjs:263``), so the data-flow
isn't the problem — OpenAI simply isn't caching anything because the
prefix is too short.

### 4. What a real cache win would require.

Two credible paths, both non-trivial:

1. **Bulk up the system prefix to >1024 tokens** with something that
   genuinely helps — e.g. few-shot examples or a long coding-standards
   preamble. Changes the evaluation's meaning: we'd no longer be
   measuring "R3 with the MVP pipeline" but "R3 with a beefier prompt".
2. **Switch the cloud leg from OpenAI to Anthropic** and use
   explicit ``cache_control: ephemeral`` markers. The rest of the
   harness is OpenAI-SDK-shaped, so this is a whole-model-migration
   change, not a single-flag toggle.

Neither is in scope for this plan's publication goal.

## What T-13 ships

- Honest record (this file) that prompt caching would not change the
  R3 SWE-bench cost-parity finding on the current pipeline.
- A one-line note in the article (T-18) pointing at this document.
- No new sweep; no API spend.

## How to actually enable prompt caching later

1. Extend ``PLAN_SYSTEM`` with a 1500-token preamble (e.g., worked
   example of decomposition + a style guide).
2. Verify token count via ``tiktoken.encoding_for_model("gpt-5.5").encode(prompt)``.
3. Run ``./bench run --config configs/variants/09-r3-cached-devstral.yaml``.
4. Check ``.venv/bin/python -c "import json; print(sum(1 for l in open('results/runs/09-r3-cached/raw.jsonl') if json.loads(l)['tokens'].get('cached', 0) > 0))"`` — expect >0 on iteration N+1 within the same hour.
