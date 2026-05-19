# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) starting with v1.0.0.

## [Unreleased]

## [1.1.1] — 2026-05-19

Phase 7 first-iteration release. Documents what we learned running the v1.1.0 harness end-to-end against opencode + qwen3-coder:30b, plus the two small fixes that came out of the iteration loop.

### Added
- **Iteration-sweep results** (5 Exercism Python tasks × 4 strategies × 1 seed = 20 rows) — bundled as the v1.1.1 release-asset tarball. See `results-v1.1.1.tar.gz` on the release page.
- **`docs/AGENTIC_ROUTES.md`** — new "Known model-compatibility limitations" section documenting the qwen3-coder + opencode tool-message format issue.

### Changed
- **R8 model field** — bench_run_id is no longer embedded in the model field for the opencode runner. Opencode 1.1.x validates incoming model ids against its `providers[].models` registry and rejects unknown ones (ProviderModelNotFoundError), so the v1.1.0 `router/<strategy>/run-<id>` shape can't pre-register. R8 falls back to timestamp-window attribution (still safe under serial `./bench sweep` invocations). R6/R7 (LiteLLM-based) keep exact-id matching.
- **`_score_in_sandbox` (R8)** — host-pytest fallback when Docker is unreachable. The repo's `.venv/bin/python` is preferred over PATH's `python3`. Trade-off: loses the `--network none` sandboxing guarantee when fallback fires; gains the ability to iterate without Docker Desktop running. Canonical sweeps still need Docker up.
- **Router proxy** — added `normalizeToolCallsInChunk()` to the streaming response path. Ollama-served models (qwen3-coder etc.) emit `tool_calls[].function.arguments` as a JSON object and `tool_calls[].function.index` instead of a sibling `index`; opencode rejects both with TypeValidationError. The proxy now rewrites to OpenAI-compliant shape before forwarding.

### Known limitations (deferred to v1.2)
- **opencode → qwen3-coder → opencode tool-message round-trip** still produces an Ollama 400 ("Value looks like object, but can't find closing '}' symbol") when the proxy forwards a `tool`-role message back to the local model. Effect: any hybrid strategy that routes a post-tool-call interpretation to qwen3-coder fails the agent loop on the next turn. v1.1.1 ships with documented findings rather than a fix; v1.2 will add an incoming-direction message-format normalizer.
- **R6 / R7** runners stay `EXPERIMENTAL` — canonical-sweep coverage deferred to v1.2.
- **Docker sandbox**: when down, R8 falls back to host pytest. Re-run with Docker up for the security guarantee.

## [1.1.0] — 2026-05-19

Agentic-routes release. Adds R8 (opencode) as the v1.1 primary agentic route, alongside R6 (mini-swe-agent) + R7 (Aider) as experimental. The `heuristic` strategy is now agent-aware. Production-pipeline framing — anyone can benchmark a new local model in three commands.

### Added
- **R8 opencode runner** at `src/hybrid_coding_eval/runners/r8_opencode.py`. Real ReAct loop with Read/Write/Edit/Bash/Grep/Glob tools, routed through the proxy on :8787.
- **R6 mini-swe-agent + R7 Aider runners** (experimental; not in the v1.1 canonical sweep).
- **Exercism Python benchmark** (`src/hybrid_coding_eval/benchmarks/exercism_python/`) — new category `X` covering single-file functional tasks vendored from Aider's polyglot benchmark (MIT).
- **Correlation-id token attribution** (`src/hybrid_coding_eval/runners/_agent_attribution.py`). Each agentic-runner call generates a 12-hex `bench_run_id`, embeds it in the model field as `router/<strategy>/run-<id>`, the router echoes it into `decisions.jsonl`, and attribution filters on the id — eliminates the timestamp-window race that bit the v4 pilot.
- **`./bench sweep --strategies --seeds`** subcommand. Loops a YAML across `(strategy × seed)` with per-cell subdirectories. The single reproducer for v1.1+ sweeps; replaces the deleted bin/v4*.sh pattern.
- **`./bench setup` opencode phase**. Clones the maintainer fork (env-overridable via `OPENCODE_GIT_URL` / `OPENCODE_GIT_REF`, default `RunanywhereAI/opencode-1@feat/hybrid-routing-plugin`) into `vendor/opencode/`. Writes a minimal `~/.config/opencode/opencode.json` registering the `hybrid-router` provider if absent; backs up existing configs that don't.
- **Bootstrap confidence intervals** in the analysis layer (`src/hybrid_coding_eval/analysis/bootstrap.py`). Per-`(category, route, strategy)` cell: pass-rate, cost-USD, cloud-fraction, wall-ms with 95% percentile CIs. Emitted as `bootstrap_cis.json`.
- **`router/tests/agent-heuristic.test.mjs`** — 20 unit tests for the new agent-aware heuristic (zero deps; uses `node:test`).
- **`docs/AGENTIC_ROUTES.md`** + **`docs/BENCHMARK_NEW_MODEL.md`** + **`configs/variants/_template-agentic.yaml`**.

