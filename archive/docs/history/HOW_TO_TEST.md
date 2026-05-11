# How to test the hybrid local/cloud router

> **TL;DR.** A local proxy at `http://127.0.0.1:8787` exposes 7 routing strategies as 7 OpenAI-compatible "models". opencode is already configured to see all 7. Pick one in opencode's model picker, send a prompt, and the proxy decides whether to answer with **`qwen3-coder:30b` (local)** or **`gpt-5.5` (cloud)**. The decision is printed at the top of every reply and logged to `router/logs/decisions.jsonl`.

## What was set up overnight

| component | location | what it is |
|---|---|---|
| Local model | Ollama | `qwen3-coder:30b` (18 GB, MoE, ~3 B active params) |
| Tiny router model | Ollama | `qwen3:0.6b` (522 MB, used by Strategy 5) |
| Embedding model | Ollama | `nomic-embed-text` (274 MB, used by Strategy 6) |
| Cloud model | OpenAI | `gpt-5.5` (key read from `.env`'s `OPEN_AI_API_KEY`) |
| Router proxy | `router/` | single-file Node ES module, zero deps, port 8787 |
| opencode config | `~/.config/opencode/opencode.json` | adds the `hybrid-router` provider with 7 model entries |
| Decision log | `router/logs/decisions.jsonl` | one JSON record per request |
| Test sweep results | `router/test/RESULTS.md` | matrix of which strategy chose what for which prompt |

## 60-second start

1. **Make sure Ollama is up** (it should be — the install survived restart):
   ```sh
   ollama list   # you should see qwen3-coder:30b, qwen3:0.6b, nomic-embed-text
   ```

2. **Make sure the router proxy is up**. If it died with the terminal, restart it:
   ```sh
   cd /Users/sanchitmonga/development/ODLM/MONOREPOOO/CODING/opencode/router
   ./start.sh                # foreground
   #   or, background:
   nohup ./start.sh > /tmp/router.log 2>&1 &
   ```

3. **Sanity check**:
   ```sh
   curl -s http://127.0.0.1:8787/healthz | jq
   # should show local: reachable=true, cloud: reachable=true, key_present=true
   ```

4. **Use it from opencode**. Two equivalent ways:
   - Interactive: `opencode`, then `/model`, then pick one of `hybrid-router/router/<strategy>`.
   - Scripted: `opencode run --model hybrid-router/router/heuristic "your prompt"`.

5. **Watch decisions live in another terminal**:
   ```sh
   tail -f /Users/sanchitmonga/development/ODLM/MONOREPOOO/CODING/opencode/router/logs/decisions.jsonl | jq
   ```

## The 7 routers

In the opencode model picker they appear in this order (numbered for clarity):

| # | model id (in opencode) | what it does | when it's interesting |
|---|---|---|---|
| 1 | `hybrid-router/router/always-local` | sends every request to `qwen3-coder:30b` | baseline for "what does local-only feel like?" |
| 2 | `hybrid-router/router/always-cloud` | sends every request to `gpt-5.5` | baseline for "what does cloud-only feel like and cost?" |
| 3 | `hybrid-router/router/rules` | regex + token + code-block rules | totally deterministic; easy to reason about |
| 4 | `hybrid-router/router/heuristic` | weighted score across multiple signals | recommended default — works on most prompts |
| 5 | `hybrid-router/router/llm-classifier` | calls `qwen3:0.6b` to classify SIMPLE/COMPLEX | adds ~50–200 ms but smarter than keyword matching |
| 6 | `hybrid-router/router/embedding-knn` | embeds the query, kNN over 50 labelled examples | best for prompts that look unlike rules but match a known pattern |
| 7 | `hybrid-router/router/cascade` | trust heuristic when confident, otherwise tie-break with the LLM classifier | recommended **smart** default — best blend |

Force a backend for debugging by appending `!local` or `!cloud` (e.g. `hybrid-router/router/heuristic!cloud`).

## What you'll see in opencode

Every assistant turn starts with a one-line banner:

```
[router] strategy=heuristic → LOCAL (qwen3-coder:30b) | conf=0.95 | heuristic[score=12.4 >=35? → local] tok=68(+0.7) -local-kw=1(-18)

Sure — here's the renamed snippet:
```javascript
const bar = 1;
```
```

The banner exposes everything: which strategy ran, what it picked, its confidence, and the human-readable reason (which signal pushed the decision). Disable with `ROUTER_BANNER=0` in the env if you don't want it in the chat.

## Suggested prompts to try

The point of the demo is to see the routers actually disagree. Here is a curated list — type each into opencode after picking the router from the table above.

### Should obviously stay local
- `Rename the variable foo to bar in this snippet: const foo = 1;`
- `Fix the typo: parseRequst → parseRequest`
- `Write a one-line JS function for Fibonacci`
- `Add a JSDoc comment to function formatDate(d) { return d.toISOString().slice(0,10); }`
- `Convert this for loop to a .map(): for (const x of arr) result.push(x*2)`
- `quick: what does Array.prototype.flat() do?`

### Should obviously go cloud
- `Design a multi-tenant authentication system with row-level security in Postgres. Walk through the schema, JWT structure, and edge cases.`
- `Plan a zero-downtime migration of our user table from MySQL to Postgres, including dual-write strategy and verification.`
- `Architect a streaming ingestion pipeline that handles 100k events/sec with at-least-once semantics and replay capability.`
- `Comprehensive review of this PR: correctness, performance, security, observability, test coverage, naming, public API.`

### Borderline (where strategies will disagree)
- `Write a Jest unit test for this function that covers empty input, one element, and a typical case` — embedding-kNN may say cloud, rules will say local.
- `Diagnose this performance regression: p99 latency jumped from 50ms to 800ms after our last deploy.` — heuristic and llm-classifier should both say cloud, rules will say local because no big-token / code-block trigger.

To run all of these mechanically and produce a side-by-side table:

```sh
cd /Users/sanchitmonga/development/ODLM/MONOREPOOO/CODING/opencode/router
node test/run-tests.mjs
open test/RESULTS.md          # pre-built report; see also test/RESULTS.json
```

## Reading the decision log

Tail the file:

```sh
tail -f /Users/sanchitmonga/development/ODLM/MONOREPOOO/CODING/opencode/router/logs/decisions.jsonl | jq
```

Each record:

```json
{
  "ts": "2026-04-26T07:14:22.123Z",
  "id": "a1b2c3d4",
  "strategy": "heuristic",
  "choice": "local",
  "reason": "heuristic[score=12.4 >=35? → local] …",
  "confidence": 0.95,
  "backend_model": "qwen3-coder:30b",
  "decide_ms": 0,
  "prompt_tokens_est": 68,
  "total_ms": 1340,
  "stream_chunks": 47,
  "success": true
}
```

Quick aggregations:

```sh
# Cost mix per strategy
jq -r 'select(.success) | "\(.strategy)\t\(.choice)"' router/logs/decisions.jsonl \
  | sort | uniq -c | sort -rn

# p50 / p95 latency per strategy
jq -r 'select(.success) | "\(.strategy)\t\(.total_ms)"' router/logs/decisions.jsonl \
  | datamash -g 1 perc:50 2 perc:95 2 count 2
```

## When something goes wrong

| symptom | what to check |
|---|---|
| `proxy not reachable at http://127.0.0.1:8787` | Run `./start.sh` in `router/`. Confirm `lsof -i :8787` shows a node process. |
| `local: reachable=false` in `/healthz` | Ollama daemon not up. `ollama serve` (it usually starts on boot via the menu bar app). |
| `cloud: reachable=false` | Wrong / expired API key. Check `cat .env` (key is `OPEN_AI_API_KEY`). |
| Cloud answers are empty / `finish_reason=length` with `reasoning_tokens` only | gpt-5.5 burned the budget on hidden reasoning. Bump `output` in `~/.config/opencode/opencode.json` for the cloud-tier model entry, or use a non-reasoning fallback (set `CLOUD_MODEL=gpt-5` in start.sh). |
| Local answers are slow on first request | Ollama is loading the 18 GB model into RAM. ~10–30 s the first time, sub-second after. |
| Banner is annoying in chat | `ROUTER_BANNER=0 ./start.sh` |
| Want to force a single backend for one prompt | Append `!local` or `!cloud` to the model id in opencode (`/model hybrid-router/router/heuristic!cloud`). |

## Where to look for more

- Architecture rationale: `HYBRID_LOCAL_CLOUD_ROUTING_ARCHITECTURE.md` (the comprehensive plan that informed this implementation).
- Router source: `router/server.mjs` (proxy + decision plumbing) and `router/strategies.mjs` (pure routing logic — read this first if you want to add an Option 8).
- Generated test results: `router/test/RESULTS.md` and `router/test/RESULTS.json` (re-run `node router/test/run-tests.mjs` to refresh).
- Runtime decision log: `router/logs/decisions.jsonl`.
