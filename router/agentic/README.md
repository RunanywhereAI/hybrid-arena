# `router/agentic/` — per-subtask hybrid routing (granularity beyond per-turn)

Per-turn routing (one decision per chat-completion request) is what the rest of the proxy does. **This directory is the next granularity step down** — when a bigger model decomposes a task into sub-steps, each sub-step gets its own routing decision, so simple steps run locally and only architecturally-heavy steps go to the cloud.

This is **Pattern A — Architect/Editor split** from `../../ROUTING_STRATEGIES.md` (the "TODO list" use-case).

## What's in here

```
router/agentic/
├── architect-core.mjs   library: runArchitect(opts) — the pipeline
├── architect.mjs        CLI: node architect.mjs "your task" → markdown report
├── examples/            generated reports from runs
└── README.md            this file
```

`server.mjs` imports `architect-core.mjs` and exposes the same pipeline as a special pseudo-strategy: `model: router/architect`. So you have **three ways** to run the per-subtask flow.

## The pipeline

```
                       ┌────────────────────────────┐
                       │ Phase 1 ─ PLANNER          │
   user task ─────────▶│   model: router/always-cloud
                       │   prompts the cloud model  │
                       │   to emit a JSON plan      │
                       └────────────┬───────────────┘
                                    │ list of steps
                                    │   {index, title, task, kind,
                                    │    rationale, depends_on,
                                    │    expected_output, router_hint}
                                    ▼
                       ┌────────────────────────────┐
                       │ Phase 2 ─ EXECUTOR         │
                       │   for each step:           │
                       │     model = router/heuristic
                       │     if step.router_hint=local
                       │        ⇒ router/always-local
                       │     if step.router_hint=cloud
                       │        ⇒ router/always-cloud
                       │   → individual decision    │
                       │     per step               │
                       └────────────┬───────────────┘
                                    │ stepResults[]
                                    ▼
                       ┌────────────────────────────┐
                       │ Phase 3 ─ SYNTHESIS        │
                       │   model: router/heuristic  │
                       │   stitches step outputs    │
                       │   into one final answer    │
                       └────────────────────────────┘
```

Each box is one chat-completion request to the proxy. The router decides (per request) whether each piece runs local or cloud. The end-to-end behavior:

- Planner is **always cloud** — `gpt-5.5` is the one that has to decompose well.
- Executor steps **vote per-step**. A "rename a variable" step routes local; a "design the system" step (or a step the planner hinted as `cloud`) routes cloud. The heuristic does the actual choosing for `auto`-hinted steps.
- Synthesiser routes via `heuristic` too, but in practice almost always lands on cloud because by then the input has all the step outputs concatenated, which the heuristic correctly recognises as a "stitch a complex thing together" task.

## Three ways to use it

### 1. CLI (recommended for testing the granularity)

```sh
cd router/agentic
node architect.mjs "your task here"
```

Writes a Markdown report to `examples/<timestamp>-<slug>.md` with the plan, per-step routing decision, per-step output, and final synthesised answer. Stdout shows live progress:

```
Phase 1 ▸ planning…
   planner → CLOUD (gpt-5.5) 12.7s
   plan        : 7 steps
     [1] (search,  hint=local) Inspect pricing implementation
     [2] (edit,    hint=local) Rename total to subtotal
     ...
Phase 2 ▸ executing…
   step  1 (search   ) → 🖥 local (qwen3-coder:30b) 15.4s  hint=local
   step  2 (edit     ) → 🖥 local (qwen3-coder:30b) 0.9s   hint=local
   ...
Phase 3 ▸ synthesising…
   synth → CLOUD (gpt-5.5) 4.7s

✓ done  7 executor steps  •  7 local / 1 cloud  •  40.5s wall  •  9 model calls
```

Flags:

| flag | default | what |
|---|---|---|
| `--planner <model>` | `router/always-cloud` | model id used for Phase 1 |
| `--executor <model>` | `router/heuristic` | model id used for Phase 2 (per step) |
| `--synthesizer <model>` | `router/heuristic` | model id used for Phase 3 |
| `--max-steps <n>` | `12` | cap on plan length |
| `--dry-run` | `false` | plan only, skip execution |
| `--out <path>` | `examples/<auto>.md` | report destination |
| `--proxy <url>` | `http://127.0.0.1:8787` | proxy base URL |

### 2. Direct API (`router/architect`)

```sh
curl -s http://127.0.0.1:8787/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "router/architect",
    "stream": false,
    "messages": [{"role": "user", "content": "your task"}]
  }' | jq -r '.choices[0].message.content'
```

The proxy runs the full pipeline and returns the synthesized answer in a normal OpenAI-compatible response, plus extra response headers:

```
X-Router-Strategy: architect
X-Router-Choice:   architect
X-Router-Backend:  (plan/execute/synth)
X-Architect-Steps: 5      ← number of plan steps
X-Architect-Local: 6      ← steps + synth that routed local
X-Architect-Cloud: 0      ← steps + synth that routed cloud (planner is separate)
```

Streaming mode (`stream: true`) emits SSE chunks with live progress text — Phase headers, per-step decisions, and finally the synthesised answer. Same response headers.

### 3. From opencode (caveat)

`router/architect` shows up in opencode's model picker (model id `hybrid-router/router/architect`). But opencode's default agent loop sees the architect's markdown response and tries to *act on it* (apply edits, run tools, etc.), which triggers more chat-completion calls — re-invoking the architect each loop iteration. Not what you want.

