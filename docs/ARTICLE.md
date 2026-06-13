# Should this coding task run on my laptop, the cloud, or split between them?

*A reproducible benchmark of local vs. cloud vs. hybrid LLM routing for coding
agents — measured end-to-end on a single M4 Max laptop, with confidence
intervals on every number.*

---

## The question

Local code models got good, fast. A 30B model that fits in 18 GB of unified
memory now writes real refactors that pass real tests. At the same time the
price gap between a frontier cloud model and that local model is roughly
**100×**.

So the interesting question stopped being *"can the cloud do it?"* (yes,
obviously) and became:

> **Which coding tasks can stay on my laptop — and when is it worth reaching
> for the cloud?**

`hybrid-coding-eval` answers that empirically. It takes four real coding agents
(**aider, opencode, mini-swe-agent, cline**), points every LLM call they make at
a small local **router**, and lets the router decide — per call — whether to
answer with a **local** Ollama model or a **cloud** frontier model. Same agent,
same task, eight different routing strategies. Because the agent and the task
are held constant, quality, cost, and latency become directly comparable.

Everything ran on one laptop. No cluster. Every published number traces back to
a single row in a results file, and cost is computed from token counts times a
pinned price table — so you can re-price the entire dataset under a different
model's rates without re-running a single inference.

This article explains what was measured, what we found, how the routing
strategies actually work in plain terms, which benchmarks were genuinely run
(including the honest status of SWE-bench), and exactly how to reproduce any of
it.

---

## The headline findings

| Configuration | Result | Cloud used | Cost |
| --- | --- | --- | --- |
| **cline + qwen3.6 + cascade**, real refactors | **24/24 = 100%** | **10%** of tokens | **~$0.022 / task** |
| cline + qwen3.6 + always-local, Exercism puzzles | 15/15 = 100% | **0%** | $0 cloud |
| cline + qwen3.6 + always-local, *hard* tasks (D6) | 8/12 = 67% | **0%** | $0 cloud |
| aider + gemma4 + heuristic, real refactors | 23/24 = 96% [88, 100] | 16% | low |
| aider + gemma4 + heuristic, *hard* tasks (D6) | 7/12 = 58% | 61% | — |
| any agent + always-cloud, *hard* tasks (D6) | 12/12 = 100% | 100% | highest |

Read those rows together and the story is sharper than "local good" or "cloud
good":

1. **For everyday refactors, a 30B local model carries almost the whole load.**
   The best hybrid cell solves 100% of real-world refactor tasks while sending
   only ~10% of its tokens to the cloud — roughly two cents a task.

2. **On genuinely hard implementation tasks, the cloud advantage is real.** A
   local-only model tops out around 67%; cloud-only holds 100%. The 33-point gap
   is not noise.

3. **The biggest lever is the local model, not the routing cleverness.** Swapping
   the local model (qwen3-coder → gemma4 → qwen3.6) moved results far more than
   swapping routing strategies did. A good local model with a simple router beats
   a mediocre local model with a sophisticated one.

4. **Multi-step "hybrid orchestration" did not pay off.** An earlier era of this
   project built elaborate cloud-plans-local-executes pipelines (including the
   Stanford "Minion" protocol). On a 250-row replication they cost **1.9×–5×**
   more than just calling the cloud, for no quality gain. The thing that works is
   boring: **route each call to the right place.** The fancy choreography loses.

5. **Routers can't reliably tell hard from easy.** The strategy that scored 100%
   on normal refactors dropped to 75% on hard ones — and the heuristic router on
   the hard set actually spent *more* on cloud (61%) while scoring *less* (58%).
   When a task is known to be hard, forcing it to the cloud beats trusting the
   router to notice.

These are findings *with their failure cases attached*, which is the part most
benchmarks leave out.

---

## The eight routing strategies, in plain terms

Every strategy is one small function. Given the request the agent is about to
send, it returns `local` or `cloud` plus a reason and a confidence. Here is what
each one actually does — no jargon.

1. **always-local** — Never use the cloud. This is the control that measures
   "how far does my laptop get on its own, for $0?"

2. **always-cloud** — Always use the cloud. The quality ceiling and the cost
   ceiling. Every other strategy is judged against these two.

3. **rules** — A hand-written checklist. If the prompt is huge (>4,000 tokens),
   pastes three or more code blocks, or contains "thinking" words like *design,
   architecture, refactor entire, security, migration plan* → cloud. If it
   contains "trivial" words like *rename, typo, format, one-liner* → local.
   Otherwise default to local. Fast, transparent, no model in the loop.

