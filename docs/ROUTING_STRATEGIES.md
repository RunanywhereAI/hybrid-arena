# Routing strategies — what they do, how they decide, and *when* they fire

This document covers two questions in detail:

1. **What does each of the 7 routers actually do?** — the algorithm, the inputs, the decision rule, the failure modes.
2. **At what granularity does routing happen?** — today it's one decision per chat-completion request. The interesting question is what *finer-grained* routing looks like (per tool call, per sub-task, per item in a TODO list a planner agent generates), what the trade-offs are, and how it can be retrofitted onto the current setup without rewriting opencode.

The 7 strategies live in `router/strategies.mjs`; the proxy plumbing in `router/server.mjs`. Read those if you want the full source.

---

## Part 1 — The seven strategies

All strategies have the same signature:

```ts
async function decide(req, ctx): Promise<{
  choice: "local" | "cloud",
  reason: string,
  confidence: number,
  meta?: object,
}>
```

`req` is the parsed OpenAI-style chat-completion body (`messages`, `tools`, `temperature`, …). `ctx` carries shared resources (Ollama base URL, OpenAI key, the embedding corpus, the log function).

The choice maps to a backend (`local` → `qwen3-coder:30b` via Ollama, `cloud` → `gpt-5.5` via OpenAI). The reason is a one-line human-readable trace that shows up in the response banner and the JSONL decision log. Confidence is a soft 0–1 score the router attaches to its own decision — it's not currently used to drive a re-route, but it's available if you want to build a "reroute when conf<0.7" wrapper.

### 1. `always-local` (control)

**Algorithm.** Returns `local`, no inspection. O(1).

**When to use it.**
- Establish the floor: "what does life feel like with only the local model?"
- Burn-in / smoke test the local model after upgrading Ollama.
- Privacy-strict mode: a hard guarantee that nothing leaves the laptop.

**Failure mode.** Will route a 50-paragraph "design a system" task to qwen3-coder, which will produce a worse answer than gpt-5.5 would. Use only as a baseline.

---

### 2. `always-cloud` (control)

**Algorithm.** Returns `cloud`, no inspection. O(1).

**When to use it.**
- Establish the ceiling: "what does life feel like with only the cloud model?"
- Compare actual cloud cost against what a real router would have saved.
- Diagnose whether a complaint is "the local model is bad" or "even gpt-5.5 is bad at this".

**Failure mode.** Burns API tokens on tasks the local model could have done in 200 ms.

---

### 3. `rules` (deterministic regex/threshold)

**Algorithm.** Reads the **last user message text** (`lastUserText(messages)`) and `totalPromptTokens(messages)`. Applies three categories of trigger:

```
TRIGGER cloud if any of:
  • totalPromptTokens > 4000
  • countCodeBlocks(text) >= 3
  • text contains any CLOUD_KEYWORDS
TRIGGER local if any of:
  • text contains any LOCAL_KEYWORDS
DEFAULT:
  • local
```

`CLOUD_KEYWORDS` (24): `design, architect, architecture, explain why, compare, long, comprehensive, plan, strategy, trade-off, tradeoff, production, security, threat model, performance critical, optimize, refactor entire, refactor all, migration plan, step by step, prove, derive, analyze the, review the, best way to, what would be the best`.

`LOCAL_KEYWORDS` (12): `rename, typo, add a comment, format, prettier, what is, fix the typo, change the variable, convert, one-liner, quick, trivial`.

**When it routes.** Once per chat-completion request. Synchronous, ~0 ms.

**When to use it.**
- You want the simplest possible router that you can audit at a glance.
- You want the decision to be 100% reproducible across runs (no stochastic LLM in the loop).
- You're calibrating the keyword list and want the decision trace to surface exactly which keyword fired.

**Failure modes.**
- Keyword spoofing: prompt that uses *the word* "design" trivially routes cloud even if the task is small.
- Misses: prompt like "diagnose this performance regression" doesn't include the obvious keyword "design", but is conceptually complex. (The keyword `step by step` catches some such prompts but not all.)
- Dialect drift: keywords are English-biased.