**Workaround:** invoke architect mode in a non-build context — e.g. via `opencode run --print` for a single-turn output, or via a custom `plan`-style agent that doesn't enter a tool-calling loop. Or, simpler: stick with the CLI or curl.

This is a known integration gap; it's a constraint of opencode's agent loop, not the proxy strategy. The strategy itself is sound — the curl test above proves it returns a single, complete, OpenAI-compatible response.

## Live results

### Run 1 — homogeneous refactor

Task: *"Refactor a small JavaScript file: rename total to subtotal, add JSDoc to price(), write a Jest test, then explain why subtotal is clearer in an e-commerce cart."*

| phase | calls | local | cloud | wall |
|---|---:|---:|---:|---:|
| plan | 1 | 0 | 1 | 12.7 s |
| execute | 7 | 7 | 0 | 23.4 s |
| synth | 1 | 0 | 1 | 4.7 s |
| **total** | **9** | **7** | **2** | **40.5 s** |

Cloud was used only for planning + synthesis. All seven concrete edits/tests/reviews ran on `qwen3-coder:30b`. **78 % of model calls landed on the local model.**

### Run 2 — heterogeneous task ("design + implement + explain trade-offs")

Task: *"Build a small Node CLI for note-taking. Tasks: (1) design the CLI command surface and storage architecture comprehensively, (2) write a function that parses YAML front-matter, (3) write a function that lists notes by date, (4) explain in detail with trade-offs why we picked SQLite over a JSON file, (5) add a one-line --help banner."*

| phase | calls | local | cloud | wall |
|---|---:|---:|---:|---:|
| plan | 1 | 0 | 1 | 26.6 s |
| execute | 12 | 10 | 2 | 92.0 s |
| synth | 1 | 0 | 1 | 46.1 s |
| **total** | **14** | **10** | **4** | **165 s** |

The planner emitted 12 steps. Step 2 (*"Design CLI and storage architecture"*) and step 11 (*"Explain SQLite over JSON"*) were hinted `cloud` — both routed cloud. **The other 10 steps** (CLI skeleton, parser, tests, listing, wiring, validation) **all routed local**.

## What this enables that per-turn routing can't

1. **Planning vs execution split.** Cloud reasons about *what to do*; local does the *typing*.
2. **Heterogeneous routing within a single user request.** If a request has 5 sub-tasks where 4 are easy and 1 is architectural, only that 1 is paid for at cloud rates.
3. **Honest cost accounting.** The decision log records `architect_plan_steps`, `architect_local_steps`, `architect_cloud_steps` per architect-mode invocation, so you can compute "what would a non-architect run have cost?" against "what did this run cost?".
4. **Audit trail.** The CLI reports include the plan, the per-step routing reason (heuristic banner), and each step's output verbatim. You can inspect *why* each step landed where it did.

## What it doesn't do (and why)

- **Per-tool-call routing.** Each tool call inside a step still runs against the model that won that step. To route per-tool-call you'd need to intercept the tool-call boundary, which requires changes to opencode's agent runtime, not just the proxy. Not built.
- **Step concurrency.** Steps run sequentially. The plan has a `depends_on` field, so a future version could run leaf steps in parallel — but for the test workloads we tried, sequential is fine and easier to debug.
- **Dynamic re-planning.** If a step output reveals the plan is wrong, the executor doesn't re-call the planner. Adding it would be a "self-correcting architect" — meaningful for long-running plans but adds latency.
- **Tool calling from within a step.** Each step is a single chat-completion (no tools enabled). For *steps that need tools* (e.g. "run the Jest tests and report the result"), you'd want the executor to be a real opencode-agent run. Not built; left as a follow-up.

## Adding your own architect-style strategies

The `runArchitect()` function in `architect-core.mjs` accepts arbitrary `planner`, `executor`, and `synthesizer` model ids. So you can build variants:

```js
import { runArchitect } from "./architect-core.mjs";

// Cheap-planner variant: use heuristic for both plan and execute.
const cheap = await runArchitect({
  task: "...",
  planner: "router/heuristic",       // try local-first for planning
  executor: "router/heuristic",
});

// Cascade-everywhere variant.
const careful = await runArchitect({
  task: "...",
  planner: "router/always-cloud",
  executor: "router/cascade",        // pay tiebreaker cost on borderline steps
  synthesizer: "router/cascade",
});
```

The `router_hint` field per step lets the planner override the executor's model id on a step-by-step basis — useful when you know upfront a step needs the big model regardless of what the heuristic might say.

## Decision-log records for architect mode

Each architect-mode invocation appends one summary record:

```json
{
  "ts": "2026-04-26T17:25:00Z",
  "id": "architect-abc123",
  "strategy": "architect",
  "choice": "architect",
  "reason": "architect: plan=12 local=10 cloud=2",
  "backend_model": "(architect-pipeline)",
  "stream": false,
  "success": true,
  "architect_plan_steps": 12,
  "architect_local_steps": 10,
  "architect_cloud_steps": 2,
  "total_ms": 165340
}
```

In addition, every sub-call (planner, each executor step, synthesiser) appends its own per-call record (since they go through the proxy too). So the log gives you both the macro view (one architect record) and the micro view (every sub-decision).

Aggregate view of just the macro records:

```sh
jq -r 'select(.strategy=="architect") |
       "\(.ts)\t\(.architect_plan_steps)\t\(.architect_local_steps)\t\(.architect_cloud_steps)\t\(.total_ms)ms"' \
  ../logs/decisions.jsonl
```
