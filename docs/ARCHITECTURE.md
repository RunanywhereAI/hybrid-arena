# Hybrid Local + Cloud Routing for opencode — Detailed Architecture

> **Date written:** April 25, 2026
> **Author context:** Comprehensive synthesis from 32 parallel research agents (8 on opencode internals, 8 on local coding models, 8 on routing techniques, 8 on small classifier/router models).
> **Goal:** Adapt opencode so a local 25–40B coder model handles routine work and a cloud frontier model handles hard work, dispatched by a fast small router. Reduce per-request cost while keeping agentic quality.
> **Hardware target:** 64 GB Apple Silicon (M3/M4 Max class) primary; Linux + 24 GB GPU secondary.

---

## 0. TL;DR

opencode is structurally **already routing-ready**. A single Effect service (`LLM.Service`) wraps the only `streamText` call site in the codebase. Every provider — cloud or local — resolves to a `LanguageModelV3` from the Vercel AI SDK. Adding a router does not require ripping anything out: it requires inserting a decision step in front of `provider.getLanguage()` (or wrapping it as middleware) and wiring a small classifier process.

**Recommended stack (April 2026):**

| Slot | Pick | Why |
|---|---|---|
| Local primary coder | **Qwen3-Coder-30B-A3B-Instruct** (MLX 4-bit) or **Qwen3.6-35B-A3B** | MoE 3B-active → 70–180 tok/s on M4 Max 64 GB, Apache 2.0, native tool calling, 256K context |
| Local conservative fallback | **Devstral-Small-2-24B-Instruct-2512** at Q6_K | 68% SWE-bench Verified, dense 24B, agent-trained, fits ~25 GB |
| Cloud strong model | **Claude Opus 4.7** (or GPT-5.5) | Frontier SWE-bench (87.6% / 85%), used for hard escalations |
| Inference engine (Mac) | **LM Studio (MLX backend)** primary, **llama.cpp `llama-server`** for grammar-strict tool calls | Best tool-calling reliability + MLX speed |
| Inference engine (Linux + GPU) | **TabbyAPI + ExLlamaV3** or **vLLM-AWQ** | Fastest single-stream + best concurrency |
| Router | Hybrid: rules (cheap, deterministic) → encoder classifier (**ModernBERT-base** fine-tuned, ~15–25 ms ONNX-INT8) → optional small-LLM tiebreaker (Qwen3-0.6B Q4) | Sub-50 ms p99, calibrated, retrainable |
| Routing library reference | **Arch Gateway / Arch-Function** patterns (in-process port, not the sidecar) | Only OSS that natively addresses tool-call routing |

**Realistic cost reduction:** 30–50% on agentic coding workloads, not the 80%+ headlines you see in single-shot QA papers. Cascades silently regress on multi-turn tool-using sessions if you're not careful.

---

## 1. Goals and Non-Goals

### Goals
- Route ~60–80% of opencode turns to a locally-hosted coder model with no perceptible quality regression.
- Pay cloud-frontier rates only for the turns that actually need them.
- Keep per-turn router overhead under **50 ms p99** so it doesn't undo the savings.
- Stay inside the existing opencode mental model — no parallel `opencode-hybrid` fork, no rewrite of the agent loop.
- Produce evaluable, calibrated, auditable routing decisions.

### Non-Goals (explicitly)
- **No edge-cloud speculative decoding.** Confirmed not viable on metered cloud APIs in April 2026 (see §7.4).
- **No online bandit router.** For a single-user coding agent, n=1 means bandits add exploration tax with no aggregate signal to learn from (see §7.6). Use offline-trained classifiers and refresh them periodically.
- **No router on the autocomplete path.** Autocomplete needs <100 ms; opencode is a chat/agent surface, not a Tab-completion surface, so this is a non-issue, but worth naming.
- **No replacement of the user's explicit model choice.** The user-supplied `model` field in the request is honored as-is. The router only kicks in when the user has selected a *router* virtual model.

---

## 2. What opencode Can Do (Capabilities Inventory)

Synthesized from agents 1.1–1.8.

### 2.1 Surfaces
- **CLI** (`opencode run`, `opencode serve`) for non-interactive and headless operation.
- **TUI** rendered by `@opentui/solid` (TypeScript SolidJS terminal renderer at 60 fps; not Go, not bubbletea).
- **Web app** (`packages/app`, SolidJS + Vite).
- **Desktop** via Tauri 2 (only Rust in the repo) and an Electron variant.
- **IDE extensions** (Zed currently shipped; SDK + HTTP API support more).
- **HTTP API + SDK** (`@opencode-ai/sdk`) generated from an OpenAPI spec.
- **Slack integration**, console (multi-tenant), enterprise SST infra (in `packages/console`, `packages/identity`, `packages/slack`, `packages/enterprise`).

### 2.2 Core Agent Capabilities
- Multi-turn coding sessions persisted to SQLite (WAL mode, JSON blob columns).
- Built-in tools: `bash`, `read`, `write`, `edit`, `apply_patch`, `glob`, `grep`, `webfetch`, `websearch`, `codesearch`, `task` (subagent spawner), `todowrite`, `skill`, `lsp` (experimental), `plan_exit`, `question`, `invalid` (repair).
- MCP server tool injection.
- Custom user tools and plugins (auto-discovered from `.opencode/tool/*.ts`, `.opencode/plugin/*.ts`).
- Custom user agents/modes (auto-discovered from `.opencode/agent/*.md`, `.opencode/mode/*.md`).
- Per-agent permission rulesets (`allow` | `deny` | `ask` per tool with glob patterns).
- Plan / Build / Explore / General / Title / Summary / Compaction built-in agents.
- Session fork, share, child sessions.
- Auto-compaction when token budget exceeds `model.limit.input - reserved`.
- Tool-call repair (case-folding, fall-through to `invalid` tool stub).
- Provider-specific transforms (DeepSeek reasoning injection, Mistral tool-id scrubbing, Qwen temperature pinning, GPT prompt template selection).
- LSP integration for code intelligence.
- Snapshot / patch tracking on disk diffs.
- Telemetry via OpenTelemetry spans on every tool call.

### 2.3 Provider Surface
- ~40 cloud providers via `models.dev` registry with capability metadata (`toolcall`, `reasoning`, `temperature`, modalities, `limit.context`, `limit.output`, cost).
- Pre-registered local-style: **LM Studio** (`http://127.0.0.1:1234/v1`), **Privatemode AI** (`http://localhost:8080/v1`), **Ollama Cloud** (hosted, not local daemon).
- Local Ollama daemon, llama.cpp, vLLM, Tabby require manual `opencode.json` config under any provider id with `npm: "@ai-sdk/openai-compatible"` and a `baseURL`.
- LiteLLM-proxy compatibility via `_noop` dummy-tool injection.
- OAuth (PKCE) for providers that need it (e.g., Anthropic Pro, Google).
- Plugin hook (`provider`) lets a plugin override the model list for any provider id.

### 2.4 What opencode does NOT do today (gaps the router fills)
- **No fallback / alternate-model field on agents.** `ConfigAgent.Info.model` is a single `providerID/modelID` string. No `fallback`, no `router`, no `cascade`.
- **No automatic local-vs-cloud dispatch.** The selected model is honored as-is.
- **No session-aware difficulty estimator.** Compaction is the only state-aware decision and it triggers reactively on overflow errors, not proactively.
- **No tool-need prediction.** All declared tools are passed every turn; the model decides which to call.
- **No router telemetry.** SQLite captures token counts, cost, and tool calls per message — but there is no "router decision" record because there is no router.

---

## 3. Current opencode Architecture (Routing-Relevant Slice)

### 3.1 The Single Provider Boundary
The whole codebase routes every model call through one path:

```
PromptInput
  → SessionPrompt.Service.prompt()         (packages/opencode/src/session/prompt.ts:1281)
  → runLoop()                              (prompt.ts:1310)
  → resolveTools()                         (prompt.ts:404)
  → SessionLLM.run()                       (packages/opencode/src/session/llm.ts:72)
  → provider.getLanguage(model)            (provider.ts via LLM.Service)
  → wrapLanguageModel(model, [transformParams middleware])
  → streamText(...)  ← Vercel AI SDK       (llm.ts:333)
  → result.fullStream  → Bus events        (llm.ts:425)
```

Three properties make this a clean router insertion target:

1. **There is exactly one `streamText` call.** Every route, agent, mode, subagent, tool-result loop, and compaction step funnels through it.
2. **Every provider already returns the same `LanguageModelV3` interface.** Local models reach this surface via `@ai-sdk/openai-compatible`. There is no special-casing for local vs cloud in the call path.
3. **Effect-TS layer composition.** Replacing `Provider.Service`, `LLM.Service`, or wrapping either is a one-file change because Effect handles dependency injection.

### 3.2 Where Model Selection Already Happens
Per-message resolution at `prompt.ts:937`:

```ts
const model = input.model ?? ag.model ?? (yield* lastModel(input.sessionID))
```

Priority order:
1. Explicit model in the incoming `PromptInput` (UI / API call).
2. Agent-level override (`agent.model` from `cfg.agent[name].model`).
3. Last model used in this session.
4. Global `cfg.model`, then first available.

The resolved `{providerID, modelID}` pair is archived in each `MessageV2.User` record. **This is exactly where a router insertion belongs.**

