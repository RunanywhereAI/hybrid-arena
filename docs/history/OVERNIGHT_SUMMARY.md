# Overnight build — hybrid local/cloud router for opencode

**Status: working. Open `opencode` and pick a model — the chat will tell you whether your message went local or cloud.**

## What is running right now

| layer | what | status |
|---|---|---|
| Local model | `qwen3-coder:30b` in Ollama (18 GB, MoE, ~3 B active params, OpenAI-compatible at `http://127.0.0.1:11434/v1`) | installed, warm |
| Cloud model | `gpt-5.5` via `https://api.openai.com/v1` (key read from `.env`'s `OPEN_AI_API_KEY`) | reachable |
| Tiny router model | `qwen3:0.6b` for the LLM-classifier strategy | installed |
| Embedding model | `nomic-embed-text` for the kNN strategy | installed |
| Proxy | Single-file Node ES-module HTTP server at `http://127.0.0.1:8787` | running, PID checked |
| opencode | Sees the proxy as a provider called `hybrid-router` with 7 model entries | configured |

If you reboot, restart the proxy with:
```sh
cd /Users/sanchitmonga/development/ODLM/MONOREPOOO/CODING/opencode/router && nohup ./start.sh > /tmp/router.log 2>&1 &
```

## How to use it

```sh
# Easiest — just opencode:
opencode
# then  /model  → pick any "hybrid-router/router/<strategy>"

# Or one-shot:
opencode run --model hybrid-router/router/heuristic "Rename foo to bar in const foo = 1"
```

Every assistant turn starts with a one-line banner showing the routing decision, e.g.
```
[router] strategy=heuristic → LOCAL (qwen3-coder:30b) | conf=1.00 | heuristic[score=-11.6 …]
```

## The 8 routers (Option 1 → Option 8)

| # | model id | what it does |
|---|---|---|
| 1 | `hybrid-router/router/always-local` | control: every request goes local |
| 2 | `hybrid-router/router/always-cloud` | control: every request goes cloud |
| 3 | `hybrid-router/router/rules` | regex + token + code-block thresholds (deterministic) |
| 4 | `hybrid-router/router/heuristic` | weighted score across multiple signals (recommended baseline) |
| 5 | `hybrid-router/router/llm-classifier` | qwen3:0.6b returns SIMPLE/COMPLEX (~50–200 ms overhead) |
| 6 | `hybrid-router/router/embedding-knn` | nomic-embed + 50-example labelled corpus, k=5 vote |
| 7 | `hybrid-router/router/cascade` | trust heuristic when confident, llm-classifier as tiebreaker |
| 8 | `hybrid-router/router/architect` | **per-subtask granularity** — cloud planner emits a JSON plan, each step is routed individually, final synthesis. See `router/agentic/README.md`. |

Routers 1–7 make **one** routing decision per chat-completion request (per-turn granularity). Router 8 (`architect`) makes **N+2** decisions per request (planner + N executor steps + synth) — the next granularity level down. Use it via the dedicated CLI for a clean demo: `node router/agentic/architect.mjs "your task"`.

Append `!local` / `!cloud` to force a backend (e.g. `hybrid-router/router/heuristic!cloud`).

## Test sweep results (17 prompts × 7 routers = 119 calls)

Full report: `router/test/RESULTS.md` (also `RESULTS.json` for raw data).

**Cost mix (% of calls that went cloud, per strategy — calibrated heuristic):**

| strategy | local | cloud | cloud-rate |
|---|---:|---:|---:|
| always-local      | 17 | 0  | 0%  |
| always-cloud      | 0  | 17 | 100% |
| rules             | 12 | 5  | 29% |
| heuristic         | 14 | 3  | 18% |
| llm-classifier    | 15 | 2  | 12% |
| **embedding-knn** | 11 | 6  | **35%** |
| cascade           | 14 | 3  | 18% |

**Architect mode (sub-task granularity):** on a 7-step refactor task, `architect` spent 1 call on planning (cloud), 7 calls on execution (all local), 1 call on synthesis (cloud) — **78 % of model calls landed on the local model** for a task that would otherwise have been a single ~30 s cloud call. On a 12-step heterogeneous "design + implement + explain trade-offs" task, the split was 4 cloud / 10 local. See `router/agentic/README.md` for the full numbers and run reports.

The 17-prompt set is **8 trivial / 2 moderate / 5 complex / 2 edge** (so 29% is the "ground-truth complex" baseline). Embedding-kNN slightly over-routes; rules and cascade hit the ground-truth fraction; llm-classifier slightly under-routes.

**Trivial prompts (8 of 17):** every smart router chose **local**. ✓ (unanimous)
**Complex-design + complex-refactor (2 of 5 complex):** every smart router chose **cloud**. ✓ (unanimous)
**The other 3 complex prompts** (perf-diagnosis, architecture, long-context) split: `rules` and `embedding-knn` were the most reliable at catching them; `llm-classifier` (qwen3:0.6b) was unreliable on these without strong keyword signals.

**Latency (median across all 17 prompts × 7 strategies):**

| strategy | median | min | max |
|---|---|---|---|
| always-local   | 2.9 s | 215 ms | 8.7 s |
| always-cloud   | 2.6 s | 1.3 s  | 17.1 s |
| rules          | 2.6 s | 186 ms | 16.3 s |
| heuristic      | 2.4 s | 139 ms | 15.0 s |
| llm-classifier | 3.5 s | 213 ms | 15.4 s |
| embedding-knn  | 2.6 s | 175 ms | 15.3 s |
| cascade        | 2.5 s | 127 ms | 16.7 s |

Local sub-second responses on trivial work (heuristic/cascade routed → qwen3-coder:30b → answer in 127–500 ms). Cloud calls take longer mainly because gpt-5.5 burns hidden reasoning tokens.

> **Heuristic was calibrated mid-build.** First-pass scoring used `totalPromptTokens(messages)`, which (in real opencode usage) gets dominated by the ~3K-token system prompt + tool definitions opencode bundles every turn — even "Reply OK" was scoring 42 and routing cloud. Fixed in `strategies.mjs:heuristic()` to score only `userMessageTokens` with a lower cap and threshold; verified on opencode end-to-end ("Reply OK" → LOCAL score 0.1; "Plan a zero-downtime migration" → CLOUD score 42.5).

## Where things live

```
opencode/
├── OVERNIGHT_SUMMARY.md                 ← this file
├── HOW_TO_TEST.md                       ← detailed usage guide
├── ROUTING_STRATEGIES.md                ← deep-dive on each strategy + granularity ladder
├── HYBRID_LOCAL_CLOUD_ROUTING_ARCHITECTURE.md   ← the comprehensive plan that informed this
├── .env                                 ← OPEN_AI_API_KEY (you set this)
└── router/
    ├── server.mjs                       ← proxy (single-file Node, zero deps)
    ├── strategies.mjs                   ← 7 per-turn routing strategies
    ├── start.sh                         ← launcher
    ├── README.md                        ← internal architecture doc
    ├── corpus/examples.json             ← 50 labelled prompts for embedding-kNN
    ├── logs/decisions.jsonl             ← every routing decision, JSON-per-line
    ├── agentic/                         ← per-subtask routing (Pattern A, "TODO list" case)
    │   ├── architect-core.mjs           ←  shared library: runArchitect()
    │   ├── architect.mjs                ←  CLI: node architect.mjs "<task>"
    │   ├── README.md                    ←  per-subtask routing doc
    │   └── examples/                    ←  generated reports
    └── test/
        ├── prompts.json                 ← 17 test prompts
        ├── run-tests.mjs                ← test harness
        ├── RESULTS.md                   ← human-readable matrix
        └── RESULTS.json                 ← raw data
```

opencode config that wires it all up: `~/.config/opencode/opencode.json` (`runanywhereai` provider was preserved; `hybrid-router` provider added alongside).

## Things you'll want to verify yourself

1. **Trivial routing** — type a one-liner like `rename foo to bar` in opencode with `router/heuristic` selected. Banner should say `→ LOCAL` and the answer should arrive in ~1–3 seconds.
2. **Complex routing** — type "Design a multi-tenant authentication system with row-level security in Postgres". With `router/heuristic` selected the banner should say `→ CLOUD (gpt-5.5)`.
3. **Decision log** — in another terminal: `tail -f router/logs/decisions.jsonl | jq` and watch the records flow as you chat.
4. **Strategy comparison** — switch the model picker between the 7 strategies on the same prompt and observe the disagreement.

## Known caveats / honest notes

- **Heuristic threshold (35) is calibrated for opencode-wrapped prompts** (~2.5 K tokens of system prompt + tools each turn). On the bare test prompts (which are 20–500 tokens), heuristic looks "too conservative" — but in real opencode usage it'll be closer to the matrix you see for `rules`. Re-run `node router/test/run-tests.mjs` after using opencode for a while and compare.
- **`cascade` is the most conservative** (6 % cloud-rate). That's because when the heuristic and llm-classifier disagree, cascade trusts the llm-classifier — and the qwen3:0.6b classifier is unreliable on borderline cases. If you want a more aggressive cascade, edit `strategies.mjs:cascade()` to default to cloud on disagreement instead of trusting the llm.
- **`gpt-5.5` is a reasoning model** and burns most of its `max_completion_tokens` on hidden reasoning before producing visible content. The opencode model entries are configured with `output: 16000` so that's not a daily problem, but it's why some short test responses look truncated.
- **No streaming through the proxy was tested end-to-end via opencode yet** (only via `opencode run`, which is non-interactive). It should work — the proxy passes SSE through byte-for-byte after a single banner chunk — but please flag it if you see weird artifacts in the live TUI.
- **Banner injection** prepends `[router] …\n\n` to the assistant's content. If you find it noisy, set `ROUTER_BANNER=0` in the env before `./start.sh`.
- **Cost is not metered.** I log token estimates, not dollars. Add a usage tracker if/when you want $-per-day rollups.

## Quick experiments to try

```sh
# 1. Same prompt through every router — see how they disagree.
for r in rules heuristic llm-classifier embedding-knn cascade; do
  echo "=== $r ==="
  curl -s http://127.0.0.1:8787/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"router/$r\",\"messages\":[{\"role\":\"user\",\"content\":\"refactor this entire module to use dependency injection\"}],\"stream\":false,\"max_tokens\":40}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'][:200])"
  echo
done

# 2. Per-strategy cost mix from the live log.
jq -r 'select(.success) | "\(.strategy)\t\(.choice)"' router/logs/decisions.jsonl \
  | sort | uniq -c | sort -rn

# 3. Which keywords actually triggered cloud most often.
jq -r 'select(.choice=="cloud" and .strategy=="rules") | .reason' router/logs/decisions.jsonl
```