4. **heuristic** — The workhorse, and the most interesting one. It's *agent-aware*:
   it recognises that a coding agent is in a back-and-forth loop, and it scores
   only the **newest message** (the latest tool result or instruction), not the
   whole giant transcript. A short "command succeeded" echo scores low → local. A
   fresh planning step at the top of the loop scores high → cloud. It also reads
   the **phase**: the very first call of a task (the planning step) gets nudged
   toward cloud; a call that's just digesting a tool's output gets nudged toward
   local. Cross a score threshold → cloud.

5. **llm-classifier** — Ask a *tiny* local model (a 0.6B model, ~50–200 ms) one
   question: "is this task SIMPLE or COMPLEX?" SIMPLE → local, COMPLEX → cloud.
   A cheap learned judge instead of hand-written rules.

6. **embedding-knn** — Keep a labelled list of 50 example prompts, 25 tagged
   "local-ish" and 25 "cloud-ish." Convert the incoming prompt to a vector, find
   its 5 nearest neighbours in that list, and vote. "Does this look more like the
   things I'd keep local or the things I'd send to the cloud?"

7. **cascade** — The champion. Run the fast heuristic first. If it's *confident*
   (the score is clearly high or clearly low), trust it and move on — no extra
   cost. Only when the score lands in the **uncertain middle** does it pay for the
   tiny llm-classifier to break the tie. Best of both: cheap on the easy
   majority, careful on the genuine maybes.

8. **phase-aware** — A specialist for the aider agent, which already splits its
   own work into an "architect" step (plan the change) and an "editor" step (type
   out the diff). This strategy just honours that split deterministically:
   architect → cloud, editor → local. Plan expensively, type cheaply.

A useful mental model: **2–3 are dumb-but-honest baselines, 4–8 are increasingly
clever attempts to spend cloud money only where it changes the answer.** The
punchline of the whole project is that the clever ones barely beat the simple
heuristic — and *which local model you pick* matters more than which of these you
choose.

You can also override any strategy on a single call by appending `!local` or
`!cloud` to the model name — handy when you already know a task is hard.

---

## What was actually benchmarked (including the honest SWE-bench answer)

People reasonably ask "did you run SWE-bench, or just toy problems?" Here is the
straight answer, era by era, because the project has two distinct phases.

### The current (v1.x) leaderboard runs on three task classes

- **puzzles** — 5 Exercism Python exercises (`grep`, `list-ops`, `phone-number`,
  `pig-latin`, `robot-name`), from the Aider polyglot benchmark. Single-function,
  hidden-test problems. **Scored functionally** by running the real test suite in
  a Docker sandbox (no network, memory-capped, 60 s timeout).

- **refactors** — real-developer task shapes, the heart of the benchmark:
  - **D1** (add a feature), **D5** (write a one-shot script) — functionally scored
    against pytest suites.
  - **D6** (v1.5 *hard* implementation challenges) — four meaty single-file
    builds: an LRU+TTL cache, a token-bucket rate limiter, a topological sort with
    cycle detection, and a recursive-descent template engine. **80 pytest
    assertions** across the four. These exist specifically to break the easy 100%
    scores and expose where local models actually fail.
  - (D3 "refactor" and D4 "code review" tasks exist too but used an LLM judge,
    which was retired in v1.4 for being too noisy.)

- **real-prs** — **SWE-bench Verified.** This is the honest part: the *adapter is
  shipped and reproducible* (it loads real merged PRs from django, sphinx, flask,
  click, requests, and friends, and scores via the upstream SWE-bench harness),
  and there's a ready config (`configs/v1.4-real-prs.yaml`, 10 tasks × aider × 3
  seeds). **But the agentic SWE-bench sweep is deferred to v1.6 — it is not part
  of the published v1.x leaderboard numbers.** If someone cites a headline
  pass-rate from this project, it's on puzzles + refactors, *not* on SWE-bench.
  Don't let anyone (including a future you) blur that line.

### SWE-bench Verified *was* genuinely run — in the earlier (MVP/v3) era

The first phase of the project (the 180-row MVP and the 250-row v3 sweep) ran
**real SWE-bench Verified instances** — astropy, django, sphinx, xarray PRs —
driven through mini-swe-agent and scored by the official harness. That's where
the "multi-step orchestration loses" conclusion came from: on those real PRs, the
Minion-style and architect-style pipelines were Pareto-dominated by plain
cloud-only. Those runs are preserved, immutable, in `results/runs/` for
reproducibility.

So: **yes, real PRs were measured** (MVP/v3 era, and the conclusion was honest
and negative for hybrid). **The current agentic leaderboard deliberately scopes
to functionally-scored puzzles and refactors**, with the SWE-bench replay sitting
ready as the next sweep.

### Do official reports exist for reproducing the real tasks?

Yes:

- **`results/REPORT_v1_mvp.md`** — the MVP report, including the SWE-bench (real
  PR) category and the synth-budget bug post-mortem.
