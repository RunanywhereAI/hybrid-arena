# Hybrid local/cloud routing for coding agents — what actually happens when you try it on real projects

> *Three real coding tasks, run twice each — once against `gpt-5.5` directly, once against a hybrid architecture that decomposes the task and routes each step to either a local model on the laptop (`qwen3.6:27b-coding-mxfp8` via Ollama) or to the cloud. Honest numbers, including where the hybrid approach is **not** worth it.*

This is a build report, not a marketing piece. Some of the findings are surprising and a few are uncomfortable: the headline cost-saving number you'd expect (hybrid saves a lot vs cloud) is true on the right comparison and false on the wrong one. The article walks through both.

---

## TL;DR

| | cloud-only single-shot | hybrid architect mode | hybrid vs same-plan all-cloud baseline |
|---|---|---|---|
| **exp 1 — wordcount CLI** | $0.059 in 26 s | $0.190 in 15 m 13 s | **62 % cheaper** vs $0.505 baseline |
| **exp 2 — todo REST API** | $0.067 in 24 s | $0.134 in 20 m 20 s | **68 % cheaper** vs $0.422 baseline |
| **exp 3 — URL shortener** | $0.126 in 58 s | $0.163 in 18 m 04 s ⚠ | **63 % cheaper** vs $0.438 baseline |

⚠ exp 3's synth step finished but emitted no visible content (gpt-5.5 burned all 2,500 completion tokens on hidden reasoning). Per-step outputs were real working code; the stitched answer was empty. Worth its own subsection.

**Three findings up front:**

1. **For tasks `gpt-5.5` can complete in one shot, single-shot cloud is the cheapest and fastest path.** Decomposing into a multi-step plan multiplies prompt tokens ~100× because every step re-sends accumulated context. The "free" local steps don't make up for that overhead against single-shot cloud — across all three experiments, hybrid was 1.3–3.2× *more* expensive than just calling `gpt-5.5` once.
2. **Against the *same decomposition* run all-cloud, hybrid is decisively cheaper — 62–68 % across the three runs.** That's the comparison that matters for any agent that already needs multi-step orchestration (tool use, long-running plans, etc.). If you're going to decompose anyway, hybrid is the right way.
3. **The local model is way slower than cloud per token.** ~10 tok/s on M4 Max for a 27 B dense coder × ~10 sequential steps = 15–20 min runs vs 24–58 s for the same task in one cloud call. For interactive use this is unworkable; for batch / overnight / privacy-sensitive workflows it's a fine trade.

All numbers reproducible from `examples/run-comparison.mjs` against the proxy at `127.0.0.1:8787`. Raw artefacts under `examples/<id>/`.

---

## What the hybrid architecture actually is

