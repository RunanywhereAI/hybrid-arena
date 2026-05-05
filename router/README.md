# opencode hybrid router

An OpenAI-compatible HTTP proxy that sits in front of opencode. Each request is routed to either a local Ollama model (`qwen3-coder:30b`) or a cloud OpenAI model (`gpt-5` / `gpt-4o`) using one of seven pluggable strategies. opencode never knows the difference — it just sees one OpenAI-compatible endpoint with a model picker.

```
opencode  ──►  this proxy (:8787)  ──┬──►  Ollama  /v1/chat/completions  (local)
                                     └──►  OpenAI  /v1/chat/completions  (cloud)
```

Every decision is logged to `logs/decisions.jsonl` and (by default) a one-line `[router]` banner is prepended to the response so you can see in opencode itself which backend handled the message.

## Files

```
router/
├── server.mjs          single-file Node ES-module HTTP proxy (zero deps)
├── strategies.mjs      seven routing strategies (decide() functions)
├── corpus/examples.json   50 labelled prompts for the embedding-kNN strategy
├── start.sh            launcher that loads ../.env and exports defaults
├── package.json
├── logs/decisions.jsonl   created at runtime — one JSON record per request
└── test/
    ├── prompts.json     ~17 trivial-to-complex test prompts
    ├── run-tests.mjs    runs every prompt through every strategy → RESULTS.md
    ├── RESULTS.md       generated report
    └── RESULTS.json     raw matrix for further analysis
```

## Routing strategies

The strategy is selected by the `model` field of the request: `model: "router/<strategy>"`.

| # | strategy | what it does | latency overhead |
|---|---|---|---|
| 1 | `always-local`   | Control: every request goes local. | ~0ms |
| 2 | `always-cloud`   | Control: every request goes cloud. | ~0ms |
| 3 | `rules`          | Hard-coded keyword + token + code-block rules. Deterministic. | <1ms |
| 4 | `heuristic`      | Weighted score across token count, code blocks, complexity keywords, tool count. | <1ms |
| 5 | `llm-classifier` | One `qwen3:0.6b` call asks "SIMPLE or COMPLEX?". | ~50–200ms |
| 6 | `embedding-knn`  | Embeds the user prompt with `nomic-embed-text` and votes among 5 nearest labelled examples. | ~30–80ms |
| 7 | `cascade`        | Trust heuristic when confident; fall back to llm-classifier when borderline. | <1ms most of the time, ~150ms on tie |

Append `!local` or `!cloud` to force a backend regardless of decision (useful for debugging — e.g. `model: "router/heuristic!cloud"`).

## Quick start

```bash
# 1. Make sure Ollama is running and you have the models.
ollama list  # should show qwen3-coder:30b, qwen3:0.6b, nomic-embed-text

# 2. Add your OpenAI key to ../.env (already done):
#    OPEN_AI_API_KEY=sk-…

# 3. Start the proxy:
./start.sh

# 4. Sanity check:
curl http://127.0.0.1:8787/healthz | jq
curl http://127.0.0.1:8787/v1/models | jq

# 5. Run an end-to-end test sweep across all strategies & prompts:
node test/run-tests.mjs
open test/RESULTS.md

# 6. In opencode, point the model at router/<strategy>. See ../HOW_TO_TEST.md.
```

## Decision log format

Each line of `logs/decisions.jsonl`:

```json
{
  "ts": "2026-04-26T07:14:22.123Z",
  "id": "a1b2c3d4",
  "strategy": "heuristic",
  "choice": "local",
  "forced": null,
  "reason": "heuristic[score=12.4 >=35? → local] tok=68(+0.7) -local-kw=1(-18)",
  "confidence": 0.95,
  "backend_model": "qwen3-coder:30b",
  "decide_ms": 0,
  "prompt_tokens_est": 68,
  "prompt_preview": "Rename the variable foo to bar in src/utils.ts",
  "stream": true,
  "stream_chunks": 47,
  "stream_bytes": 5421,
  "total_ms": 1340,
  "success": true
}
```

Tail it live: `tail -f logs/decisions.jsonl | jq`.

## Configuration via env vars

Everything has a sensible default — only `OPEN_AI_API_KEY` is mandatory for cloud routing.

| var | default | meaning |
|---|---|---|
| `PORT` | `8787` | HTTP port |
| `LOCAL_BASE` | `http://127.0.0.1:11434/v1` | Ollama OpenAI-compatible base |
| `LOCAL_MODEL` | `qwen3-coder:30b` | Ollama model used when `choice=local` |
| `ROUTER_MODEL` | `qwen3:0.6b` | Small model for `llm-classifier` |
| `CLOUD_BASE` | `https://api.openai.com/v1` | Cloud base URL |
| `CLOUD_MODEL` | `gpt-5` | Cloud model used when `choice=cloud` |
| `CLOUD_FALLBACK_MODEL` | `gpt-4o` | Used if `gpt-5` returns 404 |
| `CLOUD_API_KEY` | `OPENAI_API_KEY` ‖ `OPEN_AI_API_KEY` | Cloud auth |
| `ROUTER_BANNER` | `1` | Set to `0` to disable the `[router] …` banner |
| `ROUTER_LOG_DIR` | `./logs` | Where `decisions.jsonl` lives |

## Notes & limitations (read these)

- **Banner injection.** By default the proxy prepends a `[router] strategy=… → …` line to the first content delta. Disable with `ROUTER_BANNER=0`. It pollutes the model output, but the trade-off is you can SEE the routing decision in opencode without leaving the chat.
- **Tool-call passthrough.** `tools` and `tool_calls` are forwarded as-is. Both Ollama (Qwen3-Coder) and OpenAI support OpenAI-style tools, so this works.
- **Streaming.** SSE is forwarded byte-for-byte after the optional banner chunk. If the upstream errors mid-stream, the connection is closed cleanly.
- **Cloud model fallback.** If `gpt-5` 404s, the proxy automatically retries with `gpt-4o`. Logged and reflected in the `reason`.
- **No auth on the proxy itself.** Bind is `127.0.0.1` only — do not expose this to a network without adding auth.
- **Strategies are stateless.** They make no assumption about prior turns; each call is decided on the latest user message + token count + tools. This is deliberate (faster, easier to reason about); it also means the `cascade` strategy does not retry across turns.