- **`docs/release-notes/v1.4.0.md` → `v1.5.0.md`** — the per-release findings with
  full per-cell numbers and confidence intervals for the current leaderboard.
- **`docs/HYBRID_ROUTING_DESIGN.md`** — the canonical design doc: every strategy,
  every agent, the metric definitions, and the result schema.
- **`results/runs/`** — the immutable raw datasets (MVP runs, the v3 SWE-bench
  sweep, the judge-robustness audit) preserved byte-for-byte.

---

## Why these numbers are trustworthy

Most "local vs cloud" takes are vibes. This one is built to be checked:

- **Token-first, cost-derived.** Rows store *tokens*, never dollars. Cost is
  computed at analysis time from a SHA256-pinned price table shared by both the
  Python harness and the Node router (a parity test asserts they agree). Want to
  know the answer under Claude pricing instead of GPT pricing? Re-run the
  analysis; don't re-run the benchmark.

- **Bootstrap confidence intervals on every cell.** "X beats Y" is only claimed
  when the 95% intervals support it. The marquee `aider + gemma4 + heuristic` cell
  is reported as **96% [88, 100]**, not a bare 96%.

- **Full provenance per row.** Every row carries its task, route, strategy, seed,
  local + cloud model IDs, the config hash, and a hardware-profile reference.

- **Crash-resumable, honest about failures.** Rows flush as they complete; a
  crash loses at most one row. Where a result is an agent *session* bug rather
  than a model-quality failure (e.g. cline never wrote any code), the notes say
  so instead of quietly scoring it as a loss.

- **The negative results are kept.** The refuted Minion hypothesis, the dead-end
  cascade-threshold tuning, the runaway-generation crash that forced the local
  guardrails — all documented, not buried.

---

## How to reproduce it yourself

Five minutes to a green smoke run; about an hour to a full canonical sweep on an
M4 Max. The full step-by-step (including pause/resume for overnight runs and how
to benchmark a brand-new model in three commands) lives in
[`REPRODUCING.md`](./REPRODUCING.md). The short version:

```bash
# 1. Clone + install
git clone https://github.com/RunanywhereAI/hybrid-coding-eval
cd hybrid-coding-eval
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev,agents]"
cp .env.example .env          # paste your OpenAI key

# 2. One-time setup (Docker scoring image + agent CLIs + health check)
./bench setup

# 3. 30-second smoke test (cloud only — no local model needed yet)
./bench sweep --config configs/v1.4-smoke.yaml --strategies always-cloud --seeds 42
./bench analyze results/runs/v1.4-smoke

# 4. A real hybrid sweep (pull a local model first, ~18 GB)
ollama pull gemma4:31b
./bench sweep --config configs/v1.4-canonical-gemma4.yaml \
    --strategies always-cloud,always-local,heuristic,cascade --seeds 42,7,13
./bench analyze results/runs/v1.4-canonical-gemma4
```

Then check the headline cell against the published dataset:

```bash
jq '.cells["refactors::cline::cascade"].pass_rate' \
   results/runs/<your-sweep>/bootstrap_cis.json

# And download the canonical dataset to compare:
gh release download v1.5.1 -p results-v1.5.1.tar.gz   # == v1.5.0 bytes
```

**What it costs you:** the smoke run is ~$0.01. A full canonical sweep is
~10–15 hours of wall time and roughly $30–50 of cloud spend at frontier pricing,
plus an 18 GB model download. The smoke run gives you a green checkpoint before
you commit to any of that.

---

## The takeaways

- **A good 30B local model handles the bulk of everyday coding work.** For real
  refactors, the best hybrid setup hit 100% while sending ~10% of tokens to the
  cloud — about two cents a task.
- **The cloud earns its keep on genuinely hard problems**, where local tops out
  near two-thirds and frontier models hold 100%.
- **Pick the local model carefully; the router second.** Model choice was the
  dominant lever in every sweep.
- **Skip the elaborate hybrid choreography.** Per-call routing wins; multi-step
  orchestration lost on cost, quality, *and* latency.
- **When you know a task is hard, just send it to the cloud** — routers have a
  real blind spot for difficulty.

If you run local models for coding, the practical recommendation is concrete:
**cline + a strong 30B (qwen3.6-class) local model + the cascade router** for
day-to-day refactor work, and a hard `!cloud` override in your pocket for the
problems you already know are nasty.

---

*Reproduce any number here from a clean clone. Found a discrepancy, or want a new
model on the leaderboard? Open an issue — that's exactly what this repo is for.*

*Benchmark + data + charts + this article are all MIT-licensed. A citation in
derived work is appreciated; the BibTeX block is in the
[README](../README.md#license--citation).*