**Code reference.** `strategies.mjs:rules()` (~15 LoC).

---

### 4. `heuristic` (weighted score)

**Algorithm.** Computes a composite score and compares against a fixed threshold:

```
userTokens   = approxTokens(lastUserText(messages))   // 4 chars/token rule of thumb
codeBlocks   = count of fenced ``` ``` pairs in the user message
cloudHits    = count of CLOUD_KEYWORDS that appear (case-insensitive)
localHits    = count of LOCAL_KEYWORDS that appear
toolCount    = req.tools.length

score = min(20, userTokens / 80)        // capped, not unbounded
      + 6 * codeBlocks
      + 14 * cloudHits
      - 18 * localHits
      + (toolCount >= 25 ? 6 : 0)

choice = score >= 25 ? cloud : local
confidence = clamp(0.5 + |score - 25| / 50, 0, 1)
```

**Calibration note.** The user-token cap (20) and threshold (25) are **calibrated for opencode usage** where the system prompt + tool definitions baseline is ~3 K tokens. Earlier we scored on `totalPromptTokens` and even "Reply OK" routed cloud because opencode's wrapping alone scored ~32. The fix is to score on the user message only.

**When it routes.** Once per chat-completion request. Synchronous, ~0 ms (no I/O).

**Why it works (and where it doesn't).**
- It's a smooth, interpretable score: every contribution is in the trace.
- It's robust to keyword spoofing in a way pure rules aren't: a single keyword bumps the score by 14 but won't override a strong local signal.
- It's still keyword-bound — it will miss prompts like *"why is my p99 spiking"* that have no signature keyword but require deep reasoning.
- The toolCount signal is a near-no-op for opencode (always passes 10–15 tools regardless of task), so we only fire it at ≥25.

**When to use it.**
- Your default for human-typed prompts. It outperforms `rules` on calibration but pays the same ~0 ms.
- When you want the *reason* to be a math sentence you can debug.

**Code reference.** `strategies.mjs:heuristic()` (~30 LoC).

---

### 5. `llm-classifier` (qwen3:0.6b says SIMPLE or COMPLEX)

**Algorithm.** Sends the last user text to `qwen3:0.6b` via Ollama's native `/api/chat` endpoint with `think:false` (Qwen3's thinking mode is disabled or it eats the token budget on hidden reasoning). The system prompt:

```
You are a routing classifier. Classify each user request as SIMPLE or COMPLEX.
SIMPLE = a junior dev can do it in <5 min (rename, typo, single function, comprehension).
COMPLEX = needs architecture, security review, multi-file refactor, comprehensive analysis,
         or a long structured answer.
Respond with EXACTLY one word: SIMPLE or COMPLEX. No reasoning, no other words.
```

`num_predict=4`, `temperature=0`. Reads `message.content`, uppercases, prefix-matches `SIMPLE` or `COMPLEX`. Anything else → fallback `local`.

**When it routes.** Once per chat-completion request. Adds **50–200 ms** because of the model call (or 1–3 s on cold start when qwen3:0.6b first loads into VRAM).

**Why it's interesting (and where it fails).**
- It can recognise "this prompt has no keywords but feels like architectural thinking" — at least sometimes.
- It's stochastic: same prompt can flip on different runs. Set `temperature=0` and `num_predict=4` to reduce drift, but the model's ~0.6 B parameters is just not enough to be reliable on borderline cases.
- In our test sweep, it *miscalled* `complex-perf` and `complex-architecture` as SIMPLE, while `rules` and `embedding-knn` got them right. Don't trust qwen3:0.6b further than rules can throw it.

**When to use it.**
- You want a "second opinion" alongside the rules — but use it as input to `cascade`, not on its own.
- You're running comparable tests against a bigger router model (e.g. swap in `qwen3-coder:30b` or `mistral-small`) — the strategy is parameterised on `ctx.routerModel`.

**Replacing the model.** Set `ROUTER_MODEL=<ollama-tag>` before launching `start.sh`. Anything that responds to OpenAI-style `chat` and returns SIMPLE/COMPLEX in one token will work.