### Changed
- **`heuristic` strategy is now agent-aware.** Detects ReAct loops (tool/function role + assistant.tool_calls + system-marker hints) and scores the latest message delta (not the full prompt) with phase signals (first-call → cloud, post-tool-call → local, tool-result echo → local). The v1.0.0 implementation is preserved internally as `legacyHeuristic`, called byte-identically for plain chat. Zero numerical drift on v3.3 numbers.
- **Cascade strategy** also benefits — it forwards `ctx` into the inner heuristic and inherits the agent-awareness.
- **R8 functional scoring** now runs in the existing `hybrid-eval-python:latest` Docker sandbox (via `scorers.functional_python`), restoring the v1.0.0 sandboxing-contract that the v4 pilot's host-pytest path violated.
- **`results/runs/` is gitignored going forward.** Existing tracked v1.0.0 / v3.3 datasets stay at their commits; new v1.1+ sweeps bundle as `gh release` tarballs (`results-v1.1.K.tar.gz`).
- **`router/server.mjs`** parses optional `/run-<id>` suffix on the model field; threads `ROUTER_AGENT_HEURISTIC_THRESHOLD` + `ROUTER_AGENT_SYSTEM_MARKERS` through ctx.
- **`router/package.json`** test scripts split — `npm test` runs the new fast unit-test path; `npm test:integration` runs the existing end-to-end harness.
- **`pair_already_done`** backward-compat fix — rows without `router_strategy` (v3 era) match wildcard.

### Removed
- **5 bin scripts** from the v4 pilot (`bin/overnight-sweep.sh`, `bin/v4.1-sweep.sh`, `bin/r6-multi-seed.sh`, `bin/agent-hybrid-analyze.py`, `bin/build-agent-corpus.py`). Replaced by `./bench sweep` and the existing `./bench analyze`.
- **`agent-heuristic` strategy as a separate entry.** Folded into the canonical `heuristic` (which is now agent-aware). The `RouteStrategy` Literal in `core/config/schema.py` and the `--router-strategy` choices in `cli/run.py` are back to v1.0.0's 7 names.
- **v4/v4.1 pilot data** (`results/runs/17-v4-agent-overnight/`, `results/runs/18-v4.1-qwen3coder-agent/`) moved to gitignored `personal/raw-runs/` — they lacked `bench-config.json` manifests because they bypassed `./bench`. Re-published as part of the v1.1.K canonical sweep under the cleaned harness.

## [1.0.0] — 2026-05-18

First public OSS release. The harness, dataset, and methodology have been used internally for the v0.x → v3.x research iterations; v1.0.0 is the first version under a stable SemVer contract.

### Added
- `./bench setup` subcommand — one-shot install of `vendor/minions/` (Stanford Minions), the `hybrid-eval-python:latest` Docker image, and auxiliary Ollama models (`qwen3:0.6b`, `nomic-embed-text`). Idempotent.
- `./bench run` now auto-clones `vendor/minions/` on demand when an R4/R5 variant config is launched without it.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, `LICENSE.md`, and a `.github/` directory with issue and PR templates plus a GitHub Actions CI workflow.
- Top-level `README.md` rewritten as an OSS landing page.

### Changed
- Owner's article/working material moved out of the public repo surface into a gitignored `personal/` directory. The published dataset under `results/runs/` remains tracked.
- `vendor/README.md` documents auto-install rather than the previous manual `cd vendor && git clone …` recipe.
- `docs/REPRODUCING.md` §3.7 now points at `./bench setup`.
- Project version bumped from `0.1.0` (development) to `1.0.0` (public).

### Removed
- `bin/v3.3-*.sh` and `bin/v3.3-*.py` (10 files) — temporary sweep-orchestration scripts specific to the v3.3 campaign. The canonical UX going forward is `./bench run --config <variant>.yaml`.
- `configs/variants/_smoke-*.yaml` (3 files) — superseded by the `--smoke` flag on `./bench run`.
- `CLAUDE.md` — Claude Code's auto-loader finds `AGENTS.md` directly; the pointer file is no longer needed.

### Pre-1.0 history

The v0.x → v3.x progression is preserved in git history. Highlights:

- **v3.3 (2026-05)** — Final research sweep. 3,581 rows across 33 variant directories spanning 6 local models, 7 routing strategies, 8 task shapes, and 6 cloud-pricing scenarios. Canonical dataset under `results/runs/`.
- **v3 (2026-05-11)** — 250-row publication sweep (`results/runs/07-v3-devstral-all-routes/`); R4/R5 Minion routes added; triple-judge robustness audit (`results/runs/11-judge-robust-D/`).
- **v2 (2026-04)** — synth-budget fix, Opus-4 judge introduced, devstral local-model swap (runs 02–03).
- **v1 (2026-03 MVP)** — 3 routes (R1/R2/R3), 90-row dataset (run 01), the original "is hybrid worth it?" experiment.

[Unreleased]: https://github.com/RunanywhereAI/hybrid-coding-eval/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/RunanywhereAI/hybrid-coding-eval/releases/tag/v1.1.1
[1.1.0]: https://github.com/RunanywhereAI/hybrid-coding-eval/releases/tag/v1.1.0
[1.0.0]: https://github.com/RunanywhereAI/hybrid-coding-eval/releases/tag/v1.0.0
