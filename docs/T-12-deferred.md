# T-12 deferred — honest note

_Part of the mono-repo-reorg plan execution; deferred during overnight run._

## What T-12 was supposed to do

Run R4 Minion on SWE-bench Verified twice more with RNG seeds 7 and 13
(runs 07-r4-seed7 and 08-r4-seed13), giving three-sample CIs on the
headline 4/10 vs R1's 3/10.

## Why it's deferred

Producing *honest* CIs from a re-run requires the seed to actually
influence the model's output. That means threading a seed into:

1. **OpenAI's `chat.completions` call** — supported via the ``seed``
   parameter, but requires modifying ``minions.clients.openai.OpenAIClient``
   to accept and forward it. The vendored Minion library doesn't take
   a seed argument anywhere in its ``__call__`` chain.
2. **Ollama's generation** — supported via ``options.seed`` in the
   Ollama REST API, but exposed only through the ``ollama`` Python SDK
   that Minion doesn't use (it uses OpenAI-shape calls to the router,
   which forwards to Ollama — the router strips all non-OpenAI fields).
3. **Minion's own internal RNG** — the protocol has no explicit RNG;
   the only source of variation is model temperature + token sampling.

Without (1)+(2), invoking the same sweep with a different ``random.seed()``
would produce bit-identical outputs (LLM inference is the only
stochastic step and it doesn't see our RNG). Running it anyway would
waste ~$3 of API budget for no added signal.

## What this plan ships instead

- The MVP REPORT's N=10 caveat stays open, explicitly flagged in the
  T-18 article.
- The Wilson 95% CI in the decision matrix (T-17, landed) honestly
  reflects N=10 variance *within the single seed-42 run* — it's
  already pessimistic.
- A follow-up plan (post-publication) implements seed threading
  through the OpenAI + Ollama clients and re-runs T-12.

## Files that would implement T-12 in a future iteration

- ``vendor/minions/minions/clients/openai.py`` — add ``seed`` kwarg to
  ``__init__`` and forward into every ``chat.completions.create`` call.
- ``router/server.mjs`` — preserve ``seed`` from the request body
  instead of filtering it out as a non-OpenAI field. (Check current
  filter behaviour first.)
- ``src/hybrid_coding_eval/runners/r4_minion.py`` — accept ``seed``
  kwarg on ``run()``, thread through to both client constructors.
- ``src/hybrid_coding_eval/core/experiment.py::run_pair()`` — thread
  ``seed`` through from ``BenchConfig.benchmark.seeds``.
- ``src/hybrid_coding_eval/cli/run.py`` — iterate over ``seeds`` list
  when the config has more than one, producing one row per (task, route, seed).