**Code reference.** `strategies.mjs:llmClassifier()` (~30 LoC).

---

### 6. `embedding-knn` (kNN over a labelled corpus)

**Algorithm.**

1. **Lazy bootstrap.** On first call, load `corpus/examples.json` (50 hand-labelled prompts: 25 local-class, 25 cloud-class). Embed every example with `nomic-embed-text` via Ollama's `/api/embeddings`. Cache in memory.
2. **Per-request.** Embed the user message. Compute cosine similarity against every corpus embedding. Take the top **k=5** neighbours.
3. **Vote.** Sum the cosine similarities of the cloud-labelled neighbours and the local-labelled neighbours. Whichever sum is larger wins.
4. **Confidence** = max(weight) / (cloud-weight + local-weight).

**When it routes.** Once per chat-completion request. ~30–80 ms warm; ~5–15 s cold (loading corpus and embedding 50 examples once).

**Why it's interesting (and where it fails).**
- It generalises beyond the keyword list: a prompt like *"diagnose this performance regression: p99 latency jumped from 50ms to 800ms after our last deploy"* has no keyword match but is semantically close to *"Diagnose this performance regression: p99 latency went from 50ms to 800ms after our last deploy"* in the corpus → strong cloud vote.
- In our test sweep, it caught all 5 ground-truth complex prompts; rules only caught 4; heuristic only caught 3.
- It also over-fires: it tagged `moderate-bugfix` and `ambiguous-short` ("fix it") as cloud because the closest corpus example happened to be cloud-flavoured.
- Quality is bounded by the corpus. If you swap in a 500-example labelled corpus from your real opencode usage history, this strategy gets the most lift of all 7.

**When to use it.**
- After you've used the system for a week or two and have a real distribution of prompts that you can label and dump into `corpus/examples.json`.
- When you want a router that *learns* without training a model — just relabel the corpus.

**Failure mode to know.** Cosine similarity over 768-dim nomic embeddings is decent for English coding prompts, less reliable for multi-paragraph code dumps. If your prompt is mostly code and little prose, the embedding mostly reflects "this is a code file", which clusters everything together.

**Code reference.** `strategies.mjs:embeddingKnn()` (~50 LoC), corpus at `corpus/examples.json`.

---

### 7. `cascade` (heuristic, with llm-classifier as tiebreaker)

**Algorithm.**

```
h = heuristic(req)              // computes score and distance from threshold

if |h.score - 25| > 15:         // heuristic is confident → trust it
  return h

c = llmClassifier(req)          // 50–200 ms, qwen3:0.6b says SIMPLE/COMPLEX

if c.choice == h.choice:
  return h with combined confidence

return c                         // they disagree → trust the classifier
```

**When it routes.** Once per request. Synchronous-fast (~0 ms) on confident heuristic; +50–200 ms on borderline cases.

**Why it's the recommended *smart* router.**
- It pays the cost of the classifier only when the cheap heuristic is genuinely uncertain (~15–20% of requests in our sweep).
- It cannot be worse than `heuristic` by more than the noise of the classifier — and on borderline cases the classifier sometimes gets it right when heuristic doesn't.
- It exposes the disagreement in the trace: if heuristic says cloud and the LLM says local, the reason field shows you.

**Honest caveat.** When heuristic says cloud and the qwen3:0.6b classifier says local, cascade goes local — and the classifier is wrong on border cases ~50 % of the time. If you want a more conservative variant ("when in doubt, escalate"), change the last `return c` line to `return c.choice === "cloud" ? c : { choice: "cloud", reason: "cascade[disagree → escalate-to-cloud]: " + ..., confidence: 0.6 }`. That would push cascade's cloud-rate from 18 % to ~25 %, and probably catch `complex-perf` correctly.

**Code reference.** `strategies.mjs:cascade()` (~25 LoC).

---

## Part 2 — *When* does the router actually fire?

The strategy you pick determines the *quality* of the routing decision; the *granularity* at which the decision is made determines what kinds of work can be hybrid-routed. These are independent axes.

### The granularity ladder