### 3.3 Local Model Reality Check
Agent 1.3 confirmed:
- LM Studio is registered out of the box; Ollama daemon is **not** — it requires manual `opencode.json` config.
- Tool calling flows through the standard AI SDK path — no special local code path.
- The codebase has hardcoded model-name workarounds in `provider/transform.ts` for `deepseek`, `qwen`, `mistral`, `devstral` (so a local Qwen3-Coder gets the same temperature pinning as cloud Qwen).
- `error.ts` has overflow-detection regexes for Ollama, LM Studio, vLLM, llama.cpp — auto-compaction *does* trigger reactively on local provider errors.
- No client-side tokenization. Limits read from `model.limit.context` (must be declared in custom provider config; defaults to 0 → compaction won't trigger if you forget).

### 3.4 Three Concrete Insertion Points (from agent 1.2)

| # | Where | What it sees | Tradeoff |
|---|---|---|---|
| **A** | Inside `LLM.Service` before `streamText` (llm.ts:86–333) | Full `StreamInput`: messages, tools, agent, sessionID. Can swap `Provider.Model` before language resolution. | **Cleanest.** Full request context. Must register the local provider in the registry or build a `LanguageModelV3` dynamically. |
| **B** | A new entry in the `custom()` factory (provider.ts:141–816) | Only `(sdk, modelID, options)` — no message context. | Right for static URL-level routing (always proxy to a local gateway). Wrong for content-aware routing. |
| **C** | `wrapLanguageModel` middleware inside `llm.ts:387–401` | Final wire-format prompt; AI SDK params. | Best for token-count-based or final-prompt-content routing. Cannot change provider metadata (cost tracking, capability flags) retroactively. |

**Recommendation: Insertion Point A.** It has the richest context, lives at the single boundary, and a wrapping `Routing.Service` provided through Effect's layer system swaps in cleanly without touching `prompt.ts` or any client.

### 3.5 What a Router Has Available at Decision Time (agent 1.5)
- `Session.Info` row from a single SQLite read (id, title, timestamps, parentID, permission, code-diff summary, summary additions/deletions/files).
- `tokens.{input,output,cache.read,cache.write,total}` and `cost` from the *previous* assistant message (one indexed query).
- Compacted message history via `MessageV2.filterCompactedEffect(sessionID)` (cheap if compacted, full history otherwise).
- The current `PromptInput.parts[]` (text/file/agent/subtask).
- The agent definition (`agent.model`, `agent.permission`, `agent.steps`, `agent.tools`).
- The full tool list that *would* be passed (via `ToolRegistry.tools(model)`).

**No live token count available before the call.** Only historical from completed turns.

### 3.6 Frontend Coupling — Confirmed Thin
Agent 1.6 verified the TUI/Web/Desktop are **pure clients**: they fetch `provider.list()` + `config.providers()` for the model picker, attach `{providerID, modelID}` to `session.prompt()` calls, and consume SSE. No client-side provider calls, no client-side intelligence. **A server-side router needs zero client changes** as long as endpoint shapes are preserved.

---

## 4. Local Coding Models — April 25, 2026 (the "Local Tier")

### 4.1 The Field
Synthesized from agents 2.1–2.7. Verified models that exist in April 2026:

#### Qwen family (the lead)
| Model | Total / Active | Context | License | SWE-bench V | Aider Polyglot |
|---|---|---|---|---|---|
| **Qwen3-Coder-30B-A3B-Instruct** | 30.5B / 3.3B (MoE) | 256K (1M YaRN) | Apache 2.0 | ~50–70% (scaffold-dep.) | not published |
| **Qwen3-Coder-Next** (80B/3B MoE) | 80B / 3B | 256K | Apache 2.0 | 70.6% | not published |
| **Qwen3.6-27B** (dense, the user's "Qwen 3.6") | 27B | 262K (1M YaRN) | Apache 2.0 | **77.2%** | n/a |
| **Qwen3.6-35B-A3B** (MoE) | 35B / 3B | 262K | Apache 2.0 | 73.4% | **78.67%** (community run) |
| Qwen3-Coder-480B-A35B (reference) | 480B / 35B | 256K | Apache 2.0 | 69.6% | 60.9–61.8% |

There is **no Qwen3-Coder-32B**. The user's "Qwen 3.6" almost certainly refers to `Qwen3.6-27B` (dense, Apr 22 2026) or `Qwen3.6-35B-A3B` (Apr 16 2026). Both are pitched as "agentic coding" but ship as general-purpose, not separate Coder lines.

#### Mistral / Devstral
- **Devstral-Small-2-24B-Instruct-2512** — 24B dense, 256K, Apache 2.0, **68.0% SWE-bench Verified**, vision-capable. The strongest Mistral pick that fits 64 GB.
- Devstral-2-123B-Instruct-2512 — 72.2% SWE-V but ~70 GB at Q4_K_M. **Does not fit comfortably in 64 GB.**

#### DeepSeek
- All April 2026 DeepSeek shipping models (V4-Pro 1.6T, V4-Flash 284B, V3.2 685B) are MoE giants. Total-param footprint dominates memory regardless of low active. **No DeepSeek model fits in 64 GB at usable quality.**
- Smallest practical V4-Flash MLX-Q3 quant is 135 GB.
- DeepSeek as a local coder is out of contention on this hardware.

#### Llama 4
- Scout (17B active / 109B total, MoE) is the only Llama-4 variant that fits at Q4_K_M (~24 GB).
- Scout coding quality is **clearly below** Qwen3-Coder. No Code Llama 4 / coding-tuned Llama 4 was released.
- License is Llama Community License (not OSI-open; >700M MAU clause; EU exclusion for multimodal).
- Skip for the local coder slot.

#### Gemma 4 (April 2, 2026)
- E2B / E4B (sub-10B), **26B-A4B MoE**, **31B dense**.
- 256K context, **Apache 2.0** (big license shift from Gemma 3).
- Gemma 4 31B: **61.4% SWE-bench Verified**, 80% LiveCodeBench v6 (jump of ~50pt over Gemma 3).
- Native function calling now real, multimodal, very fast on Apple Silicon (~150 tok/s for 26B MoE 4-bit on M5 Pro).
- **Honest verdict:** Gemma 4 31B is competitive but Qwen3.6 still leads SWE-bench by ~16 points. Gemma 4 wins as an all-rounder; Qwen3 wins for pure coding agents.

#### Other notable in 7–40B band
- **NVIDIA OpenCodeReasoning-Nemotron-32B** — Apache 2.0, Qwen2.5-32B base post-trained on competitive programming + R1 traces. Q6_K ~26.9 GB → fits 64 GB.
- **Microsoft Phi-4-reasoning-plus** (14B, MIT) — best truly-independent lineage option.
- **IBM Granite 4.0-H-Small** (32B/9B MoE, Apache 2.0) — solid, not frontier.
- **Cursor Composer 2** (closed weights; arXiv 2603.24477) — closed but instructive: a single MoE model RL-trained inside the Cursor harness, scoring 73.7 on SWE-bench Multilingual at "fast" inference. Cited because the paper makes the case that domain-specialized models can match frontier general models on SWE-bench at substantially lower serve cost — relevant to the local-tier-vs-cloud comparison even if the weights are private.
- StarCoder3 / Yi-Coder 2026 / Apple/xAI/Anthropic open coders: **do not exist** as of April 2026.

### 4.2 The Local-Tier Pick

**Primary: `Qwen/Qwen3-Coder-30B-A3B-Instruct` at MLX 4-bit (`lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit`).**

Justification:
1. **Fits comfortably:** ~17–25 GB resident, leaves 40+ GB free for OS, IDE, browser, and KV cache up to 64K context.
2. **Speed:** 60–180 tok/s on M3/M4 Max via MLX (3.3B active means MoE wins on memory-bandwidth-bound Apple Silicon).
3. **Apache 2.0, native tool calling, well-supported parsers in Cline/OpenCode/llama.cpp/SGLang/vLLM.**
4. **256K native context** is enough to load entire repos before deciding to escalate.

**Quality alternative: `Qwen/Qwen3.6-27B` (dense, the user's likely "Qwen 3.6 coder").** SWE-bench 77.2 vs ~50 — much higher quality, but 3–5× slower per token because dense 27B activates all 27B every token. Pick this when you prioritize peak quality over latency.

**Agent alternative: `mistralai/Devstral-Small-2-24B-Instruct-2512` at Q6_K (~19 GB).** 68% SWE-bench Verified, agent-trained for tool loops, Apache 2.0. Pick this if you find Qwen3-Coder's MoE tool-calling brittle on your specific workflows.

**Avoid:** Qwen3-Coder-Next (48 GB Q4_K_M is too tight on 64 GB; needs 128 GB), Llama 4 (license + quality), DeepSeek (memory), Codestral 22B (license).

### 4.3 Inference Engine — Apple Silicon 64 GB

From agent 2.8:

| Engine | Mac viable | Tool calling | Quants | Realistic 32B Q4 / 32K ctx | Spec decode |
|---|---|---|---|---|---|
| **LM Studio (MLX backend)** | **yes — primary** | OpenAI-format + Outlines (MLX) / grammars (GGUF) | GGUF + MLX 4/8 | ~21 GB; 70–90 tok/s | Yes (0.3.10+) |
| **llama.cpp `llama-server`** | **yes — for grammars** | GBNF grammar-constrained (gold standard) | GGUF | ~21 GB; 40–50 tok/s on M4 Max | Yes (`--draft-model`) |
| **Ollama** | yes — fallback | OpenAI tools API (model-dep. quirks) | GGUF + MLX (0.19+) | ~21 GB; 45–55 tok/s GGUF, 70–80 tok/s MLX | No first-class UI |
| **MLX-LM / mlx_omni_server** | yes | Template-based (less strict) | MLX | ~19 GB; fastest tok/s | Yes |
| vLLM | **no** (Linux only) | OpenAI + xgrammar | AWQ/GPTQ/FP8 | n/a | Yes (EAGLE) |
| TabbyAPI / EXL3 | **no** (CUDA only) | OAI + Lark | EXL3 | n/a | Yes |
| TGI / SGLang | **no** | OAI | AWQ/GPTQ | n/a | Yes |
| KoboldCpp | yes | Jinja templates + GBNF | GGUF | similar to llama.cpp | Yes |

**Pick:** **LM Studio (MLX backend)** as the daily driver, fall back to **`llama-server` with `--grammar`** when you need bullet-proof JSON tool calls. Both expose `/v1/chat/completions`; both work as a custom provider in `opencode.json` with `npm: "@ai-sdk/openai-compatible"`.

### 4.4 What This Looks Like in opencode Config

```jsonc
{
  "provider": {
    "lmstudio-mlx": {
      "name": "Local LM Studio (MLX)",
      "api": "http://127.0.0.1:1234/v1",
      "npm": "@ai-sdk/openai-compatible",
      "options": { "apiKey": "lm-studio" },
      "models": {
        "qwen3-coder-30b-a3b-mlx-4bit": {
          "name": "Qwen3 Coder 30B A3B (MLX 4-bit)",
          "limit": { "context": 262144, "output": 32000 },
          "tool_call": true,
          "temperature": 0.55
        }
      }
    },
    "llamacpp-grammar": {
      "name": "Local llama.cpp (grammar mode)",
      "api": "http://127.0.0.1:8080/v1",
      "npm": "@ai-sdk/openai-compatible",
      "options": { "apiKey": "llamacpp" },
      "models": {
        "qwen3-coder-30b-a3b-q4km": {
          "name": "Qwen3 Coder 30B A3B (GGUF Q4_K_M)",
          "limit": { "context": 262144, "output": 32000 },
          "tool_call": true
        }
      }
    }
  }
}
```

Today, with **zero code changes**, you can already point opencode at this. The hybrid story below adds the routing intelligence on top.

---

## 5. Cloud Tier (the "Big Stick")

Pick one, configure it as the cloud half of the router. From benchmarks (agent 2.7):

| Closed model | SWE-bench V | Notes |
|---|---|---|
| **Claude Mythos Preview** | 93.9% | Anthropic's research preview |
| **Claude Opus 4.7** | **87.6%** | Recommended default; opencode already supports |
| GPT-5.3-Codex | 85.0% | OpenAI strong-coder variant |
| Claude Opus 4.5 / 4.6 | 80.9 / 80.8 | Cheaper than 4.7, still strong |
| Gemini 3.1 Pro | 80.6% | Tool calling reliable |
| GPT-5.2 | 80.0% | Generalist |
| Claude Sonnet 4.6 | 79.6% | Good cost/quality ratio for medium-tier |

**Recommended cloud tier:** Claude Opus 4.7 for hard escalations, Sonnet 4.6 as a "medium tier" between local and Opus when you want a 3-tier cascade. Both are first-class in opencode's provider registry.

---

## 6. Routing Techniques — What's Been Tried, What Works, What Fails

From agents 3.1–3.8.

### 6.1 Library Landscape

| Library | Algorithm | Local-vs-cloud aware? | Tool-aware? | Maintained 2026? | Verdict |
|---|---|---|---|---|---|
| **RouteLLM** (LMSYS) | Matrix factorization, BERT classifier, causal LLM, similarity-weighted | Mechanically yes | No | Dormant since Aug 2024 (research artifact); 4.8k stars | **Use as algorithmic reference**, not as a dep |
| **Arch Gateway / Plano** (Katanemo) | 1.5B preference-aligned router LLM + Arch-Function (1.5B–32B) | **Yes — first-class** | **Yes — uniquely** | Very active (Apr 24, 2026 release); now powering HuggingChat "Omni" | **Use the Arch-Function weights**, port the algorithm in-process |
| **LLMRouter** (ulab-uiuc) | OSS library with Hybrid LLM, Router-R1, MasRouter, etc. all under one CLI | Algorithmic only | Partial (Router-R1 multi-hop) | Active; 2k stars; arXiv 2406.18665, 2506.09033 | Useful as an algorithm reference + pretrained checkpoints |
| **vLLM Semantic Router** | Embedding/encoder router (Qwen3, Gemma) integrated into vLLM | First-class for self-hosted | No | Very active; ranked #2 on RouterArena (acc 66.5) | Inspiration for self-hosted setups |
| LiteLLM Router | Operations layer (RPM, latency, retries) | No semantic | No | Very active; 100+ providers; **March 2026 supply-chain attack on v1.82.7-1.82.8** — pin versions | **Useful underneath** for ops-layer fallback once decision is made |
| Portkey AI Gateway | Rule + condition routing; sub-1ms gateway | Cloud-first | No | Active; 10B+ tokens/day | Skip as core |
| Bifrost (Maxim) | Go-native; sub-100µs overhead at scale | No semantic | No | Active | Throughput-focused; consider only at >>1k req/s |
| Vercel AI Gateway | Framework-native | No | No | Active | Useful only inside Vercel ecosystem |
| OptiLLM | Routes to inference-time techniques (MOA, MARS, AutoThink) | Provider-agnostic | No | Active | Optional add-on for hard tasks |
| Martian | Proprietary | Cloud-only | No | Closed; powers RouterBench | Skip; reference RouterBench paper instead |
| Aider | Hard-coded 3-tier (architect/editor/weak) | User-configured | No | Active | Pattern reference (see §6.6) |
| Continue.dev | Role-based config (chat/edit/apply/autocomplete/embed/rerank) | User-configured local + cloud | No | Active | The clearest "shipped" hybrid story |
| AnythingLLM | Skill routing | Local-first | Skill yes | Active | Skip — different problem |
| **NVIDIA LLM Router Blueprint** | Intent-based (Qwen 1.7B) + auto-routing (CLIP+NN); FastAPI backend | Yes (NIM-aware) | No | Active | Useful reference for enterprise-grade observability |
| **Sierra Multi-Model Router (MMR)** | Per-task ordered model lists + congestion-aware provider selector | Internal | Per-task | Production; "Constellation of Models" pattern | Pattern reference for behavior-preserving fallback |
| Semantic Router (aurelio-labs) | Cosine in vector space | Privacy-first | Tools yes | Active | Microsecond decisions; pair with classifier above |

**Net:** Nobody open-sources a full ML local-vs-cloud-with-tool-awareness router as a drop-in library. The closest is Arch Gateway's `katanemo/Arch-Router-1.5B` and `katanemo/Arch-Function-*` weights — designed for tool-need prediction, MIT-licensed weights. The **vLLM Semantic Router** project (`llm-semantic-router` HF org) is the strongest 2026 entrant for self-hosters and currently sits second on the RouterArena leaderboard. Use those weights, write the router thin.

### 6.2 What's Actually Shipping in Coding Agents (April 2026)

From agent 3.3:
- **Cursor** — three specialized in-house models (Tab/Fusion at p50 260 ms / 13K ctx, Fast Apply, Composer/Composer 2). The **Composer 2 Technical Report (arXiv 2603.24477, March 2026)** confirms it's a single MoE coding model trained via RL in the live Cursor harness; scores 73.7 on SWE-bench Multilingual and 61.7 on Terminal-Bench at "fast" inference. Routing remains **role-based, not learned**; "don't suggest" is RL-baked into the Tab model.
- **GitHub Copilot Auto** — has a real `/models/session/intent` endpoint, but [GitHub's own docs](https://docs.github.com/copilot/concepts/auto-model-selection) describe it as choosing "based on real time system health and model performance" — i.e., availability/health/policy, not learned task complexity. The Copilot Next-Edit-Suggestions blog (Nov 2025) further confirms NES is a small custom model, separate from Auto's selection layer. Closest thing to ML routing in production.
- **Claude Code Auto Mode** — two-stage classifier (single-token yes/no → CoT review). Routes **safety**, not models. Latency and FP/FN published; FN 17%.
- **Windsurf "Adaptive" (Cognition)** — shipped April 6, 2026 as the default model picker option. Per the [Windsurf docs](https://docs.windsurf.com/windsurf/adaptive) and JetBrains changelog, Adaptive "intelligently selects the best AI model for each task" with **fixed per-token billing regardless of underlying model** ($0.50/M input, $2.00/M output, $0.10/M cache). This is the first **shipped, billed** hybrid router in a mainstream coding tool — confirming the demand exists.
- **Aider** — three-slot static (`--model`, `--editor-model`, `--weak-model`). User configures; no learned routing.
- **Continue.dev** — role-based config (chat/autocomplete/edit/apply/embed/rerank/summarize). Local for autocomplete + cloud for chat is the most common hybrid setup actually shipped. April 2026 docs recommend Claude Opus 4.6 / Sonnet 4 chat, GPT-5.1, Grok-4, Gemini 3.1 Pro, with DeepSeek-Coder 2 16B / Llama 3.1 8B as local picks.
- **Roo Code (formerly Roo-Cline)** — open-source autonomous coder; user-configured per-mode model selection, no learned routing.
- **Cline / Cody / Tabby / Replit / Codeium** — heuristic + user-configured; no ML local-vs-cloud router.
- **Sierra Multi-Model Router** — for non-coding agents but architecturally instructive: per-inference-task ordered fallback list + congestion-aware provider selector that "preserves agent behavior" across model swaps.

**Honest synthesis:** **Windsurf Adaptive (April 6, 2026) is the first shipped, billed ML-style routing in a mainstream coding tool.** It uses opaque routing internally, charges a flat per-token rate independent of which model gets picked, and pitches itself as "the best default for most users." Cursor, Copilot, Claude Code, and the open-source IDEs remain rule/role-based. opencode would be the first **open-source** coding agent to ship learned local-vs-cloud routing if it does.

Why? Three structural reasons:
1. **Latency tax** — autocomplete needs <100 ms; rules add 1 ms, classifiers add 50–100 ms.
2. **Frontier-vs-local quality gap** — for non-trivial tasks the answer is almost always "cloud," so a static rule does the work of a classifier.
3. **Non-determinism is a UX bug** — users complain when "the same prompt" gets different answers.

For opencode specifically:
- Its surface is **chat/agent**, not Tab-completion → 50 ms router overhead is fine.
- The 64 GB local-Qwen3-Coder is *good enough* for a wide band of routine work (the entire premise of the user's question).
- opencode users are technical and explicit about wanting cost control — they accept routing non-determinism more than IDE users do.

So the structural reasons that block this in IDEs **do not apply** here.

### 6.3 Cascade Routing: Does It Actually Work?

From agent 3.2. Cascades = "try cheap first, escalate if confidence low."

| Paper | Pattern | Reported savings | Failure mode | Agentic gap |
|---|---|---|---|---|
| FrugalGPT (2305.05176) | DistilBERT scorer → escalate | Up to 98% on QA | Threshold drift | Single-shot only |
| AutoMix (2310.12963, NeurIPS 2024) | Self-verification + POMDP meta-router | >50% cost cut | Self-eval is noisy | Single-shot |
| Mixture-of-Agents (Together AI) | Layered ensemble (NOT a cascade) | Quality-only, increases cost | Slow agent dominates | Single-shot |
| **EcoAssistant (2310.03046)** | Hierarchical agent with execution loop, retries before escalation | >+10pt success at <50% cost | Cheap model burns turns before promotion | **Closest to agentic** |
| RouteLLM (2406.18665, ICLR 2025) | Pre-classifier (NOT a cascade) | 95% GPT-4 at ~50% cost | Fragile to keyword injection (98% prediction-flip on superficial perturbations) | First-prompt only |
| Hybrid LLM (2404.14618, ICLR 2024) | BART/MLP difficulty predictor with **runtime-tunable quality threshold** | 40% fewer cloud calls without quality drop | Calibration drift | Single-query |
| **Cascade Routing (2410.10347, ICML 2025)** | First **theoretically optimal** unified routing-cascading framework | +8% on RouterBench, **+14% on SWE-bench** vs routing or cascading alone | Requires good quality estimator | First framework to address agentic coding directly |
| **xRouter (2510.08439, Salesforce)** | RL-trained tool-calling router (Qwen2.5-7B) with cost-aware reward | xRouter-7B near-GPT-5 accuracy on Olympiad Bench at 1/8 the cost | Small open models hard to train for sophisticated orchestration | Multi-call orchestration (closer to agentic) |
| **Router-R1 (2506.09033, NeurIPS 2025)** | RL with think/route interleaving; multi-hop QA | Outperforms baselines across 7 benchmarks; **conditions only on simple model descriptors** so generalizes to unseen models | Requires capable router LLM | Sequential decision multi-hop |
| **DAAO (2509.11079)** | VAE difficulty estimator + workflow allocator | +11.21% accuracy at 64% of prior cost | VAE is opaque | Multi-agent (workflow-level, not turn-level) |
| **CARGO (2509.14899)** | Embedding regressor + binary classifier; per-category | 76.4% top-1 routing acc, 72-89% win-rate vs experts | Per-category training overhead | Single-shot |
| **AdaptiveLLM (2506.10525)** | Cluster CoT lengths from a reasoning model + CodeBERT + XGBoost | +7.86% pass@1 at -88.9% resource use | Requires running a reasoning model per query | Code-focused, single-shot |
| **TRIM (2601.10245)** | **Step-level** routing; PRM scores gate strong-vs-weak per reasoning step | Selectively escalates only the steps likely to derail | PRM dependency | Reasoning steps inside a turn |
| **CSCR / Cost-Spectrum Contrastive Routing (2508.12491)** | Logit footprints + perplexity fingerprints + FAISS k-NN; microsecond latency | +25% on cost-quality tradeoff vs baselines | Embedding pool needs refresh on model changes | Static-pool retraining-free |
| **R2-Router (under ICML 2026 review)** | Reasons about quality-vs-output-length jointly; 17 Ridge regressors per LLM | **#1 on RouterArena leaderboard (acc-cost arena 71.60)** | Pre-built per-model regressors | Budget-aware single-shot |

**Critical finding (preserved and now strengthened by 2410.10347):** All single-shot cascade papers report 50–98% savings. The 2410.10347 unified framework is the first to put numbers on **agentic** cascade routing — and reports **+14% on SWE-bench** when routing and cascading are combined optimally vs either alone. **Multi-turn agentic cascades still have no broadly-adopted benchmark**, and the side-effect rollback problem remains unaddressed. Self-consistency sampling re-executes side-effecting tools. Verifier ceilings (Stroebl 2024, arXiv 2411.17501) bite hard: code that compiles and passes thin tests may still be wrong → silent regression that an agent commits. Stroebl proves there's a **hard upper bound on resampling-based inference scaling whenever the verifier is imperfect** — no amount of compute closes the gap to a stronger base model.

**Realistic savings for opencode-style agentic coding: 30–50%, not 80%+.** Anyone quoting bigger numbers is selling. Production reports are starting to converge on this band: Thumbtack's CNN+LLM cascade for moderation cuts inference cost to ~1.5% of naive full-LLM (3.7× precision, 1.5× recall) but moderation is a binary classification problem; agentic coding is not.

### 6.4 The Pattern That Actually Fits Agents

Synthesizing EcoAssistant + verifier-ceiling caveats + Stroebl 2024:

1. **Route at turn boundaries, escalate within.** A pre-classifier picks the starting tier from prompt features. RouteLLM-style alone is fragile (keyword injection breaks 98% of decisions); always layer with rules + execution checks.
2. **Per-tool-call gate, not per-turn.** Cheap model proposes the next tool call; a small verifier (parse? typecheck? tests pass?) gates it. **Execution signals beat learned scorers** — but only if your tests/types have real coverage. Process Reward Models (PRMs) are a related, stronger pattern: **ThinkPRM** (arXiv 2504.16828, TMLR 2025) ships generative-CoT verifiers at 1.5B/7B/14B sizes (HF: `launch/ThinkPRM-{1.5B,7B,14B}`) trained on only 1K synthetic CoTs and beats LLM-as-judge with 1% of the labels. **CodePRM** (ACL 2025 findings) and **DreamPRM-Code** (arXiv 2512.15000, 80.9 pass@1 on LiveCodeBench) make the function-as-step decomposition for code specifically.
3. **Escalate on retry, not on first uncertainty.** EcoAssistant's pattern — k retries before promoting — beats premature escalation.
4. **Carry trajectory on escalation; checkpoint side effects.** opencode already snapshots diffs (`SnapshotPart`); this becomes the rollback point.
5. **Avoid sampling-based confidence inside agent turns** — re-executing side-effecting tools is too expensive.
6. **Treat the router as fragile.** Per the 2025 fragility paper, monitor for keyword-injection drift; retrain quarterly; never gate safety-critical behavior on the router alone.
7. **Watch for the disruption-recovery tradeoff.** "Accurate Failure Prediction in Agents Does Not Imply Effective Failure Prevention" (arXiv 2602.03338, 2026) shows critics with AUROC 0.94 can still **degrade** end-to-end performance because intervening on a "would-have-succeeded" trajectory disrupts more than it saves. Run the paper's 50-task pre-deployment pilot before flipping the verifier on.

### 6.5 Edge-Cloud Speculative Decoding (Confirmed Not Viable)

From agent 3.4. **Cloud APIs charge per output token regardless of whether they "verified" your draft tokens.** No major commercial API in 2026 exposes a "verifier endpoint" priced on accepted-vs-drafted tokens. Local-draft + cloud-verify only saves money if you self-host the target — in which case the cloud is your GPU server, not a metered API.

For latency: network RTT is ~78% of per-token time in WAN spec-decode papers. Below ~1.15–1.20 acceptance rate, spec decoding *loses* to plain cloud autoregressive. Code/JSON OOD acceptance rates often drop to 30–50%. **Net-negative for opencode's workload.** Skip this entire branch.

### 6.6 What Aider and Continue Got Right

**Aider's 3-slot model is a useful pattern even without ML routing**:
- `architect` (strong, frontier) — for planning/reasoning passes.
- `editor` (cheap) — for diff materialization (Cursor's "Fast Apply" is the same idea).
- `weak` (smallest) — for commit messages, summarization, title generation.

opencode already has `cfg.small_model` — extend this to a full 3-slot model with `cfg.local_model`, `cfg.cloud_model`, `cfg.router_model` and you have the static-rule fallback that always works.

### 6.7 Tool-Aware and Context-Aware Routing

From agent 3.5. The literature mostly uses learned semantic features (embeddings, BERT logits). The handful of papers that use engineered features (Triage 2604.07494, AdaptiveLLM 2506.10525, Agent Psychometrics 2604.00594) confirm:

- Repo state and test patches are stronger difficulty signals than the issue prompt alone (Agent Psychometrics).
- Code-quality metrics (cyclomatic complexity, coupling, file size, duplication) drive Triage's central routing signal.
- Token-margin / verbalized confidence are weak self-eval signals on hard tasks (Spiess et al., ICSE 2025; raw LLM confidence has ECE 0.32 on code, drops to 0.03 only after rescaling).
- Multi-file scope (#hunks > 1, files modified > 1) is the dominant predictor of SWE-bench-Pro vs Verified gap.

### 6.8 Online Bandit Routers — Don't

From agent 3.6. Bandits assume amortizing exploration cost across many users. For a single-user opencode setup:

- Per-arm samples grow at the rate the user types prompts (50–200/week, not millions).
- Reward is binary, sparse, delayed, and noisy (thumbs-up rate <5% in production).
- Exploration tax is paid by the user — every "let me try Haiku on this hard prompt to learn" is a degraded answer in their face.
- New model releases wipe priors faster than the bandit converges.

**Use offline-trained classifiers refreshed quarterly.** Skip bandits.

---

## 7. Small Router Models — What to Build the Classifier From

From agents 4.1–4.8.

### 7.1 The Encoder-vs-Decoder Choice

| Choice | Pros | Cons |
|---|---|---|
| **Encoder (BERT-style)** | 5–25 ms p99 on M-series CPU; trains in 2 GPU-hours; deterministic; classification-head is 100k params | Cannot emit structured tool calls; pure label decision |
| **Decoder (Qwen3-0.6B style)** | Can emit JSON route + reasoning in one shot; reuses chat templates | 40–60 ms first-token latency; harder to fine-tune; bigger memory |

**Pick:** **encoder primary** (ModernBERT-base or DeBERTa-v3-small with classification head). Add a decoder fallback only if you decide the router needs to return structured "why" for telemetry/UX.

### 7.2 Recommended Encoder Stack

| Model | Params | M-series ONNX-INT8 | Best for |
|---|---|---|---|
| **ModernBERT-base** | 149M | ~15–25 ms (8K context support) | **Primary pick** — enough capacity for code prompts, native long context |
| DeBERTa-v3-small | 86M backbone (44M body) | ~10–20 ms | Backup if ModernBERT tooling is not yet on your runtime |
| **bge-small-en-v1.5** | 33M | ~5–15 ms | Embedding for kNN routing or contrastive prior; pair with LR head |
| all-MiniLM-L6-v2 | 22M | <10 ms | Cheap baseline; good for embedding cache |
| jina-code-embeddings-0.5B | 500M | ~50 ms | If routing on code-specific retrieval features (78% on code retrieval tasks) |
| **Qwen3-0.6B (pooling mode)** | 600M | n/a (sidecar) | The R2-Router #1 RouterArena entrant uses this as its embedding backbone; 1024-dim |
| **snowflake-arctic-embed-l** | 334M | ~30 ms | Apache 2.0; #1 on MTEB by perf-per-size at release; useful if you don't want a Bert-style fine-tune |
| Voyage-code-3 / Voyage-4-lite | hosted | API only | Closed but excellent on code retrieval; use only if you accept cloud routing-side calls |

**Inference stack:** ONNX Runtime via `onnxruntime-node` (N-API, in-process Bun), CoreML EP on macOS, CPU EP elsewhere. INT8 dynamic quantization (ORT quantizer). Fixed sequence-length padding so the graph isn't recompiled per request. **Note from Opper's 2026 latency benchmark:** vLLM-SR and RouteLLM exhibit 500+ ms latency in part because they call the OpenAI embedding API; in-process ONNX avoids this trap entirely.

### 7.3 If You Want a Generative Router Too

From agent 4.1:

| Model | License | M-series 4-bit speed | Tool calling | Notes |
|---|---|---|---|---|
| **Qwen3-0.6B** | Apache 2.0 | 150–250 tok/s, ~40–60 ms TTFT | Native, strong | **Primary pick** for decoder router |
| **katanemo/Arch-Router-1.5B** | MIT | ~50 ms decision on contemporary HW | Preference-aligned, function-call shaped | **Bootstrap option** — powers HuggingChat "Omni" via chat-ui's `LLM_ROUTER_ARCH_BASE_URL` config; routes by Domain-Action taxonomy and reports 93.17% routing score |
| **katanemo/Arch-Function-{1.5B,3B,7B,32B}** | MIT | varies | **Yes — top-7 BFCL** as of Sep 2024 | For tool-need prediction specifically |
| **Router-R1 (ulab-uiuc/Router-R1)** | Open | 7B-class | Multi-hop think+route | RL-trained on simple model descriptors; generalizes across model pools |
| **xRouter (SalesforceAIResearch/xRouter)** | Open | Qwen2.5-7B-Instruct base | Tool-calling-style orchestration | xRouter-7B near-GPT-5 on Olympiad Bench at 1/8 cost |
| Llama-3.2-1B | Llama Comm. | 100–180 tok/s | Native | License friction |
| Gemma 3 270M-IT | Gemma terms | 400–600 tok/s | Weak base; `functiongemma-270m-it` available | License gated |
| SmolLM2-360M | Apache 2.0 | >500 tok/s | Weak zero-shot | Good for fine-tuned narrow labels |

**Pick:** Qwen3-0.6B at MLX 4-bit, behind a Unix-socket sidecar (not in-process — keep router process isolated for hot-swap). **Bootstrap shortcut:** if you want to skip training entirely, point Tier 3 at `katanemo/Arch-Router-1.5B` running in vLLM/Ollama and configure routes the way HuggingChat does (`routes.json` describing primary + fallback models per domain). This is the fastest path to a working dynamic router and matches how `huggingface/chat-ui` ships the "Omni" virtual model today.

### 7.4 Routing Feature Vector for opencode

Synthesizing agents 3.5, 3.8, 4.5:

```
features = {
  # Cheap heuristics (microseconds)
  prompt_token_count          : log-transformed user message length,
  history_token_count         : running session tokens,
  turn_index                  : position in session (1 = planning, N = "fix the lint"),
  file_reference_count        : @file mentions + path/to/x regex hits + pasted code blocks,
  has_stack_trace             : regex for /Error:/, /Traceback/, /panic:/, /^\s+at /,
  has_diff_or_code_block      : fenced ```, unified diff,
  intent_keyword_score        : lexicon hit rate. heavy {refactor, design, architect, migrate, audit, debug, optimize}; fast {rename, format, lint, comment, typo, revert, run},
  active_mode                 : opencode mode {plan, build, explore},
  recent_tool_error_rate      : failed tool calls in last K turns,

  # Learned (~15 ms)
  task_type_classifier_logit  : ModernBERT head over {read-only, single-edit, multi-file refactor, new-feature, debug, doc/format},
  prompt_embedding_difficulty : VAE/MLP scalar over jina-code-embeddings,
}

route_score = sigmoid(W · features)   # logistic regression on top
```

Decision rule: `route_score > τ_high → cloud`, `< τ_low → local`, otherwise apply rules cascade (next).

### 7.5 The Three-Tier Cascade

```
Tier 0 — Hard rules (100 µs)
  - User explicitly chose a model            → honor it
  - Privacy flag set / repo marked sensitive → force local
  - PromptInput contains pasted secret/key   → force local
  - cfg.cloud_disabled = true                → force local

Tier 1 — Heuristic + cached embedding (5 ms)
  - L1 hash exact-match cache                → reuse last decision
  - L2 embedding similarity ≥ 0.92           → reuse cached decision
  - Heuristic score (cheap features only)
    - score > 0.85 → cloud
    - score < 0.15 → local
    - else fall through to Tier 2

Tier 2 — Encoder classifier (15–25 ms)
  - ModernBERT INT8 over prompt + last 1k tokens of history
  - Output: P(needs_cloud) ∈ [0,1]
  - Calibrated threshold τ = 0.5 (tune on dev set)
  - If margin |P - 0.5| < 0.10 → fall through to Tier 3

Tier 3 — Optional Qwen3-0.6B tiebreaker (40–60 ms)
  - Only ~5–10% of requests reach here
  - Returns {label, confidence, reasoning_summary}
  - Logged for retraining

Tier 4 — Per-tool-call gate (during turn)
  - Cheap-tier model proposes a tool call
  - Verifier checks: did the patch parse? does the test runner exit 0? does the typechecker pass?
  - On k=2 retry failures, escalate the *next* tool call to cloud, not the whole turn.
```

End-to-end p50 router overhead: **~10 ms**. p99 (Tier 3 reached): **~70 ms**.

### 7.6 Training the Classifier

From agents 4.3, 4.7:

**Recipe (~1 GPU-day on RTX 4090 or M4 Max 64 GB)**:

1. **Seed (300 prompts)** — pull real opencode prompts; if not available, use SWE-bench Verified (500), HumanEval+ (164), LiveCodeBench-2026 recent, BigCodeBench-Hard-Instruct.
2. **Synthesize (~4500 prompts)** — ask Opus 4.7 to generate diversified coding prompts across 30 task families (regex, async, SQL, IaC, frontend, kernel, etc.). Dedupe via MinHash 0.8.
3. **Dual-execute** — run both candidates (Qwen3-Coder local, Opus 4.7 cloud) on each. Cache aggressively. Cost: ~$300–800 for 30K prompts.
4. **Auto-label with judge** — Opus 4.7 with rubric (correctness / completeness / test-pass / instruction-following). Label `local-OK` if local score ≥ cloud - 0.15; else `needs-cloud`. Drop confidence < 0.7.
5. **Augment with hard labels** — for executable tasks, run unit tests; objective pass/fail overrides the judge. Mix 50/50.
6. **Train ModernBERT-base** — `AutoModelForSequenceClassification`, 2 classes, AdamW lr 2e-5, batch 32, 3 epochs. ~3 GPU-hours.
7. **Calibrate threshold** — pick τ on dev set for `cloud_recall ≥ 0.95`.
8. **Active-learning round** — pick 500 highest-entropy + diverse from unlabeled pool; relabel; retrain. +3–5 F1 typical.
9. **Distill to ONNX-INT8** — `onnxruntime.quantization.quantize_dynamic`. <1% accuracy drop.
10. **Shadow-deploy** — log routing decisions for 1 week before enabling.

Expected: AUC ≈ 0.86–0.92 routing accuracy, <50 ms p99 inference, 50–70% cloud-call reduction with <2% measured quality regression.

### 7.7 Bootstrap Without Training

If you don't want to train: use `katanemo/Arch-Router-1.5B` weights + `katanemo/Arch-Function-1.5B` for tool-need prediction. Fine-tune on ~5K opencode-specific labels (1 GPU-hour). Get 80% of the value with a fraction of the work.

---

## 8. Proposed Architecture

### 8.1 Topology

```
                 ┌────────────────────────────────────┐
                 │  TUI / Web / Desktop / Slack       │
                 │  (unchanged — pure SDK clients)    │
                 └─────────────────┬──────────────────┘
                                   │  POST /session/:id/message
                                   ▼
            ┌──────────────────────────────────────────────┐
            │  opencode HTTP server (Hono + Bun)           │
            │  Existing middleware: error / auth / log /   │
            │  compression / workspace / instance          │
            └─────────────────┬────────────────────────────┘
                              │  SessionPrompt.Service.prompt()
                              ▼
        ┌─────────────────────────────────────────────────────┐
        │  runLoop  (prompt.ts:1310)                           │
        │  resolveTools  (prompt.ts:404)                       │
        └─────────────────┬───────────────────────────────────┘
                          │  llm.stream(input)
                          ▼
       ┌───────────────────────────────────────────────────────┐
       │  LLM.Service.run (llm.ts:72)                           │
       │                                                        │
       │  ╔══════════════ NEW: Routing.Service ═══════════════╗ │
       │  ║  Tier 0 (rules)                                  ║ │
       │  ║    ↓                                             ║ │
       │  ║  Tier 1 (heuristics + embedding cache)           ║ │
       │  ║    ↓                                             ║ │
       │  ║  Tier 2 (ModernBERT ONNX-INT8 in N-API)          ║ │
       │  ║    ↓                                             ║ │
       │  ║  Tier 3 (Qwen3-0.6B sidecar, optional)           ║ │
       │  ║    ↓                                             ║ │
       │  ║  decision = { tier: "local"|"cloud", reason,     ║ │
       │  ║               score, features, cached: bool }     ║ │
       │  ║  → Persist to `routing_decision` table           ║ │
       │  ╚══════════════════════════════════════════════════╝ │
       │                          ↓                             │
       │  provider.getLanguage(decision.model)                  │
       │  wrapLanguageModel(model, [transformParams])           │
       │  streamText(...)  ← Vercel AI SDK                       │
       └────────────────────────────┬──────────────────────────┘
                                    │  fullStream events
                                    ▼
            ┌────────────────────────────────────────────┐
            │  Bus → SSE → clients                        │
            │  Per tool-call gate (Tier 4 verifier)       │
            └────────────────────────────────────────────┘

Sidecar processes (managed by opencode server lifecycle):
  • LM Studio (MLX backend) on :1234     — local primary coder
  • llama-server with --grammar on :8080  — fallback for grammar-strict tool calls
  • [optional] router-decoder on :9100    — Qwen3-0.6B for Tier 3
```

### 8.2 The `Routing.Service` (Concrete Design)

```ts
// packages/opencode/src/routing/routing.ts

export interface Decision {
  tier: "local" | "medium" | "cloud"
  providerID: ProviderID
  modelID: ModelID
  score: number        // P(needs_cloud) ∈ [0,1]
  reason: string       // human-readable
  features: FeatureMap // logged
  cached: boolean
  ms: number           // routing overhead
}

export interface RoutingInput {
  sessionID: SessionID
  agentName: string
  promptInput: PromptInput
  tools: Tool.Def[]
  history: MessageV2.Info[]   // post-compaction
  config: Config.Info
}

export interface RoutingPolicy {
  rules: Rule[]                     // Tier 0
  heuristics: HeuristicConfig       // Tier 1
  classifier: ClassifierBackend     // Tier 2 (ONNX path)
  tiebreaker?: GenerativeBackend    // Tier 3 (HTTP sidecar)
  candidates: ModelTier[]
  thresholds: { τ_high: number; τ_low: number; tiebreaker_margin: number }
  privacy: PrivacyConfig
}

export interface Service {
  decide: (input: RoutingInput) => Effect.Effect<Decision>
  feedback: (decision: Decision, outcome: Outcome) => Effect.Effect<void>
}

export const Service = Context.GenericTag<Service>("@opencode/Routing")
```

`Routing.layer` is provided by `LLM.defaultLayer`. To swap routing strategies at runtime, provide a different layer (test fixtures, A/B experiments, plugin overrides).

### 8.3 Wiring Into `LLM.Service`

```ts
// packages/opencode/src/session/llm.ts (delta)

export const Service = {
  run: (input: StreamInput) => Effect.gen(function*() {
    const routing = yield* Routing.Service
    const provider = yield* Provider.Service

    // NEW: route only when the user picked a 'router' virtual model
    let chosen = input.model
    let decision: Decision | null = null
    if (isRouterModel(chosen)) {
      decision = yield* routing.decide({
        sessionID: input.sessionID,
        agentName: input.agentName,
        promptInput: input.prompt,
        tools: input.tools,
        history: input.history,
        config: input.config,
      })
      chosen = { providerID: decision.providerID, modelID: decision.modelID }
      yield* persistDecision(decision, input.sessionID)
    }

    const language = yield* provider.getLanguage(chosen)
    const wrapped = wrapLanguageModel({ model: language, middleware: [transformMiddleware] })
    const result = streamText({
      model: wrapped,
      system: yield* resolveSystem(input, chosen),
      messages: yield* resolveMessages(input, chosen),
      tools: yield* resolveProviderTools(input, chosen),
      // ...
    })
    return result
  }),
}
```

**Insertion point: A** (cleanest; full request context). Net change: ~30 lines in `llm.ts`, plus the new `routing/` module.

### 8.4 Config Schema Extension

```jsonc
// opencode.json (new fields, additive — existing config still works)
{
  "router": {
    "enabled": true,
    "candidates": [
      {
        "tier": "local",
        "model": "lmstudio-mlx/qwen3-coder-30b-a3b-mlx-4bit",
        "max_context_tokens": 65536,
        "tool_call": true
      },
      {
        "tier": "medium",
        "model": "anthropic/claude-sonnet-4-6",
        "tool_call": true
      },
      {
        "tier": "cloud",
        "model": "anthropic/claude-opus-4-7",
        "tool_call": true
      }
    ],
    "rules": [
      { "if": "user.privacy_flag", "force_tier": "local" },
      { "if": "tools.includes('apply_patch')", "force_tier": "cloud" },
      { "if": "history.token_count > 200000", "force_tier": "cloud" }
    ],
    "classifier": {
      "type": "onnx",
      "model_path": "~/.local/share/opencode/router/modernbert-base-int8.onnx",
      "tokenizer_path": "~/.local/share/opencode/router/tokenizer.json",
      "max_seq_length": 512,
      "thresholds": { "high": 0.7, "low": 0.3 }
    },
    "tiebreaker": {
      "type": "generative",
      "endpoint": "http://127.0.0.1:9100/v1",
      "model": "qwen3-0.6b-instruct"
    },
    "privacy": {
      "secret_patterns": ["AKIA[0-9A-Z]{16}", "ghp_[A-Za-z0-9]{36}", "sk-[A-Za-z0-9]{48}"],
      "always_local_on_match": true
    },
    "telemetry": {
      "log_decisions": true,
      "log_features": true
    }
  }
}
```

Then a user/agent picks `"model": "router/auto"` (a virtual model that triggers the router) and routing is live.

To make this composable with existing agents:

```jsonc
{
  "agent": {
    "build": {
      "model": "router/auto",
      "permission": { "edit": "allow", "bash": "ask" }
    }
  }
}
```

### 8.5 Telemetry Schema

```sql
-- New SQLite table alongside session/message/part
CREATE TABLE routing_decision (
  id            TEXT PRIMARY KEY,           -- DecisionID (ULID)
  session_id    TEXT NOT NULL,
  message_id    TEXT NOT NULL,              -- which user message triggered this
  created_at    INTEGER NOT NULL,
  tier          TEXT NOT NULL,              -- local|medium|cloud
  provider_id   TEXT NOT NULL,
  model_id      TEXT NOT NULL,
  score         REAL NOT NULL,              -- P(needs_cloud)
  reason        TEXT NOT NULL,              -- "rule:privacy" | "heuristic:keyword" | "classifier:0.78" | "tiebreaker:cloud"
  features_json TEXT NOT NULL,              -- json blob of all features
  cached        INTEGER NOT NULL,
  overhead_ms   INTEGER NOT NULL,

  -- Filled in after the call completes
  outcome       TEXT,                       -- success|tool_error|user_retry|escalated
  escalated_to  TEXT,                       -- providerID/modelID (if escalation happened)
  total_ms      INTEGER,
  tokens_in     INTEGER,
  tokens_out    INTEGER,
  cost_usd      REAL,
  user_thumb    INTEGER                     -- -1 / 0 / +1
);
CREATE INDEX idx_routing_session ON routing_decision(session_id, created_at);
CREATE INDEX idx_routing_outcome ON routing_decision(outcome, score);
```

This is the dataset that retrains the classifier each quarter.

### 8.6 The Per-Tool-Call Gate (Tier 4)

This is the agentic-cascade piece — the highest-leverage idea from EcoAssistant + Stroebl 2024 verifier-ceiling work.

```ts
// packages/opencode/src/routing/gate.ts (new)

export const gate = (toolCall: ToolCall, ctx: Context) => Effect.gen(function*() {
  const result = yield* execute(toolCall)        // run the tool
  const verifier = yield* Verifier.Service       // cheap structural checks
  const ok = yield* verifier.check(toolCall, result)
  if (ok.isSuccess) return result
  const session = yield* SessionState.get(ctx.sessionID)
  session.tier_failure_count += 1
  if (session.tier_failure_count >= 2 && session.current_tier === "local") {
    yield* SessionState.escalate(ctx.sessionID, "cloud")
    yield* Bus.publish("routing.escalated", { sessionID: ctx.sessionID, reason: "verifier_failed_twice" })
  }
  return result
})

// Verifier checks per tool:
//   edit/write/apply_patch → tree-sitter parse, language-specific syntactic check
//   bash → exit code, stderr regex, optional sandboxed run
//   typecheck-eligible languages → tsc --noEmit / mypy / cargo check
//   tests → exit 0
```

This piggybacks on opencode's existing snapshot/patch tracking — it does not rewrite the agent loop.

### 8.7 What the User Sees

- Picks `"model": "router/auto"` (or sets it on an agent).
- A small badge in the TUI shows the tier each turn used: `[local]`, `[medium]`, `[cloud]`. Click to see the routing decision.
- Cost tracker shows: `Saved $X.XX vs cloud-only this session (router decisions: N local / M medium / K cloud)`.
- Privacy override: a dot file `.opencode/no-cloud` forces `tier=local` for this repo.
- "Why?" command in TUI explains a routing decision: rule → heuristic → classifier score → tiebreaker (if any).

---

## 9. Phased Rollout

### Phase 0 — Validate (week 1)
**Goal:** confirm Qwen3-Coder-30B-A3B + LM Studio works end-to-end on opencode with no code changes.

Steps:
1. `brew install lmstudio` (or download). Pull `lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit`.
2. Add the `lmstudio-mlx` provider to `~/.config/opencode/opencode.json` per §4.4.
3. Set `"model": "lmstudio-mlx/qwen3-coder-30b-a3b-mlx-4bit"` and run a real coding session.
4. Verify tool calling works: ask it to read a file, edit it, run a test, fix the test.
5. Measure tok/s, time-to-first-token, and tool-call reliability across 20 prompts.

**Success metric:** Qwen3-Coder handles ≥60% of routine tasks (rename, format, single-file edit, simple debug) acceptably. If it can't, fall back to Qwen3.6-27B (dense, slower but higher quality) or Devstral Small 2 24B.

### Phase 1 — Static Three-Slot Cascade (week 2)
**Goal:** ship the equivalent of Aider's architect/editor/weak split inside opencode.

Steps:
1. Add `cfg.local_model`, `cfg.cloud_model`, `cfg.medium_model` to the schema.
2. Add a "router/static" virtual model that hard-routes by:
   - `agent.name === "title" || "summary"` → small_model (already exists).
   - `agent.name === "plan"` → cloud_model.
   - All else → local_model.
3. Add per-tool permissions so `apply_patch` and `bash --network` go to cloud_model.

**Success metric:** 30%+ cost reduction vs cloud-only on a real workweek of opencode usage with no measurable quality regression.

### Phase 2 — Heuristic Router (week 3)
**Goal:** replace the static rules with the heuristic feature score (no ML yet).

Steps:
1. Implement Tier 0 (rules) and Tier 1 (heuristics + cached embedding) per §7.5.
2. Use the feature vector from §7.4 with hand-tuned weights.
3. Add the `routing_decision` table and start logging.
4. Add the `[local]/[cloud]` tier badge to the TUI.

**Success metric:** 40%+ cost reduction; routing overhead p99 <10 ms.

### Phase 3 — Trained Classifier (weeks 4–6)
**Goal:** ship the ModernBERT-base ONNX classifier.

Steps:
1. Run the training recipe in §7.6. ~$500 oracle cost + 1 GPU-day.
2. Quantize to INT8 ONNX. Bundle the model + tokenizer to `~/.local/share/opencode/router/`.
3. Add the ONNX runtime path to opencode (via `onnxruntime-node` N-API).
4. Shadow-deploy: classifier outputs are logged but rules + heuristics still drive the actual decision.
5. After 2 weeks of shadow data, flip the switch.

**Success metric:** 50%+ cost reduction; AUC ≥0.85 on held-out test set; ECE ≤0.05; <2% measured quality regression on a curated 100-task evaluation set.

### Phase 4 — Per-Tool-Call Gate (weeks 7–8)
**Goal:** add the verifier-driven escalation per §8.6.

Steps:
1. Add `Verifier.Service` with per-language syntactic checks (tree-sitter), typecheck shells, test-runner shells.
2. Track per-session escalation state.
3. Plumb escalation events through the bus (UI shows the escalation reason).

**Success metric:** silent regression rate (cases where local model produced bad code that committed without escalation) <1%.

### Phase 5 — Retrain Loop (ongoing)
- Quarterly retrain on logged `routing_decision + outcome` pairs.
- Active-learning round each retrain: pick the 500 highest-entropy + most-diverse examples for human spot-check.
- Track distribution drift (prompt embedding shifts, model deprecations).

---

## 10. Evaluation Methodology

From agent 3.7. Don't ship without these.

### 10.1 Held-Out Set
- 500 SWE-bench Verified issues
- 500 LiveCodeBench items (post-Aug 2025 to avoid contamination)
- 500 real opencode session prompts (curate from your own logs)

Pre-generate completions from both candidates so the router is scored offline.

### 10.2 Metrics

| # | Metric | Computation | Target |
|---|---|---|---|
| 1 | **Quality-at-cost (Q@50%)** | Pass@1 retained when budget = 50% of cloud-only | ≥95% |
| 2 | **AUDC / Router Efficacy** | Area under deferral curve / oracle Pareto | ≥0.85 |
| 3 | **CPT(95%)** | % of cloud calls needed for 95% of cloud-only quality | ≤50% |
| 4 | **Routing latency p50/p99** | Wall-clock from decision request to result | p99 ≤25 ms |
| 5 | **ECE of confidence** | 15-bin expected calibration error | ≤0.05 |
| 6 | **Coding-task win-rate vs Best Single** | Per-task pass@1 vs the *single best* model uniformly applied | **>50%** (hard floor) |
| 7 | **Silent regression rate** | Local committed bad code without escalation | ≤1% |
| 8 | **Privacy violation rate** | Sensitive content sent to cloud | 0 (hard) |
| 9 | **Pareto Distance** | Distance from achieved (cost, quality) point to convex hull of oracle outcomes | near 0 |
| 10 | **PGR / Performance Gap Recovered** | Fraction of (strong − weak) accuracy gap the router actually recovers | ≥80% |
| 11 | **QNC / Query-Normalized Cost** | Cost per 1K queries to reach a target accuracy; surfaces routing collapse | beat Best Single by ≥20% |
| 12 | **Brier score per model** | Mean squared error between predicted-correctness probability and observed outcome, per target model | <0.20 |
| 13 | **Reliability diagram** | Plot predicted P(needs_cloud) vs realized cloud-was-needed rate, per bin | diagonal-tracking |

**Benchmarks to evaluate against (in addition to opencode session prompts):**
- **RouterBench (arXiv 2403.12031)** — 405k inference outcomes across 11 models, 8 datasets; the original evaluation framework. 70/30 split standard.
- **RouterArena (arXiv 2510.00202)** — 9 domains × 44 categories with stratified easy/medium/hard; metrics for accuracy, cost, optimality, robustness, latency. Live leaderboard at `routeworks.github.io`.
- **RouterEval (arXiv 2503.10657)** — 200M records from 8500+ LLMs across 12 evals; measures generalization breadth.
- **LLMRouterBench** (`ynulihao/LLMRouterBench`) — unified harness for 27+ benchmarks.
- **MixEval-X (arXiv 2410.13754)** — multimodal "any-to-any" benchmark with 0.98 correlation to crowd-sourced human preference.
- **SWE-bench Verified / Pro / Multilingual**, **LiveCodeBench**, **BigCodeBench-Hard**, **Aider Polyglot** — the four code-routing benchmarks that matter; LiveCodeBench's continuous-refresh design is contamination-resistant.

### 10.3 Calibration Techniques (added April 2026)

| Technique | When to use | Notes |
|---|---|---|
| **Temperature scaling** | First post-hoc fix; one parameter | Free; usually halves ECE |
| **Adaptive Temperature Scaling (arXiv 2409.19817)** | Per-token recalibration | +10-50% over baseline; survives RLHF |
| **Platt scaling** | Two-parameter sigmoid | When you need bias correction too |
| **Isotonic regression** | When you have ≥2K calibration samples | Most flexible; risk of overfit on small sets |
| **Conformal prediction (CP-Router, arXiv 2505.19970)** | When safety guarantees matter | Distribution-free coverage guarantees; FBE entropy-based threshold selection |
| **Calibration Across Layers (arXiv 2511.00280)** | Diagnostic only — find the "calibration direction" in residual stream | Confirms calibration is distributed phenomenon, not just last-layer; possible to improve ECE+MCE without harming accuracy |

### 10.4 Continuous Monitoring
- Track all 13 metrics weekly on production traffic via the `routing_decision` table.
- Alert if `silent regression rate > 2%` or `privacy violation > 0` or `win-rate vs Best Single < 50%`.
- Dashboard surfaces tier mix, cost trend, quality trend, latency trend, **per-model Brier score drift** (early warning for model-pool churn).
- **Pre-deployment pilot:** before flipping the verifier-driven gate on for all users, run the 50-task disruption-recovery pilot from arXiv 2602.03338 to confirm interventions don't disrupt more than they save.

---

## 11. Honest Risks & Caveats

### 11.1 Acceptance Risk
The local model will sometimes get hard tasks wrong. The classifier will sometimes route those tasks local. The verifier will sometimes miss the failure. **Plan for ~1–2% silent regression as the price of cost reduction.** Mitigations: per-tool-call gate, escalation on retry, easy `[escalate]` button in the TUI.

### 11.2 Router Fragility
"Fragility of Router-LLMs" (arXiv 2504.07113, 2025) shows that learned routers have ~98% prediction-flip rate on superficial keyword injection. Anyone can break your router with a deliberately-worded prompt. **Layer rules + heuristics + classifier so no single layer can be bypassed.** Treat the router as fragile. Monitor for keyword-injection drift. Re-tune quarterly. Never gate safety-critical behavior on the router.

### 11.3 Tool-Calling Reliability of Local Models
Even Qwen3-Coder is not as reliable at tool calling as Claude/GPT for nested schemas, parallel calls, or 1000+ call sequences. **Use grammar-constrained decoding** (llama.cpp `--grammar`) when this matters. Set `experimental_repairToolCall` (already exists in opencode) to mop up case issues.

### 11.4 Memory Headroom
A 32B model at Q4_K_M plus 32K context KV cache uses ~22–25 GB. Add OS, browser, IDE, IDE LSP, the router process — you're at 35 GB easily. **Don't push to 128K context unless you have to.** Use `model.limit.context: 32768` in opencode.json to keep compaction kicking in early.

### 11.5 Apple Neural Engine Caveat
ONNX Runtime's CoreML EP partially uses the ANE; coverage depends on op support. MLX **does not target ANE** — Metal/GPU only. If you specifically want ANE, convert via `coremltools` to ML Program format and force `MLComputeUnits.CPUAndNeuralEngine`. Profile in Xcode Instruments to confirm residency. Otherwise, accept that the router runs on CPU/GPU.

### 11.6 Privacy is Binary, Not Optimization
Don't let the router decide privacy. If a repo has secrets, the user's privacy flag is the last word — Tier 0 rules force `local` regardless of any other signal. Test the secret-pattern regex on real keys before relying on it; weak regex is worse than no regex.

### 11.7 Cloud Provider API Drift
Anthropic / OpenAI tool-calling APIs change. The transform.ts hardcoded workarounds will rot. Pin AI SDK versions; add CI tests that hit each provider with a canary prompt; treat provider regressions as bugs in opencode's adapter layer, not in your router.

### 11.8 The Cost Saving Will Not Be 80%
You will see headlines from FrugalGPT etc. claiming 80–98% cost reduction. **Those numbers are single-shot QA on benchmarks that don't exist in the real world.** Real agentic-coding cost reduction realistic range is 30–50%. Plan for that.

### 11.9 Routing Collapse
"Routing collapse" — the router systematically over-uses the expensive model even on easy queries despite having multiple options — is a documented failure mode (arXiv 2602.03478, "EquiRouter"). It happens because scalar confidence scores can flip when the underlying prediction errors are small relative to the score gap between models. The fix is to predict **relative model rankings** rather than absolute scores. Watch the QNC metric in §10.2 — if you can't beat Best Single by 20% on cost, you're collapsing.

### 11.10 Disruption-Recovery Tradeoff (Failure Prevention ≠ Failure Prediction)
arXiv 2602.03338 (April 2026) shows critics with AUROC 0.94 can still degrade end-to-end performance because intervening on a "would-have-succeeded" trajectory disrupts more than it saves. A perfectly-predicting verifier is not enough; **measure end-to-end task success with the gate on vs off**, not just gate accuracy. Run the paper's 50-task pilot before enabling.

### 11.11 Provider Instability and Behavior Drift
Sierra's "Constellation of Models" engineering blog (Feb 2026) documents that silent provider-side model swaps under congestion change agent behavior even when the API name is unchanged. Their MMR + congestion-aware provider selector pattern (per-task ordered fallback list, never silently downgrade unless permitted) is the right shape. The Helicone acquisition (Mar 2026, maintenance mode) and the LiteLLM v1.82.7-1.82.8 supply-chain compromise both happened in the gateway layer in 2026 — pin gateway versions, audit deps, prefer in-process routing for the hot path.

### 11.12 Position Bias in LLM Judges
arXiv 2406.07791 (Yan et al., updated 2026) demonstrates systematic, judge-dependent position bias in pairwise LLM evaluation across 12 judges and 100K+ instances. If you train your router via Opus-4.7 pairwise judging (per §7.6 step 4), **randomize order, use multiple judges, and report position-consistency** alongside accuracy. Bias is most pronounced on close calls — exactly the cases your classifier needs labelled correctly.

### 11.13 Goodhart's Law on Router Metrics
Once you publicly report "% local" or "$X saved", every change in the model picker is incentivized to hit those targets rather than serve the user. Track multi-metric (cost, quality, win-rate, regression rate) jointly and refuse to compress to a single number in dashboards or marketing.

---

## 12. Recommended Starting Stack (concrete)

If you want to ship Phase 1 + Phase 2 in two weeks, here's the exact configuration:

```bash
# 1. Install LM Studio, pull the model
open -a "LM Studio"
# In LM Studio: download lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit
# Start the server on port 1234

# 2. Optional: also run llama-server for grammar fallback
brew install llama.cpp
llama-server -m ~/models/Qwen3-Coder-30B-A3B-Q4_K_M.gguf \
  --grammar-file qwen-tools.gbnf --port 8080 --ctx-size 65536
```

```jsonc
// ~/.config/opencode/opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "lmstudio-mlx": {
      "name": "Local LM Studio (MLX)",
      "api": "http://127.0.0.1:1234/v1",
      "npm": "@ai-sdk/openai-compatible",
      "options": { "apiKey": "lm-studio" },
      "models": {
        "qwen3-coder-30b-a3b": {
          "name": "Qwen3 Coder 30B A3B",
          "limit": { "context": 65536, "output": 32000 },
          "tool_call": true,
          "temperature": 0.55
        }
      }
    }
  },

  // Phase 1 today, behind a feature flag in code:
  "router": {
    "enabled": false,           // flip to true when Routing.Service ships
    "candidates": [
      { "tier": "local",  "model": "lmstudio-mlx/qwen3-coder-30b-a3b" },
      { "tier": "medium", "model": "anthropic/claude-sonnet-4-6" },
      { "tier": "cloud",  "model": "anthropic/claude-opus-4-7" }
    ],
    "rules": [
      { "if": "history.token_count > 200000", "force_tier": "cloud" },
      { "if": "user.privacy_flag", "force_tier": "local" }
    ]
  },

  "agent": {
    "build": { "model": "router/auto" },         // once router lands
    "plan":  { "model": "anthropic/claude-opus-4-7" },
    "title": { "model": "lmstudio-mlx/qwen3-coder-30b-a3b" }
  },

  "small_model": "lmstudio-mlx/qwen3-coder-30b-a3b"
}
```

Today (no router code yet) you can already get value from this config by setting `"model": "lmstudio-mlx/qwen3-coder-30b-a3b"` for routine sessions and switching to Opus 4.7 manually for hard ones. That's Phase 0. Phase 1 makes the switch automatic.

---

## 13. Files That Will Change

The implementation surface is small. Estimated diff to ship Phases 1–3:

| File | Change | Lines |
|---|---|---|
| `packages/opencode/src/routing/routing.ts` | **NEW** — Routing.Service interface and Effect layer | ~250 |
| `packages/opencode/src/routing/rules.ts` | **NEW** — Tier 0 rule evaluator | ~120 |
| `packages/opencode/src/routing/heuristics.ts` | **NEW** — Tier 1 feature extractor + scorer | ~200 |
| `packages/opencode/src/routing/classifier.ts` | **NEW** — Tier 2 ONNX wrapper (onnxruntime-node) | ~180 |
| `packages/opencode/src/routing/tiebreaker.ts` | **NEW** — Tier 3 sidecar HTTP client | ~80 |
| `packages/opencode/src/routing/gate.ts` | **NEW** — Tier 4 per-tool-call verifier | ~150 |
| `packages/opencode/src/routing/feature-vector.ts` | **NEW** — feature extraction shared helpers | ~140 |
| `packages/opencode/src/routing/persistence.ts` | **NEW** — SQLite `routing_decision` table | ~100 |
| `packages/opencode/src/session/llm.ts` | **EDIT** — call `Routing.Service.decide` before `provider.getLanguage` | ~30 |
| `packages/opencode/src/config/router.ts` | **NEW** — config schema for `router` block | ~120 |
| `packages/opencode/src/config/config.ts` | **EDIT** — wire router into root config | ~20 |
| `packages/opencode/src/server/routes/instance/index.ts` | **EDIT** — `/router/decision/:id` debug endpoint | ~30 |
| `packages/sdk/openapi.json` | **REGEN** — new endpoints | auto |
| `packages/opencode/src/storage/db.ts` | **EDIT** — add `routing_decision` table migration | ~40 |
| `packages/opencode/src/cli/cmd/tui/component/...` | **EDIT** — tier badge component | ~80 |

Total: ~1500 lines of new code + ~100 lines of edits. Shippable in ~3 weeks of focused work.

---

## 14. Resolved Decisions

These were originally open questions; the user has now answered them. Locking in:

1. **Privacy flag UX — DECIDED: all three layers, dotfile strongest.**
   - **Env var** `OPENCODE_NO_CLOUD=1` for ephemeral sessions / CI.
   - **Dotfile** `.opencode/no-cloud` (or `.no-cloud` at repo root) is the strongest signal — when present in the resolved project tree, Tier 0 forces `local` regardless of any other rule. This is the right knob for repos with secrets, customer data, or NDA constraints.
   - **Per-message UI toggle** in the TUI (e.g., `Ctrl+L` flips the next message to forced-local) for ad-hoc one-off cases.
   - Resolution order (highest wins): per-message toggle > dotfile > env var > config default.

2. **Router model distribution — DECIDED: download on activation.**
   - opencode binary stays slim. First time `router.enabled = true` and the router actually fires, it pulls the ONNX classifier + tokenizer from a versioned URL into `~/.local/share/opencode/router/<version>/`.
   - SHA256 verified, mirrored on the opencode CDN, falls back to HuggingFace.
   - Router updates ship independently of opencode releases. Pinning via `router.classifier.version` in config.

3. **Telemetry — DECIDED: 100% local by default; opt-in anonymized upstream pool.**
   - Default: every `routing_decision` row stays in the local SQLite database. Nothing leaves the machine.
   - Opt-in: `router.telemetry.share_to_pool = true` enables anonymized upstream sharing. What's sent: feature vector (numeric only — token counts, file-ref counts, classifier logit, tier chosen, outcome label), plus a salted session-id hash. **Never** sent: prompt text, file paths, file contents, tool arguments, model output. Pool is used to retrain the public ONNX classifier each quarter; the retrained model becomes the next download in (2).
   - Clear in-product UX: opt-in toggle in `opencode auth` flow with a one-screen summary of exactly what fields are sent. Easy off-switch.

4. **Cloud tier choice — DECIDED: N-tier dynamic (local → Sonnet 4.6 → Opus 4.7), with the router picking among them.**
   - Three configured tiers: `local` (Qwen3-Coder), `medium` (Sonnet 4.6), `hard` (Opus 4.7).
   - The classifier emits a tier label, not a binary. Threshold sweep on the dev set determines which logit ranges map to which tier. Targets: ~70% local, ~20% medium, ~10% hard.
   - Architecture is open-ended — adding a `cheap` tier (Haiku 4.5 for trivial summarization/title work) or swapping in GPT-5.5 for `hard` is a config-only change, no code edits.
   - Note: this means the `Decision.tier` enum already in §8.2 (`"local" | "medium" | "cloud"`) is the right shape; the implementation just needs the classifier to be 3-class instead of binary. ~5 lines of training-script delta.

5. **Silent regression tolerance — DECIDED: 1–2% acceptable; pursue aggressive 30–50% savings target.**
   - Calibration target: `cloud_recall ≥ 0.93` (was 0.95 in the conservative plan). The 2-point relaxation lets the router send more borderline cases to local.
   - Per-tool-call gate (Tier 4) is the safety net: structural verifier + escalation-on-retry catches the cases where local got it wrong before the user sees a regressed commit.
   - Monitor the `silent_regression_rate` metric weekly. If it crosses 2.5%, auto-bump the threshold conservatively until the next retrain absorbs the drift.
   - Aggressive default profile shipped as `router.profile = "savings"`. Conservative profile (`"quality"`) available for users who want it — sets `cloud_recall = 0.97` and `escalate_on_first_failure = true`, savings drop to ~15–25%.

---

## 15. Sources

This document is synthesized from 32 parallel research agents covering the opencode codebase, current local coding models, current routing libraries and papers, and current small-classifier model literature — all as of April 25, 2026. Per-agent detailed source lists are extensive; the most-cited primaries:

- [Qwen3-Coder-30B-A3B-Instruct (HF)](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct)
- [Qwen3.6-27B (HF)](https://huggingface.co/Qwen/Qwen3.6-27B)
- [Qwen3.6-35B-A3B (HF)](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)
- [Devstral-Small-2-24B-Instruct-2512 (HF)](https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512)
- [SWE-bench Verified leaderboard](https://www.swebench.com/)
- [LiveCodeBench leaderboard](https://livecodebench.github.io/leaderboard.html)
- [Aider Polyglot leaderboard](https://aider.chat/docs/leaderboards/)
- [RouteLLM (arXiv 2406.18665, ICLR 2025)](https://arxiv.org/abs/2406.18665)
- [FrugalGPT (arXiv 2305.05176)](https://arxiv.org/abs/2305.05176)
- [EcoAssistant (arXiv 2310.03046)](https://arxiv.org/abs/2310.03046)
- [Fragility of Router-LLMs (arXiv 2504.07113)](https://arxiv.org/html/2504.07113v1)
- [Agent Psychometrics (arXiv 2604.00594)](https://arxiv.org/html/2604.00594v1)
- [Triage code-quality routing (arXiv 2604.07494)](https://arxiv.org/html/2604.07494)
- [DAAO difficulty-aware orchestration (arXiv 2509.11079)](https://arxiv.org/abs/2509.11079)
- [Arch-Router-1.5B (HF)](https://huggingface.co/katanemo/Arch-Router-1.5B)
- [Arch Gateway (Katanemo)](https://github.com/katanemo/archgw)
- [LiteLLM Router](https://docs.litellm.ai/docs/routing)
- [ModernBERT (Answer.AI)](https://huggingface.co/answerdotai/ModernBERT-base)
- [DeBERTa-v3 (Microsoft)](https://huggingface.co/microsoft/deberta-v3-small)
- [LM Studio Tool Use docs](https://lmstudio.ai/docs/developer/openai-compat/tools)
- [llama.cpp function-calling docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md)
- [Aider architect/editor mode](https://aider.chat/2024/09/26/architect.html)
- [Continue.dev model roles](https://docs.continue.dev/customize/model-roles)
- [Cursor Composer 2 technical report](https://cursor.com/resources/Composer2.pdf)
- [GitHub Copilot Auto changelog](https://github.blog/changelog/2025-12-10-auto-model-selection-is-generally-available-in-github-copilot-in-visual-studio-code/)
- [opencode source — packages/opencode/src/{provider, session, tool, config, routing}](packages/opencode/src/)

---

## 16. Post-Research Updates (April 25, 2026)

This section captures what 5 fresh deep-research reports (open-source router models; production hybrid coding agents; production hybrid non-coding; agentic & tool-aware routing; router evaluation/benchmarks/calibration — generated April 25, 2026 via Exa + Perplexity sonar-deep-research) added, confirmed, or refuted relative to the original synthesis above.

### 16.1 Confirmed
- **Local Qwen3-Coder-30B-A3B + LM Studio + MLX** remains the right stack pick for Apple Silicon 64 GB. No newer model dethrones it for MoE-on-Mac at this hardware tier.
- **Cursor, Copilot, Claude Code, Aider, Continue, Cline, Roo, Cody, Tabby still do not ship learned local-vs-cloud ML routing.** Cursor's Composer 2 paper (2603.24477) confirms a single-specialist-model strategy. Copilot Auto's docs explicitly describe selection as health/availability driven.
- **Realistic agentic-coding cost reduction is 30–50%, not 80%+.** Multiple 2026 sources (Zylos research, the SitePoint April 22 2026 hybrid-architecture guide, the Local AI Master April 11 2026 piece) reach the same band.
- **Stroebl 2024 (verifier ceilings, 2411.17501) and the fragility paper (2504.07113) are still the two most-cited cautions.** Both validated by independent 2026 work.
- **Per-tool-call gate with execution checks beats learned scorers** when the tests/types have real coverage. Reaffirmed by ThinkPRM (2504.16828), CodePRM (ACL findings 2025), and the 2602.03338 disruption-recovery analysis.
- **Encoder-primary, decoder-fallback** router stack is the right shape; no 2026 paper displaces this pattern for sub-50ms p99.

### 16.2 New findings (added to relevant sections)
- **Windsurf "Adaptive" (April 6, 2026)** — first shipped, billed hybrid router in mainstream coding tooling; flat $0.50/M input pricing regardless of underlying model. Existence proof of demand. Added to §6.2.
- **Cascade Routing (arXiv 2410.10347, ICML 2025)** — first **theoretically optimal** unified routing-cascading framework with **+14% reported on SWE-bench**. Added to §6.3 cascade table.
- **xRouter (2510.08439)** and **Router-R1 (2506.09033)** — RL-trained tool-calling routers; xRouter-7B near-GPT-5 on Olympiad Bench at 1/8 cost. Added to §6.3 and §7.3.
- **R2-Router (under ICML 2026 review, `jqxue1999/router`)** — currently **#1 on RouterArena leaderboard**; per-LLM Ridge regressors over Qwen3-0.6B embeddings; budget-aware. Added to §6.3 and §7.2.
- **vLLM Semantic Router** + **Arch-Router-1.5B as HuggingChat "Omni"** — confirmed live production use; HuggingChat config schema (`LLM_ROUTER_ARCH_BASE_URL`, `routes.json`) is a useful template. Added to §6.1, §7.3.
- **ThinkPRM, CodePRM, FunPRM, DreamPRM-Code** — 2025-2026 wave of process reward models. ThinkPRM at 1.5B/7B/14B HF checkpoints; DreamPRM-Code hits 80.9 pass@1 on LiveCodeBench. Added to §6.4.
- **TRIM (2601.10245)** — step-level routing where PRM scores gate strong-vs-weak per reasoning step. Added to §6.3.
- **CARGO (2509.14899), CSCR (2508.12491), AdaptiveLLM (2506.10525)** — three new training-data-efficient or microsecond-latency router approaches.
- **RouterArena (2510.00202), RouterEval (2503.10657), LLMRouterBench, MixEval-X (2410.13754)** — joined RouterBench as the standard eval suite. Added to §10.2.
- **Pareto Distance, PGR, QNC, per-model Brier, Reliability Diagram** — added to the §10.2 metric table.
- **Calibration techniques inventory** (temperature, ATS arXiv 2409.19817, Platt, isotonic, conformal, calibration-across-layers arXiv 2511.00280) — new §10.3 subsection.
- **Goodhart's Law, position bias (2406.07791), routing collapse (2602.03478), disruption-recovery (2602.03338), Sierra MMR pattern, LiteLLM Mar 2026 supply-chain compromise, Helicone acquisition** — added as risks §11.9–§11.13.
- **Cursor Composer 2 Technical Report (arXiv 2603.24477, March 2026)** — adds a high-quality data point on the local-tier-vs-cloud quality gap. Added to §4.1.
- **Intercom Fin (Sep 2025 blog)** — production cascade-router case study reaching 98% escalation accuracy via fine-tuned Gemma/Qwen + encoder model — useful confirmation that custom small-model cascades beat single LLM in narrow domains.

### 16.3 Refuted or Nuanced
- **"Routers always add latency."** Refuted by Opper's 2026 latency benchmark (200-call test): OpenRouter was actually **70 ms faster than OpenAI direct** on TTFT (0.640 s vs 0.712 s). The router-tax narrative depends entirely on implementation. **Geography dominated model choice** (Tokyo 2× slower than Ireland, 3.08 s vs 1.61 s) — bigger latency impact than tier switch.
- **"95% GPT-4 performance at 14% of GPT-4 calls" (RouteLLM headline).** Nuanced: the RouterArena leaderboard shows RouteLLM ranks 11th of 12 evaluated routers and **its overall acc-cost arena score (48.1) is lower than R2-Router (71.6), vLLM-SR (67.2), MIRT-BERT (66.9), and Azure-Router (66.7).** The headline numbers were on MT Bench specifically, with augmented training; in broad evaluation RouteLLM is mid-pack.
- **"Mixture-of-Agents reduces cost."** Refuted: MoA is an ensemble that **increases cost** for quality gains; it is not a cascade. Existing §6.3 caveat is now reinforced.
- **"Speculative decoding can save cloud cost."** Re-confirmed not viable on metered APIs (no API in 2026 prices verifier-vs-drafter accepted-token rates) — but worth reiterating: the SitePoint and Local AI Master 2026 hybrid-architecture guides both pitch hybrid routing as the *only* economically viable path for cloud-quality output at local-tier cost in 2026.
- **"LLM-as-judge labeling is reliable."** Nuanced: arXiv 2406.07791 shows judge-dependent position bias in 12 judges across 100K+ pairs. Mitigations (randomization, multi-judge aggregation, per-judge calibration) are now mandatory in §7.6 step 4.
- **"Verifier accuracy of 0.94 means the gate works."** Refuted by 2602.03338 — false positive rate plus disruption-recovery imbalance can make a high-AUROC critic *degrade* end-to-end performance. The 50-task pre-deployment pilot is now in §10.4.
- **"Agentic cascades have no benchmark."** Partially refuted: Cascade Routing (2410.10347) reports SWE-bench numbers; RouterArena added a robustness column; but multi-turn-with-side-effects is still ungained — the rollback semantics remain an open problem.

### 16.4 Open questions surfaced
1. **Should routing happen at turn boundary, or per-tool-call only, or both?** The new TRIM (2601.10245) step-level routing and the Cascade Routing (2410.10347) framework both argue for finer granularity than turn boundaries; opencode's design currently routes per-turn with verifier escalation per-tool-call. Worth a dedicated experiment after Phase 4.
2. **Where does Process Reward Model verification beat tree-sitter + tests + typecheck?** ThinkPRM/CodePRM/DreamPRM-Code claim wins on reasoning steps; structural verifiers win on syntactic correctness. The right hybrid (e.g., PRM after tests pass, or PRM only on reasoning-heavy turns) is unclear.
3. **Can the router itself be made provider-pool-aware without retraining?** Router-R1 (2506.09033) conditions only on simple model descriptors and generalizes; whether this transfers to opencode's evolving model list (Qwen3.7 next month, Opus 5 next quarter) is untested.
4. **What's the right unit of telemetry pooling for retraining?** §14 decided on opt-in numeric-feature pooling. The 2511.00280 calibration-direction work suggests *internal model state* may be more useful than feature vectors — but pooling that raises new privacy questions.
5. **Does Sierra-style "behavior-preserving fallback" (per-task ordered model lists with no silent downgrade) belong in opencode?** It's the right pattern for non-coding agents; for coding the question is whether the Decision.tier abstraction already covers it or whether per-tool-call ordered lists need to be first-class.
6. **Is DAAO-style workflow-depth adaptation worthwhile inside a single coding agent?** DAAO (2509.11079) reports +11.21% accuracy at 64% cost by varying workflow complexity; opencode's mode system (plan/build/explore) is a static analog — open whether learned workflow selection adds value over the existing mode-router pairing.

---

## 17. Research Source Index

Canonical, deduplicated reference list across the 5 fresh research reports (April 25, 2026). Grouped by topic to ease navigation. Where the same paper appears in multiple reports, listed under primary topic.

### 17.1 Open-source router models, weights, and library code

- [RouteLLM (lm-sys/RouteLLM)](https://github.com/lm-sys/routellm) — original framework + matrix factorization, BERT, causal LLM, similarity-weighted routers; 4.8k stars; dormant since Aug 2024.
- [RouteLLM blog (LMSYS)](https://lmsys.org/blog/2024-07-01-routellm/) — release notes with MT Bench / MMLU / GSM8K cost reduction numbers.
- [RouteLLM paper (arXiv 2406.18665, ICLR 2025)](https://arxiv.org/abs/2406.18665) — preference-data training framework.
- [katanemo/Arch-Router-1.5B (HF)](https://huggingface.co/katanemo/Arch-Router-1.5B) — preference-aligned 1.5B routing LLM; powers HuggingChat "Omni".
- [katanemo/archgw (Arch Gateway)](https://github.com/katanemo/archgw) — sidecar gateway for tool-aware routing.
- [katanemo/Arch-Function (GitHub)](https://github.com/katanemo/Arch-Function) — 1.5B/3B/7B/32B function-calling specialists, top-7 BFCL.
- [Arch-Router HuggingChat integration docs](https://github.com/huggingface/chat-ui/blob/main/docs/source/configuration/llm-router.md) — production config schema.
- [HuggingChat "Omni" announcement](https://hackernoon.com/huggingface-chooses-arch-router) — production deployment writeup.
- [Arch-Router 1.5B explainer](https://python.plainenglish.io/arch-router-the-1-5b-model-that-routes-and-thinks-like-a-human-fda4c88ee006).
- [Arch-Router paper (arXiv 2506.16655)](https://arxiv.org/html/2506.16655v1) — 93.17% routing score; Domain-Action taxonomy.
- [vLLM Semantic Router](https://vllm-semantic-router.com) — open-source mixture-of-models router for vLLM.
- [vLLM Semantic Router embedding docs](https://vllm-semantic-router.com/docs/v0.1/tutorials/intelligent-route/embedding-routing/) — Qwen3 / Gemma config examples.
- [vLLM Semantic Router paper (arXiv 2510.08731)](https://arxiv.org/abs/2510.08731) — 10.2pt MMLU-Pro improvement; 47% latency reduction.
- [llm-semantic-router HF org](https://huggingface.co/llm-semantic-router) — checkpoints.
- [LLMRouter library (ulab-uiuc/LLMRouter)](https://github.com/ulab-uiuc/LLMRouter) — open-source; 2K stars; multiple algorithms under one CLI.
- [LLMRouter Hybrid LLM module README](https://github.com/ulab-uiuc/LLMRouter/blob/main/llmrouter/models/hybrid_llm/README.md).
- [Router-R1 (ulab-uiuc/Router-R1)](https://github.com/ulab-uiuc/Router-R1) — RL-trained multi-hop router; NeurIPS 2025.
- [Router-R1 paper (arXiv 2506.09033)](https://arxiv.org/abs/2506.09033).
- [xRouter (Salesforce, arXiv 2510.08439)](https://arxiv.org/abs/2510.08439) — RL-trained tool-calling router.
- [xRouter HTML version](https://arxiv.org/html/2510.08439v1).
- [DAAO (arXiv 2509.11079)](https://arxiv.org/abs/2509.11079) — Difficulty-Aware Agentic Orchestration.
- [DAAO HTML](https://arxiv.org/html/2509.11079v1).
- [CARGO (arXiv 2509.14899)](https://arxiv.org/abs/2509.14899) — Category-Aware Routing.
- [CARROT-LLM-Routing (somerstep/CARROT)](https://github.com/somerstep/CARROT) — cost-aware routing reference.
- [CSCR / Cost-Spectrum Contrastive Routing (arXiv 2508.12491)](https://arxiv.org/abs/2508.12491).
- [TRIM (arXiv 2601.10245)](https://arxiv.org/html/2601.10245v2) — step-level routing for multi-step reasoning.
- [PerSyn (arXiv 2510.10925)](https://arxiv.org/abs/2510.10925) — Route-then-Generate personalised synthesis.
- [R2-Router GitHub (jqxue1999/router release-routerarena-public)](https://github.com/jqxue1999/router/tree/release-routerarena-public) — current #1 on RouterArena.
- [Semantic Router (aurelio-labs)](https://github.com/aurelio-labs/semantic-router) — vector-space decision layer.
- [Martian Protocol router (martianprotocol/martianrouter)](https://github.com/martianprotocol/martianrouter).
- [NotDiamond + Weights & Biases router training guide](https://wandb.ai/ml-reports/not-diamond/reports/How-to-train-an-LLM-router-with-W-B-Weave-and-Not-Diamond--VmlldzoxMDA0MjIwNA).
- [OpenRouter Auto Router docs](https://openrouter.ai/docs/guides/routing/routers/auto-router) — uses NotDiamond under the hood.
- [NVIDIA LLM Router Blueprint](https://build.nvidia.com/nvidia/llm-router) — enterprise reference architecture; intent (Qwen 1.7B) + auto (CLIP+NN).
- [CoDyn coding-task router](https://neurips.cc/virtual/2025/131708) — NeurIPS 2025; 43% cost savings on five coding tasks.
- [Reasoning router (AmirMohseni)](https://huggingface.tw/datasets/AmirMohseni/WildChat-filtered-Qwen-3-8B-Scored) — think/no-think routing dataset for Qwen3.
- [Qwen3 reasoning mode (OpenRouter)](https://openrouter.ai/qwen) — official Qwen3 thinking-mode toggle docs.
- [DevQuasar/llm_router_dataset-synth (HF, used in ModernBERT routing fine-tunes)](https://www.philschmid.de/fine-tune-modern-bert-in-2025).
- [ModernBERT (Answer.AI)](https://huggingface.co/answerdotai/ModernBERT-base).
- [Voyage AI embeddings docs](https://docs.voyageai.com/docs/embeddings) — Voyage-code-3, Voyage-4, Voyage-finance-2, Voyage-law-2.
- [snowflake-arctic-embed family](https://www.snowflake.com/en/blog/introducing-snowflake-arctic-embed-snowflakes-state-of-the-art-text-embedding-family-of-models/) — Apache 2.0 embedding family.
- [Text Embeddings Inference (huggingface/text-embeddings-inference)](https://github.com/huggingface/text-embeddings-inference) — Rust serving for embedding models incl. ModernBERT, Qwen3, Gemma3.

### 17.2 Production hybrid coding agents

- [Cursor homepage](https://cursor.com/) — claims and product copy.
- [Cursor Tab/Fusion blog](https://cursor.com/en/blog/tab-update) — Fusion model; 260 ms p50; 13K ctx.
- [Cursor Composer 2 paper (arXiv 2603.24477)](https://arxiv.org/pdf/2603.24477) — RL in the harness; 73.7 SWE-bench Multilingual.
- [Cursor Composer launch blog](https://cursor.com/blog/composer) — MoE coding model trained via RL; "Cheetah" prototype.
- [Cursor community: routing instead of heuristic Auto](https://forum.cursor.com/t/llm-routing-instead-of-heuristic-based-auto-selection/154050) — user-side request.
- [GitHub Copilot Auto docs](https://docs.github.com/copilot/concepts/auto-model-selection) — explicit "based on system health" framing.
- [GitHub Copilot Auto changelog (Dec 10 2025)](https://github.blog/changelog/2025-12-10-auto-model-selection-is-generally-available-in-github-copilot-in-visual-studio-code/).
- [GitHub Copilot NES blog (Nov 2025)](https://github.blog/ai-and-ml/github-copilot/evolving-github-copilots-next-edit-suggestions-through-custom-model-training/) — small custom NES model, separate from Auto.
- [Sourcegraph Cody completion lifecycle](https://sourcegraph.com/blog/the-lifecycle-of-a-code-ai-completion).
- [Continue.dev model roles docs](https://docs.continue.dev/customize/model-roles) — chat / edit / apply / autocomplete / embed / rerank.
- [Continue.dev chat role recommendations](https://docs.continue.dev/customize/model-roles/chat) — Claude Opus 4.6, Sonnet 4, GPT-5.1, Gemini 3.1 Pro, Grok-4 picks.
- [Continue.dev models guide](https://docs.continue.dev/customize/models).
- [Continue.dev configuring models, rules, tools](https://docs.continue.dev/guides/configuring-models-rules-tools).
- [Roo Code (formerly Roo-Cline)](https://github.com/aidrivencoder/Roo-Cline) — autonomous coding agent.
- [Windsurf Adaptive docs](https://docs.windsurf.com/windsurf/adaptive) — "intelligent model router"; flat per-token billing.
- [Windsurf Cascade overview](https://docs.codeium.com/plugins/cascade/cascade-overview).
- [Windsurf JetBrains changelog (Adaptive launch)](https://codeium.com/changelog/jetbrains) — April 6 2026 GA.
- [Aider architect/editor mode](https://aider.chat/2024/09/26/architect.html).
- [Cursor Composer 2 PDF (Cursor research site)](https://cursor.com/resources/Composer2.pdf).

### 17.3 Production hybrid non-coding deployments

- [Intercom Fin escalation router (Sep 2025)](https://fin.ai/research/to-escalate-or-not-to-escalate-that-is-the-question/) — fine-tuned Gemma/Qwen + encoder model reaching 98% accuracy.
- [Thumbtack CNN+LLM moderation cascade (ZenML LLMOps)](https://www.zenml.io/llmops-database/fine-tuned-llm-for-message-content-moderation-and-trust-safety) — AUC 0.93; 3.7× precision; tens of millions of messages.
- [LLM content moderation cascade (Tian Pan, April 2026)](https://tianpan.co/blog/2026-04-12-llm-content-moderation-at-scale) — 97.5% safe, 2.5% to LLM; 1.5% of naive cost; +66.5pt F1.
- [SitePoint hybrid cloud-local LLM guide (April 22 2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) — LiteLLM + Ollama + Claude reference architecture.
- [Local AI Master hybrid architecture (April 11 2026)](https://localaimaster.com/blog/hybrid-local-cloud-ai) — 85-95% local / 5-15% cloud production pattern.
- [Zylos Research: AI Agent Model Routing (March 2026)](https://zylos.ai/research/2026-03-02-ai-agent-model-routing) — survey of routing strategies and frameworks.
- [Sierra: Multi-Model Router blog (Feb 2026)](https://sierra.ai/blog/model-failover) — "Constellation of Models"; per-task ordered fallback list; congestion-aware provider selector.
- [Glean Agents Nov 2025 release notes](https://glean.com/blog/glean-agents-nov-drop-2025) — Fast vs Thinking modes; agent routing.
- [Atlassian + Glean enterprise architecture writeup (Feb 2026)](https://medium.com/@kevinrt6911/enterprise-ai-system-design-atlassian-glean-architecture-a36d80f5bc7f).
- [Agent frameworks compared (Ry Walker, Feb 2026)](https://rywalker.com/research/agent-frameworks).
- [LangGraph vs CrewAI vs AutoGen (Lushbinary, April 2026)](https://lushbinary.com/blog/langgraph-vs-crewai-vs-autogen-ai-agent-framework-comparison/).
- [Best AI Gateway & LLM Router 2026 (NeuralRouting)](https://neuralrouting.io/blog/best-ai-gateway-llm-router-2026) — comparison incl. Helicone acquisition + LiteLLM supply-chain compromise.
- [RelayPlane vs LiteLLM vs Helicone vs Bifrost (March 2026)](https://relayplane.com/blog/relayplane-vs-litellm-vs-helicone-vs-bifrost).
- [Portkey AI Gateway docs](https://portkey-ai-gateway.mintlify.app/introduction) — sub-1ms; 10B+ tokens/day in prod.
- [Complete Guide to LLM Routing (Medium, Feb 2026)](https://medium.com/%40kamyashah2018/the-complete-guide-to-llm-routing-5-ai-gateways-transforming-production-ai-infrastructure-b5c68ee6d641).
- [Patronus.ai AI agent routing guide](https://www.patronus.ai/ai-agent-development/ai-agent-routing).
- [Augment Code AI model routing guide](https://www.augmentcode.com/guides/ai-model-routing-guide).
- [Mindstudio AI: model router + cost optimization](https://www.mindstudio.ai/blog/what-is-ai-model-router-optimize-cost-llm-providers/).
- [Multi-agent system failures (FutureAGI substack)](https://futureagi.substack.com/p/why-do-multi-agent-llm-systems-fail) — MAST taxonomy; 41-86.7% failure rate.

### 17.4 Agentic, tool-aware, and cascade routing research

- [FrugalGPT (arXiv 2305.05176)](https://arxiv.org/abs/2305.05176) — original cascade.
- [AutoMix (arXiv 2310.12963)](https://arxiv.org/abs/2310.12963) — POMDP cascade with self-verification.
- [EcoAssistant (arXiv 2310.03046)](https://arxiv.org/abs/2310.03046) — code-driven cascade with execution loop; +10pt success at <50% GPT-4 cost.
- [Hybrid LLM (arXiv 2404.14618)](https://arxiv.org/abs/2404.14618) — runtime-tunable quality threshold.
- [Cascade Routing — A Unified Approach to Routing and Cascading (ICML 2025)](https://icml.cc/virtual/2025/poster/46183) — first theoretically optimal unified framework.
- [Cascade Routing PDF (arXiv 2410.10347)](https://arxiv.org/pdf/2410.10347.pdf) — +14% on SWE-bench reported.
- [BaRP — Bandit-feedback Routing with Preferences (arXiv 2510.07429)](https://arxiv.org/abs/2510.07429).
- [Online Multi-LLM Selection via Contextual Bandits (arXiv 2506.17670)](https://arxiv.org/abs/2506.17670).
- [Calibration-Gated LLM Pseudo-Observations (arXiv 2604.14961)](https://arxiv.org/abs/2604.14961).
- [Routing, Cascades, and User Choice (arXiv 2602.09902)](https://arxiv.org/html/2602.09902v1).
- [CP-Router (arXiv 2505.19970)](https://arxiv.org/abs/2505.19970) — conformal-prediction routing.
- [Fragility of Router-LLMs (arXiv 2504.07113)](https://arxiv.org/html/2504.07113v1) — DSC framework; 98% prediction-flip.
- [Inference Scaling Limits / verifier ceilings (arXiv 2411.17501)](https://arxiv.org/abs/2411.17501) — Stroebl et al.
- [Agent Psychometrics (arXiv 2604.00594)](https://arxiv.org/abs/2604.00594) — IRT for agent task difficulty.
- [Triage code-quality routing (arXiv 2604.07494)](https://arxiv.org/html/2604.07494).
- [AdaptiveLLM (arXiv 2506.10525)](https://arxiv.org/html/2506.10525) — CoT length as difficulty signal; +7.86% pass@1 at -88.9% resources.
- [Rerouting LLM Routers (arXiv 2501.01818)](https://arxiv.org/abs/2501.01818) — adversarial routing attacks.
- [PickLLM (arXiv 2412.12170)](https://arxiv.org/abs/2412.12170) — context-aware RL-assisted routing.
- [ToolLLM (arXiv 2307.16789)](https://arxiv.org/abs/2307.16789) — 16,464 RESTful APIs.
- [ToolACE (arXiv 2409.00920)](https://arxiv.org/abs/2409.00920) — function-calling data synthesis.
- [ToolACE-MCP (arXiv 2601.08276)](https://arxiv.org/abs/2601.08276) — history-aware tool routing.
- [ToolACE-R (arXiv 2504.01400)](https://arxiv.org/abs/2504.01400v1) — adaptive self-refinement.
- [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html).
- [Why LLM agents break with tools (dev.to)](https://dev.to/terzioglub/why-llm-agents-break-when-you-give-them-tools-and-what-to-do-about-it-f5).
- [ThinkPRM (mukhal/ThinkPRM)](https://github.com/mukhal/thinkprm) — 1.5B/7B/14B PRMs at `launch/ThinkPRM-{1.5B,7B,14B}` on HF.
- [ThinkPRM paper (arXiv 2504.16828)](https://arxiv.org/abs/2504.16828) — TMLR.
- [DreamPRM-Code (arXiv 2512.15000)](https://arxiv.org/abs/2512.15000) — 80.9 pass@1 on LiveCodeBench.
- [FunPRM (arXiv 2601.22249)](https://arxiv.org/abs/2601.22249).
- [CodePRM (ACL 2025 findings)](https://aclanthology.org/2025.findings-acl.428.pdf).
- [AgentPRM (arXiv 2511.08325)](https://arxiv.org/abs/2511.08325).
- [Accurate Failure Prediction Does Not Imply Effective Failure Prevention (arXiv 2602.03338)](https://arxiv.org/abs/2602.03338).
- [Token-Budget-Aware Pool Routing (arXiv 2604.09613)](https://arxiv.org/abs/2604.09613) — infrastructure-tier routing; 17-39% GPU savings.
- [LangGraph multi-agent router knowledge base](https://docs.langchain.com/oss/python/langchain/multi-agent/router-knowledge-base).
- [LangGraph trajectory evals](https://docs.langchain.com/langsmith/trajectory-evals).
- [Reasoning on a Budget survey (arXiv 2507.02076)](https://arxiv.org/abs/2507.02076).
- [Dynamic Speculative Agent Planning (arXiv 2509.01920)](https://arxiv.org/abs/2509.01920).
- [Difficulty-Aware Agent Orchestration HTML (arXiv 2509.11079)](https://arxiv.org/html/2509.11079v1).
- [Self-Repair surveys / Rerouting / failure attribution (arXiv 2505.00212)](https://arxiv.org/abs/2505.00212).

### 17.5 Router evaluation, benchmarks, and calibration

- [RouterBench (arXiv 2403.12031)](https://arxiv.org/abs/2403.12031) — 405k inference outcomes; 70/30 split methodology.
- [RouterBench HTML v2](https://arxiv.org/html/2403.12031v2).
- [RouterBench OpenReview PDF](https://openreview.net/pdf?id=IVXmV8Uxwh).
- [RouterBench code (withmartian/routerbench)](https://github.com/withmartian/routerbench).
- [RouterArena (arXiv 2510.00202)](https://arxiv.org/abs/2510.00202) — 9 domains × 44 categories; live leaderboard.
- [RouterArena code (RouteWorks/RouterArena)](https://github.com/RouteWorks/RouterArena).
- [RouterArena leaderboard](https://routeworks.github.io/) — R2-Router #1 (71.60), vLLM-SR #2 (67.23), MIRT-BERT #3 (66.86); RouteLLM 11/12 (48.1).
- [RouterEval (arXiv 2503.10657)](https://arxiv.org/abs/2503.10657) — 200M records, 8500 LLMs.
- [LLMRouterBench (ynulihao/LLMRouterBench)](https://github.com/ynulihao/LLMRouterBench/blob/main/evaluation/README.md) — 27+ benchmarks unified.
- [MixEval-X (arXiv 2410.13754)](https://arxiv.org/abs/2410.13754) — multimodal; 0.98 corr to human preference.
- [Opper LLM router latency benchmark 2026](https://opper.ai/blog/llm-router-latency-benchmark-2026) — OpenRouter 70 ms faster than OpenAI direct on TTFT; geography 2× model choice.
- [Martian "Up and to the Left" cost-quality case study](https://withmartian.com/post/up-and-to-the-left) — 52.4% error reduction + 92% cost reduction case.
- [W&B router training & evaluation report (CPT, PGR examples)](https://wandb.ai/byyoung3/ML_NEWS3/reports/How-to-train-and-evaluate-an-LLM-router--Vmlldzo5MjU0MTA1).
- [EquiRouter / routing collapse (arXiv 2602.03478)](https://arxiv.org/html/2602.03478v1).
- [Win-rate vs Best Single baseline study (arXiv 2601.07206)](https://arxiv.org/html/2601.07206v1).
- [CP-Router uncertainty-aware routing (arXiv 2505.19970)](https://arxiv.org/abs/2505.19970).
- [Adaptive Temperature Scaling (arXiv 2409.19817)](https://arxiv.org/abs/2409.19817) — +10-50% over baseline.
- [Calibration Across Layers (arXiv 2511.00280)](https://arxiv.org/abs/2511.00280) — calibration direction in residual stream.
- [Reliability diagrams + ECE explainer (YouTube)](https://www.youtube.com/watch?v=NDY2fH1FitQ).
- [Per-model Brier + reliability comprehensive eval (arXiv 2603.20895)](https://arxiv.org/html/2603.20895v2).
- [Position bias in LLM judges (arXiv 2406.07791)](https://arxiv.org/html/2406.07791v4).
- [Benchmark contamination audit framework (arXiv 2603.21636)](https://arxiv.org/html/2603.21636v1).
- [Goodhart's Law on routing metrics](https://chacocanyon.com/pointlookout/230308.shtml).
- [SWE-bench](https://www.swebench.com).
- [LiveCodeBench](https://livecodebench.github.io) — continuous-refresh; contamination-resistant.
- [BigCodeBench](https://bigcode-bench.github.io).
- [Aider Polyglot (Epoch AI)](https://epoch.ai/benchmarks/aider-polyglot).
- [Anthropic Mythos preview (April 2026)](https://red.anthropic.com/2026/mythos-preview/).
- [Online vs offline LLM evaluation (Rhesis.ai)](https://rhesis.ai/post/offline-vs-online-evaluation-llm-applications).
- [A/B testing AI outputs in production (Render.com)](https://render.com/articles/best-practices-for-running-ai-output-a-b-test-in-production) — sticky sessions, circuit breakers, configuration as data.
- [Router monitoring observability (ManageEngine)](https://www.manageengine.com/network-monitoring/tech-topics/what-is-router-monitoring.html).
- [Hybrid Preferences: routing instances for human vs AI feedback (Allen AI)](https://allenai.org/blog/hybrid-preferences-learning-to-route-instances-for-human-vs-ai-feedback-6bed4b68c0a2).
- [DeepSeek/Gemini deep-think routing guide](https://www.digitalapplied.com/blog/gemini-3-deep-think-reasoning-benchmarks-guide).
- [Routing efficacy / large-scale unified eval (arXiv 2603.20895)](https://arxiv.org/html/2603.20895v2).

### 17.6 Local inference engines and quantization references

- [LM Studio Tool Use docs](https://lmstudio.ai/docs/developer/openai-compat/tools).
- [llama.cpp function-calling docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md).
- [LiteLLM Router](https://docs.litellm.ai/docs/routing).
- [vLLM supported models](https://docs.vllm.ai/en/latest/models/supported_models/).
- [GPU vs CPU inference speed/cost analysis (GMI Cloud)](https://www.gmicloud.ai/blog/gpu-inference-vs-cpu-inference-speed-cost-and-scalability).
- [ONNX ML support reference (ST Edge AI)](https://stedgeai-dc.st.com/assets/embedded-docs/onnx_ml_support.html).

### 17.7 Local coding model references

- [Qwen3-Coder-30B-A3B-Instruct (HF)](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct).
- [Qwen3.6-27B (HF)](https://huggingface.co/Qwen/Qwen3.6-27B).
- [Qwen3.6-35B-A3B (HF)](https://huggingface.co/Qwen/Qwen3.6-35B-A3B).
- [Devstral-Small-2-24B-Instruct-2512 (HF)](https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512).

(Note: §17 deduplicates against §15 above; URLs that appeared in §15 are retained there as "most-cited primaries" and not repeated here unless the new research adds material like an updated leaderboard.)

---

*End of architecture document.*