Three layers, all in the [public companion repo](#) (link before publishing):

1. **An OpenAI-compatible HTTP proxy** running on `localhost:8787`. Looks like just-another-OpenAI-endpoint to whatever client you point at it (`opencode`, `curl`, your custom code, anything that speaks the OpenAI API). Internally it routes each request to either Ollama on `127.0.0.1:11434` or `api.openai.com` based on a strategy chosen by the model id (`router/heuristic`, `router/cascade`, etc.).
2. **Seven routing strategies** that decide local-vs-cloud per request:
   - `always-local`, `always-cloud` — controls
   - `rules` — hard-coded keyword + token-count thresholds
   - `heuristic` — weighted score across user-message tokens, code-block count, complexity keywords, tool count
   - `llm-classifier` — a tiny `qwen3:0.6b` model decides SIMPLE vs COMPLEX
   - `embedding-knn` — k=5 vote against a labelled corpus, embeddings via `nomic-embed-text`
   - `cascade` — heuristic when confident, llm-classifier as tie-breaker
3. **Architect mode** (`router/agentic/architect.mjs`) — a decomposed pipeline. The cloud model emits a structured JSON plan; each plan step then gets its own routing decision; a synthesizer stitches the step outputs back into one coherent answer. *This is the "per-subtask" granularity we tested in this article.*

For the experiments below, "hybrid" means architect mode with `router/always-cloud` as planner, `router/heuristic` as executor and synthesizer.

For the deeper architecture writeup, see `ROUTING_STRATEGIES.md` in the repo. The TL;DR is: per-turn routing is the easy win; per-subtask routing is more interesting but pays a context-replay tax.

---

## Setup

| | |
|---|---|
| **Hardware** | M4 Max, 64 GB RAM, macOS |
| **Local model** | `qwen3.6:27b-coding-mxfp8` (Qwen team's coding-tuned 27 B dense in mxfp8, 31 GB on disk, ~10 tok/s on M4 Max via Ollama, native `/api/chat` with `think:false`) |
| **Cloud model** | `gpt-5.5` (`gpt-5.5-2026-04-23` echoed in responses) |
| **Pricing source** | [models.dev](https://models.dev/api.json) (fetched 2026-04-27): `gpt-5.5` = **$5/M input, $30/M output, $0.50/M cached input** |
| **Local cost** | $0 — laptop hardware/electricity treated as free at the margin. The honest comparison is "what extra would I have paid the cloud provider", not "is it free physics" |
| **Methodology** | For each experiment: run the same prompt through (a) `router/always-cloud` single-shot to gpt-5.5, (b) architect mode with hybrid routing. Capture every chat-completion via the proxy's JSONL decision log. Manually compare outputs |

The runner script is `examples/run-comparison.mjs` (~250 lines, no external deps). Every artefact in this article lives under `examples/<id>/` for reproducibility.

---

## Experiment 1 — Wordcount CLI

> *Build a single-file Node `wordcount` utility plus a small Node test suite plus a README.*

Full prompt: `examples/01-wordcount-cli/prompt.txt`. Three deliverables expected — one source file, one test file, one README.

### Numbers

| | cost | wall time | calls (local / cloud) | prompt tokens | completion tokens |
|---|---:|---:|---:|---:|---:|
| **cloud-only** | **$0.059** | **26.5 s** | 1 / 1 | 205 | 1,942 (938 reasoning) |
| **hybrid (architect)** | **$0.190** | **15 m 13 s** | 8 / 2 | 22,847 | 13,030 (1,842 reasoning) |
| _hybrid all-cloud baseline (same plan)_ | _$0.505_ | — | 0 / 10 | 22,847 | 13,030 |

**Hybrid is 3.2× more expensive than single-shot cloud here.** It is **62 % cheaper than running the same architect-decomposition all-cloud.**

### Why

The architect produced a 9-step plan. Most steps stayed local (8 of 10 executor steps), saving the per-step cloud cost. But the plan + per-step context-replay drove total prompt tokens from **205 (single-shot) → 22,847 (hybrid)**, a 111× expansion. The synth step alone consumed 8,510 input tokens stitching together everything the executor produced.

Routing decisions for this experiment (full table in `examples/01-wordcount-cli/hybrid/run.md`):

```
0 planner          ☁ cloud   gpt-5.5                       20.4s    in=524    out=1579   $0.050
1 design   auto    🖥 local  qwen3.6:27b-coding-mxfp8       1m46s   in=435    out=1198   $0.000
2 edit     auto    ☁ cloud   gpt-5.5                       12.5s    in=709    out=803    $0.028
3 edit     auto    🖥 local  qwen3.6:27b-coding-mxfp8       1m20s   in=990    out=636    $0.000
4 edit     auto    🖥 local  qwen3.6:27b-coding-mxfp8       2m14s   in=1249   out=960    $0.000
5 edit     auto    🖥 local  qwen3.6:27b-coding-mxfp8       1m28s   in=1540   out=822    $0.000
6 edit     auto    🖥 local  qwen3.6:27b-coding-mxfp8       36.8s   in=1836   out=194    $0.000
7 test     local   🖥 local  qwen3.6:27b-coding-mxfp8       2m20s   in=2075   out=1500   $0.000
8 review   auto    🖥 local  qwen3.6:27b-coding-mxfp8       2m12s   in=2341   out=1500   $0.000
9 answer   auto    🖥 local  qwen3.6:27b-coding-mxfp8       2m09s   in=2638   out=1500   $0.000
Σ synth    —      ☁ cloud   gpt-5.5                       33.8s   in=8510   out=2338   $0.113
```

The `heuristic` strategy quite reasonably routed step 2 (an `edit` step on a slightly heavier prompt) cloud, every other executor step local, and the final synthesizer cloud (8.5 K input tokens — well above the heuristic's threshold for "do this carefully"). That last cloud synth call alone is **$0.113**, more than half of the hybrid run's total cost.

### Output quality

Both produced working code that satisfies the prompt. Differences are real but minor:

- **Cloud-only** factored the counting logic into a `countText()` function exported from the module — making `wordcount.test.js` test the function directly. Slightly more idiomatic.
- **Hybrid** wrote the counting inline in `main()`. The test suite has to spawn child processes to drive the CLI binary instead. Functional but more invasive tests.
- **Cloud-only** uses `Array.from(text).length` for character count (correct for unicode surrogate pairs). **Hybrid** uses `content.length` (off-by-some on rare unicode but fine for ASCII).

For "small developer utility" code review purposes both are acceptable. The cloud version is what you'd want to merge; the hybrid version is what you'd accept from a junior dev and lightly clean up.

Files: `examples/01-wordcount-cli/cloud-only/output.txt` and `examples/01-wordcount-cli/hybrid/output.txt`.

---

## Experiment 2 — Todo REST API

> *Express REST API with 5 endpoints (POST/GET/PATCH/DELETE), in-memory storage, validation, one happy-path test, README, package.json.*

Full prompt: `examples/02-todo-api/prompt.txt`. Five-file deliverable.

### Numbers

| | cost | wall time | calls (local / cloud) | prompt tokens | completion tokens |
|---|---:|---:|---:|---:|---:|
| **cloud-only** | **$0.067** | **24.1 s** | 1 / 1 | 314 | 2,172 (512 reasoning) |
| **hybrid (architect)** | **$0.134** | **20 m 20 s** | 10 / 1 | 24,385 | 10,006 (551 reasoning) |
| _hybrid all-cloud baseline_ | _$0.422_ | — | 0 / 11 | 24,385 | 10,006 |

**Hybrid is 2.0× more expensive than single-shot cloud here. 68 % cheaper than the same decomposition run all-cloud.**

### Routing

The planner generated a 10-step plan and **hint-tagged every executor step `local`** — it correctly identified this as a mostly-mechanical task. The heuristic agreed every time. Synth went cloud (the heuristic correctly identifies that 6,596-token input as "do this carefully").

```
0 planner          ☁ cloud   gpt-5.5                       17.8s    in=633    out=1548   $0.050
1 design   auto    🖥 local  qwen3.6:27b-coding-mxfp8       1m40s   in=493    out=1294   $0.000
2 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       23.8s   in=825    out=130    $0.000
3 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       1m30s   in=1023   out=614    $0.000
4 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       1m44s   in=1300   out=725    $0.000
5 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       1m25s   in=1607   out=394    $0.000
6 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       1m48s   in=1885   out=721    $0.000
7 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       1m59s   in=2083   out=746    $0.000
8 test     local   🖥 local  qwen3.6:27b-coding-mxfp8       2m35s   in=2394   out=329    $0.000
9 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       2m33s   in=2631   out=295    $0.000
10 answer  auto    🖥 local  qwen3.6:27b-coding-mxfp8       4m04s   in=2915   out=1500   $0.000
Σ synth    —      ☁ cloud   gpt-5.5                       20.1s   in=6596   out=1710   $0.084
```

Every cent of hybrid spend was the planner ($0.050) + synth ($0.084). The 10 executor steps and the bulk of the actual code-writing happened on the laptop.

### Output quality

Both produced functional Express APIs. Differences:

- **Cloud-only**'s test uses Node's built-in `node:test` runner with `fetch` against an ephemeral-port server. The hybrid output uses `supertest` (and even adds it as a `devDependency` in `package.json` — the prompt didn't ask for it). Both work; supertest is heavier but more idiomatic for many teams.
- **Cloud-only** validates `done` field type explicitly; **hybrid** silently coerces non-boolean `done` to `false`. Subtle but the cloud version is stricter (closer to the prompt's intent).
- **Cloud-only**'s response shapes match the prompt exactly. Hybrid added `.trim()` on title (a reasonable choice the prompt didn't specify) — useful in production but not asked for.

Verdict: both ship. The cloud version is what you'd merge unmodified; the hybrid version needs ~5 minutes of light cleanup. **Quality gap is real but small.**

Files: `examples/02-todo-api/cloud-only/output.txt` and `examples/02-todo-api/hybrid/output.txt`.

---

## Experiment 3 — Rate-limited URL shortener

> *Express + URL store + fixed-window-or-token-bucket rate limiter + tests + README with three design sections (data model, rate-limiting choice, production checklist).*

This was the hardest of the three: 5 files, real architectural choices to defend in prose, code that has to compose correctly across modules.

### Numbers

| | cost | wall time | calls (local / cloud) | prompt tokens | completion tokens |
|---|---:|---:|---:|---:|---:|
| **cloud-only** | **$0.126** | **57.5 s** | 1 / 1 | 465 | 4,120 (2,048 reasoning) |
| **hybrid (architect)** | **$0.163** | **18 m 04 s** | 9 / 1 | 22,617 | 10,814 (2,536 reasoning) |
| _hybrid all-cloud baseline_ | _$0.438_ | — | 0 / 10 | 22,617 | 10,814 |

**Hybrid only 1.3× more expensive than single-shot cloud — the smallest gap of the three.** 63 % cheaper vs same-plan all-cloud.

But there's a catch.

### The synth-blew-its-budget failure mode

The synth step received 6,662 prompt tokens (concatenation of all 9 step outputs), routed cloud (heuristic score 86 — well over threshold), and called gpt-5.5 with `max_tokens: 2500`. The model returned **2,500 reasoning tokens and 0 visible content tokens**. The architect's "final synthesised output" section in `hybrid/run.md` is empty.

This is a real failure mode of synth-style multi-step pipelines on aggressive reasoning models. gpt-5.5 decided it needed to think very hard before answering, and didn't leave itself enough budget to actually answer.

**The per-step outputs were real working code:**

```js
// step 1 of exp 3 (local, qwen3.6:27b-coding-mxfp8) — real output, abbreviated:
=== FILE: urlStore.js ===
const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
const CODE_LENGTH = 6;
const MAX_RETRIES = 5;
const store = new Map();
function generateCode() { /* … */ }
function create(url) {
  let retries = 0;
  while (retries < MAX_RETRIES) {
    const code = generateCode();
    if (!has(code)) { set(code, url); return { code }; }
    retries++;
  }
  throw new Error('Failed to generate a unique code after maximum retries');
}
module.exports = { set, get, has, create };
```

Every other step also produced sensible code. The intermediate work was good. The synthesizer just couldn't fit a stitched final answer in 2,500 visible tokens after gpt-5.5's reasoning ate the budget.

### Routing

```
0 planner          ☁ cloud   gpt-5.5                       20.1s    in=784    out=1690   $0.055
1 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       1m15s   in=651    out=92     $0.000
2 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       42.5s   in=877    out=325    $0.000
3 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       1m31s   in=1181   out=270    $0.000
4 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       2m00s   in=1505   out=487    $0.000
5 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       1m13s   in=1731   out=322    $0.000
6 edit     local   🖥 local  qwen3.6:27b-coding-mxfp8       2m06s   in=1953   out=628    $0.000
7 test     local   🖥 local  qwen3.6:27b-coding-mxfp8       3m09s   in=2124   out=1500   $0.000
8 review   auto    🖥 local  qwen3.6:27b-coding-mxfp8       2m36s   in=2458   out=1500   $0.000
9 answer   auto    🖥 local  qwen3.6:27b-coding-mxfp8       2m32s   in=2691   out=1500   $0.000
Σ synth    —      ☁ cloud   gpt-5.5                       38.5s   in=6662   out=2500*  $0.108  ⚠ all reasoning
```

The fix is mechanical (and noted in **Gaps** below): bump the synth `max_tokens` from 2,500 to 6,000–8,000, or use `gpt-5` (less reasoning-aggressive than `gpt-5.5`) for the synth step specifically. Architect-core can be configured per-phase.

### Output quality

**Cloud-only** produced a complete 5-file project including the README design discussion: data model rationale ("a single Map is fine for the demo, but for production swap in Redis with TTLs"), rate-limit choice ("fixed-window for simplicity; token bucket would be smoother under bursts but adds state"), and a production checklist. Real, substantive prose.

**Hybrid** produced 9 working code files and intermediate notes, but the synth's empty visible content means the final stitched answer is missing. To use the hybrid output you'd have to manually concatenate step outputs from `events.json` — workable for a demo, broken as a user experience.

**This is the case where hybrid is unambiguously worse than single-shot cloud — both on cost (1.3× more) AND on output usability (failed synth).**

Files: `examples/03-url-shortener/cloud-only/output.txt` and `examples/03-url-shortener/hybrid/events.json` for the per-step outputs.

---

## Cross-experiment findings

| | exp 1 wordcount | exp 2 todo API | exp 3 URL shortener |
|---|---:|---:|---:|
| cloud-only cost | $0.059 | $0.067 | $0.126 |
| hybrid cost | $0.190 | $0.134 | $0.163 |
| **hybrid / cloud ratio** | **3.2×** | **2.0×** | **1.3×** |
| cloud-only completion tokens | 1,942 | 2,172 | 4,120 |
| hybrid completion tokens | 13,030 | 10,006 | 10,814 |
| hybrid prompt-token expansion vs cloud | 111× | 78× | 49× |
| % of executor steps that stayed local | 8 of 9 | 10 of 10 | 9 of 9 |
| synth as fraction of hybrid cost | 59 % | 63 % | 66 % |

A few patterns jump out:

**1. The hybrid-vs-cloud-single ratio shrinks as the task gets bigger.** On a tiny task (exp 1) cloud-only's 1,942 completion tokens are cheap relative to the architect's expansion. On a more complex task (exp 3) cloud-only itself pays $0.126 and hybrid only adds $0.04 to that — because synth is roughly fixed-cost per task, and the executor is essentially free.

If we extrapolated, around the **5× task complexity** mark, hybrid would equal or beat cloud-only on cost. Worth running a fourth experiment at that scale.

**2. The heuristic correctly routed almost everything.** 27 of 28 executor steps across all three runs went local. That's the heuristic doing exactly what it should: planning routes cloud, synth routes cloud, mechanical executor steps route local.

**3. Synth dominates hybrid cost.** Across all three: 59 / 63 / 66 % of hybrid spend was the synth step alone. Every other call combined is ~1/3. Anything that reduces synth cost — prompt caching, smaller synth ceilings, skipping synth entirely on small plans — is the highest-leverage change.

**4. Local prompt-token explosion is the real tax.** Hybrid prompt tokens are 49–111× cloud-only's. This isn't a bug, it's a feature of the architect pattern — every step receives the original task plus prior step outputs as context. But it's the dominant cost driver, and the obvious place to optimise (per-step truncation, summarisation, or context-aware step prompts).

---

## Where hybrid actually wins, and where it doesn't

**Hybrid wins decisively when:**

- **You're going to decompose the task anyway.** Tool-using agents, long-running batch pipelines, anywhere a single cloud roundtrip can't carry the whole job. vs an all-cloud architect, hybrid is 60 %+ cheaper. Same quality, much lower bill.
- **You care about privacy.** Local steps never see the cloud. For trade-secret code or regulated data, that's the difference between "cannot use this technology" and "can".
- **You can tolerate latency.** Batch / overnight / "submit job, get result tomorrow morning" patterns are perfect for this — the per-token speed disadvantage doesn't matter when the wall clock isn't the budget.

**Hybrid loses when:**

- **The task fits in one cloud call.** Tested across all three experiments: single-shot cloud is the cost floor by 1.3–3.2×. Don't over-engineer.
- **You need real-time interaction.** 10 tok/s × 10 sequential steps = 15+ minutes. A user typing into a chat UI will give up.
- **The cloud model's reasoning behaviour kicks in mid-pipeline.** Exp 3 showed a real failure: a reasoning-model synth burning the entire visible-output budget on hidden thought. Mitigations exist but require thoughtful per-phase configuration.

**The honest TL;DR**: hybrid is a tool with a specific shape. Don't pitch it as a free lunch.

---

## Latency reality

The local model runs at **~10 tok/s on M4 Max** for `qwen3.6:27b-coding-mxfp8` (27 B dense in mxfp8, served via Ollama with `think:false`). gpt-5.5's effective wall-clock output rate including reasoning is roughly 50–80 tok/s.

Across three experiments:

| | cloud time | hybrid time | hybrid / cloud |
|---|---:|---:|---:|
| exp 1 | 26.5 s | 15 m 13 s | **34×** |
| exp 2 | 24.1 s | 20 m 20 s | **51×** |
| exp 3 | 57.5 s | 18 m 04 s | **19×** |

This is *the* trade-off of the hybrid architecture. The "no extra cloud spend" comes from the local model doing 60–80 % of the work, but it does that work much slower per token AND the steps run sequentially. There's nothing fundamental about this — using a faster local model (e.g., qwen3-coder MoE with 3B-active params or quantised harder) would close some of the gap. Parallelising independent steps in the plan would close the rest. Both are interesting follow-ups.

For now: **single-shot cloud is the latency floor too. Hybrid is an order of magnitude slower no matter how you slice it.**

---

## Gaps and what's next

In priority order for the next iteration:

1. **Bump synth `max_tokens` and/or move synth to a non-reasoning model.** Exp 3's failure has a five-line fix in `architect-core.mjs` — set `maxTokens: 6000` for the synth phase, or pin synth to `gpt-5` (less reasoning-aggressive) instead of `gpt-5.5`. Would have produced a usable output for exp 3 at ~the same cost.
2. **Wire prompt caching for the cloud calls.** OpenAI's automatic prompt caching gives 10× discount on cache-read tokens. The architect's planner and synth re-send chunks of stable prefix every time — exactly what caching is for. On a $0.10 synth that's $0.05–0.07 saved with zero quality impact.
3. **Truncate or summarise prior-step context in executor prompts.** Currently every executor step receives the entire prior-step blob (up to 800 chars per prior step). For the long plans this is the dominant cost of hybrid prompt tokens. Could replace with a per-step "what was produced" summary (~50 tokens each) for a similar information transfer at 1/10 the cost.
4. **Try a faster local model.** `qwen3-coder:30b` (MoE 3B-active) ran ~1.5–2× faster than `qwen3.6:27b-coding-mxfp8` (dense) in earlier ad-hoc runs. The quality difference on these tasks would be small. If the goal is "viable for interactive use", this is the most direct lever.
5. **Parallelise independent steps in the plan.** The planner emits a `depends_on` field that's currently ignored — every step runs sequentially. For tasks where steps 2, 3, 4 don't depend on each other (multiple independent files), running them concurrently would cut hybrid wall time roughly in half.
6. **LLM-as-judge for quality comparison.** Manual review is fine for three experiments; for a 50-experiment battery you want pairwise judging with an impartial model (e.g., `gpt-5` rating outputs from `gpt-5.5` and `qwen3.6` blind). Would let us put numbers on quality regression instead of "looks comparable".

The first two are weekend-scale. Either alone would shift exp-3-class workloads from "loses to cloud-single" to "draws or beats cloud-single".

---

## How to reproduce

```sh
# Pre-reqs
ollama pull qwen3.6:27b-coding-mxfp8     # local code model (27 B mxfp8, ~31 GB)
ollama pull qwen3:0.6b                    # router-classifier model
ollama pull nomic-embed-text              # embedding model for kNN strategy

# OpenAI key in .env:
echo "OPEN_AI_API_KEY=sk-..." > .env

# Start the proxy
./router/start.sh   # listens on :8787

# Run the experiments
node examples/run-comparison.mjs                  # all 3
node examples/run-comparison.mjs 02-todo-api      # just one
```

Outputs land under `examples/<id>/{cloud-only,hybrid}/`. Aggregate at `examples/RESULTS.md`.

---

## Closing

The framing this article landed on — *hybrid is for decomposed agents, not single-shot tasks* — is more nuanced than the obvious "look how cheap local is" pitch. We started this work expecting to declare hybrid routing a 70 %+ cost saving across the board. The honest answer is that the saving exists *exactly when you'd expect it to*: when you'd otherwise be doing decomposition anyway and most of the per-step work is mechanical.

The piece of work we're least sure about is what happens when there's a real human in the loop accepting/rejecting code changes between steps. That changes the latency picture entirely — wall time becomes "developer-typing-speed bounded" instead of "model-token-rate bounded". Worth running this experiment again with a real session log replayed through the proxy and seeing what happens.

If you want to try it: the repo is up, the runner is real, the numbers reproduce. Open issues are welcome — especially the "where it doesn't work" cases.