```
coarsest                                                               finest
  ◯─────────────◯─────────────◯─────────────◯─────────────◯
  per-session   per-turn       per-tool-call  per-subtask   per-token
  (you set it   (one decision  (each tool     (each item    (theoretical;
   once at      per chat-      call routed    in a planner  not done in
   startup)     completion)    individually)  agent's TODO  practice)
                ← TODAY                       list routed)
```

### Today: per-turn

Every time opencode sends `POST /v1/chat/completions`, the proxy makes **one** routing decision and forwards the entire body to one backend. That backend handles the full turn, including any tool-calls inside it. When opencode follows up (e.g. with the tool-call results in the messages array), that's a *new* HTTP request → a *new* routing decision.

So in an agentic loop where the user asks "list the 5 largest files and summarise", you'll see something like:

| step | who calls whom | router decision |
|---|---|---|
| 1 | opencode → proxy: chat with the user prompt + tools | one decision, e.g. `→ cloud` because the prompt has a complex feel |
| 2 | proxy → gpt-5.5: same body | gpt-5.5 emits 3 tool calls (`bash ls -la`, `bash wc -l file*`, `bash head ...`) and waits |
| 3 | opencode runs the tools locally and packages the results | — |
| 4 | opencode → proxy: chat (now with tool results in messages) + tools | a *new* routing decision, e.g. `→ cloud` again because the message history is now ~5 K tokens and includes the file dump |
| 5 | proxy → gpt-5.5: summarises | … |

Cost-wise, the per-turn granularity means the user's whole multi-turn agentic session is either-or: every turn is its own decision, but **within** a turn the model that was picked does everything. You cannot, today, have qwen3-coder run the `ls` tool call and gpt-5.5 run the summarisation, because the tool call is decided by the *backend model*, not by the router.

### Per-tool-call (next-step granularity)

The first finer granularity is **route each tool call independently**. The pattern looks like this:

```
opencode → proxy → backend-A produces a tool-call
            ↑
            └── proxy intercepts, decides where to RUN the tool's continuation,
                possibly handing off to backend-B before the next chat round
```

Two ways this can be implemented:

**(a) Tool-result-time re-route.** Easiest, runs inside the existing proxy.

In opencode's agent loop, after every tool-call the assistant is invoked again with `tool` messages appended. That second invocation is *already* a new chat-completion request → already gets a fresh routing decision today. So if you want it to consider whether *this round* is now simpler than the last (because the heavy planning happened in the previous turn), you only need a small heuristic addition: detect that the most recent assistant message was a planning text + tool-calls, and the upcoming round is "consume the tool result". That's a simple signal: `messages[-1].role === "tool"` and `messages[-2].content` was long → bias toward local on this round.

This is *de facto* possible right now, just not specifically tuned. You can prototype it as an 8th strategy: copy `heuristic`, add `if (messages[-1].role === "tool") score -= 10`, see if it helps.

**(b) Tool-call dispatch (agent rewrite).** Hard, requires changing opencode's agent loop or adding a sub-process pattern.

Each tool call gets a **per-call** routing decision based on what the call looks like:

```
backend-A produces: tool_calls = [
  { name: "bash", args: { cmd: "ls -la" } },     // simple, route bash to local
  { name: "explain", args: { reasoning: "…" } }, // heavy, route to cloud
]
```

To make that work you'd need (i) a layer that runs between opencode and the backend and intercepts tool calls, (ii) per-tool routing rules, and (iii) a way to fold the per-call results back into the conversation. opencode doesn't expose that today.

The closest thing in the current codebase is the **plugin** mechanism — a plugin can intercept events. Plugins live in `~/.config/opencode/` (it has `bun.lock`/`package.json`/`node_modules`, so a plugin is npm-installable). A `model.before` hook would let you swap the model right before each chat-completion request based on what's in `messages`, which is essentially per-turn routing with full context — equivalent to what the proxy does, but in-process.

### Per-subtask: the "TODO list from a bigger agent" case

This is the case you specifically asked about: a bigger agent generates a TODO list, and *some* tasks could be done by a smaller model. There are three legitimate ways to do this, in increasing order of how much you have to change.

#### Pattern A — Architect/Editor split (the aider model)

This is how aider's `--architect` mode works:

```
phase 1 (planner)           phase 2 (executor)
─────────────────           ──────────────────
big model receives          small/cheap model receives
  • user request              • the user request  
  • code context              • the architect's plan
emits a structured plan     • executes it (file edits, simple code)
  e.g. JSON:
  [
    {"step": 1, "kind": "edit",
     "task": "rename total to subtotal in pricing.ts"},
    {"step": 2, "kind": "explain",
     "task": "why does this break the cart contract?"},
    ...
  ]
```

In this pattern you have **two routing decisions per user turn**:

1. The *planning* turn always goes to the big model (because planning needs reasoning).
2. *Each step* of the plan gets its own routing decision when the executor consumes it. Step 1 ("rename") routes local; step 2 ("explain why") routes cloud.

opencode does not ship architect/editor split out of the box. To add it you'd build:

- A new opencode **agent definition** (`opencode agent` command exists). The agent's system prompt instructs the model to first emit a structured plan (e.g. as a fenced JSON block), wait, then execute step-by-step.
- A small "step dispatcher" that takes a step JSON, picks a model with the heuristic, and runs that step against the chosen backend.

For tonight's setup I did **not** build this — it would have required more than a routing proxy. But the proxy is the right substrate to build it on: each step would just be one more chat-completion request to `http://127.0.0.1:8787/v1/chat/completions`, with model `router/heuristic`, and the heuristic would correctly route most steps without you having to label them by hand.

**Sketch — what an architect/editor opencode agent would look like:**

```jsonc
// ~/.config/opencode/agents/architect-editor.json
{
  "name": "architect-editor",
  "description": "Plan with the big model, execute step-by-step with router/heuristic",
  "phases": [
    { "name": "plan",
      "model": "hybrid-router/router/always-cloud",
      "prompt_suffix": "Emit a JSON plan as a list of {step, kind, task} objects.",
      "expect": "json_array_of_steps" },
    { "name": "execute",
      "for_each": "step",
      "model": "hybrid-router/router/heuristic",
      "prompt_template": "Execute this step from the plan: {step}",
      "fold_into": "messages" }
  ]
}
```

opencode's agent system supports custom agents but the per-step routing/dispatching is something you'd need to write — it's not a one-config change. It's about 100 lines of TypeScript.

#### Pattern B — `delegate` tool

Another shape is to give the big model a tool that *explicitly delegates*:

```
big model thinks → emits tool_call to `delegate(task: string, hint: "simple"|"complex")`
                ↘
                  the proxy or opencode plugin runs the delegate by
                  routing the inner task with router/heuristic
                ↗
big model receives the delegate's result → continues
```

This is an explicit, agent-driven version of routing: the big model itself decides "this part is small enough to delegate", emits the tool call, and the router executes the inner task in the cheap backend. Failure mode: the big model is bad at recognising what's actually simple, and might never delegate or always delegate.

**Honest assessment.** In our research, "agent self-delegation" is a known pattern but works less reliably than external routing. The big model has incentive to keep tasks for itself (it doesn't know it costs money). If you build this, give the big model concrete examples in its system prompt of what to delegate — and instrument the delegation rate.

#### Pattern C — TODO-list parser (post-hoc)

If a TODO list is just text (e.g. the model emits `1. Do X. 2. Do Y.`), a post-hoc parser can split it into items and re-prompt for each. This is the easiest to build but the lossiest — TODO lists in natural language don't always have crisp boundaries, and re-prompting per item loses the "I'm in the middle of a task" context.

I'd consider this a legacy pattern. If you go this direction, prefer Pattern A.

### What the *router proxy* can do today vs what would need new code

| capability | proxy today | needs |
|---|---|---|
| per-turn routing | ✅ default | — |
| route differently after a tool call (heuristic-aware of message history) | ✅ already happens because each turn re-routes | optional: add a strategy that biases toward local when the previous message was a tool result |
| per-tool-call routing (different model for `bash` vs `explain`) | ❌ | would require a layer between opencode and the backend that demuxes tool calls |
| architect/editor split | ❌ | new opencode agent + step dispatcher (~100 LoC), uses the proxy unmodified |
| explicit `delegate` tool | ❌ | the big model needs a `delegate` tool definition; the proxy can serve as the executor for delegate calls |
| post-hoc TODO parsing | ❌ | a small wrapper script would work, but Pattern A is better |

### Concrete recommendation

If you want to actually try per-subtask routing tonight or this weekend:

1. **Stay at per-turn routing** for the main chat. That's already working and the heuristic handles it well.
2. **Build Pattern A as an opencode agent.** Either as a custom agent or as a Node script that calls the proxy in two phases (plan with `router/always-cloud`, then execute each step with `router/heuristic`). The proxy is unchanged.
3. **Measure.** Compare pure cloud (`always-cloud`) vs architect/editor on a 50-task workload. The expected outcome: 60–80 % of executor steps route local, costing nearly nothing, while the 20–40 % that route cloud are the ones that actually need it.
4. **Don't touch tool-call-level routing yet.** It requires more architecture and the win is smaller — most tool calls are cheap shell commands that the local model can already drive.

### Implementation status

Pattern A is **implemented and live** in `router/agentic/`:

- **`router/agentic/architect.mjs`** — CLI tool. `node architect.mjs "your task"` runs the full plan→execute→synth pipeline against the proxy and writes a markdown report to `examples/`.
- **`router/agentic/architect-core.mjs`** — shared library exposing `runArchitect(opts)`.
- **`router/architect`** — pseudo-strategy in the proxy. The proxy intercepts `model: "router/architect"` and runs the same pipeline, returning the synthesised answer as a normal OpenAI chat completion (with `X-Architect-Steps`, `X-Architect-Local`, `X-Architect-Cloud` response headers and a per-call decision-log record).

Empirical results on first runs:

| task | calls | plan | local exec | cloud exec | synth | wall |
|---|---:|---:|---:|---:|---:|---:|
| 7-step refactor (rename + JSDoc + test + explain) | 9 | 1 cloud | 7 | 0 | 1 cloud | 40 s |
| 12-step heterogeneous (design + implement + explain) | 14 | 1 cloud | 10 | 2 | 1 cloud | 165 s |

Per-subtask routing actually delivers what it promises: the trivial editing/testing/wiring steps execute on the local model for free, while the cloud is reserved for the parts that genuinely need it (planning, architectural decisions, final synthesis). Read `router/agentic/README.md` for the full breakdown, including the opencode-integration caveat (opencode's build agent loops on the architect's response — use the CLI or curl for clean demos).

---

## Part 3 — Decision-record extension for sub-task routing

If/when you add Pattern A, the existing `logs/decisions.jsonl` schema extends naturally:

```jsonc
{
  "ts": "...",
  "id": "...",
  "phase": "plan",          // NEW: "plan" | "execute" | "single"
  "parent_id": null,        // NEW: links execute steps to their plan turn
  "step_index": null,       // NEW: which item in the plan
  "step_kind": null,        // NEW: "edit" | "explain" | "search" | …
  "strategy": "always-cloud",
  "choice": "cloud",
  ...
}
```

That makes "what fraction of executor steps routed local?" a one-liner:

```sh
jq -r 'select(.phase=="execute") | .choice' logs/decisions.jsonl \
  | sort | uniq -c
```

---

## Summary

- **Strategy** (1–7) decides *how* the router thinks. Today: 7 implementations, of which `cascade` and `embedding-knn` are the strongest on quality, `heuristic` is the strongest on simplicity-vs-quality trade-off.
- **Granularity** (per-session ↔ per-token) decides *when* the router thinks. Today: per-turn. Per-subtask routing (the TODO-list case) is feasible without modifying the proxy by building an architect/editor agent on top — the proxy already supports the multiple chat-completion calls that would entail.
- The next material gain comes from (a) curating a real labelled corpus from your live decisions log and pointing `embedding-knn` at it, and (b) building Pattern A so a planner agent can use the cheap backend for the parts of its plan that don't need the expensive one. Both are weekend-scale projects on top of what's already running.
