# Contributing to hybrid-coding-eval

Thanks for your interest. This project is a **research artifact**, not a product, but contributions — especially new model variants and benchmarks — are welcome.

By contributing you agree your changes are released under the same terms as the rest of the repo: **MIT** for code, **CC-BY-4.0** for documentation, data, and results.

---

## Quick environment setup

```bash
git clone https://github.com/RunanywhereAI/hybrid-coding-eval
cd hybrid-coding-eval

python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e ".[dev]"

cp .env.example .env  # add OPEN_AI_API_KEY + ANTHROPIC_API_KEY
./bench setup         # clones vendor/minions, builds Docker image, pulls aux Ollama models
```

`./bench setup` is idempotent — safe to re-run. See `docs/REPRODUCING.md` for the full first-run walkthrough.

## Running tests

```bash
# fast tests (~3 minutes; no Docker / Ollama / network calls)
.venv/bin/pytest tests/ -q -m 'not slow'

# one test file
.venv/bin/pytest tests/test_r3_hybrid_architect.py -q

# lint
.venv/bin/ruff check src/ tests/
```

All PRs must pass `pytest -m 'not slow'` and `ruff check src/ tests/`. CI runs both on every push (see `.github/workflows/ci.yml`).

---

## Adding a new model variant

Most common contribution; ~90 seconds for a model already on Ollama or OpenAI.

1. Copy the template:

   ```bash
   cp configs/variants/_template.yaml configs/variants/NN-my-model-all-routes.yaml
   ```

2. Edit two lines:

   ```yaml
   variant_tag: my-model
   models:
     cloud: gpt-5.5
     local: my-model:latest
   ```

3. If local, pull the Ollama model: `ollama pull my-model:latest`.

4. Run a smoke sweep:

   ```bash
   ./bench run --config configs/variants/NN-my-model-all-routes.yaml --smoke
   ```

5. If smoke passes, run the full sweep, then analyze:

   ```bash
   ./bench run --config configs/variants/NN-my-model-all-routes.yaml
   ./bench analyze results/runs/NN-my-model-all-routes/
   ```

6. Commit the variant config only. Result dumps require a separate review for inclusion in the canonical dataset.

The PR description should include: model name, parameter count, quantization, smoke-run `progress.log`, and a one-line take vs the baseline. See `examples/drop-in-a-new-model.md` for a full walkthrough.

## Adding a new task or benchmark

1. Pick a unique category letter (A–D are taken).
2. Add `src/hybrid_coding_eval/benchmarks/my_bench/` with `__init__.py`, `loader.py`, and a `README.md` documenting source + license + pin commit.
3. Register the category in `src/hybrid_coding_eval/core/experiment.py:CATEGORY_SOURCES`.
4. Add at least one unit test loading the first task.
5. Document the upstream attribution in `NOTICE.md`.

## Adding a new routing strategy

1. Add the `case` branch in `router/strategies.mjs`.
2. Register the name in the choices list in `src/hybrid_coding_eval/cli/run.py` and the schema enum at `src/hybrid_coding_eval/core/config/schema.py`.
3. Regenerate the JSON schema: `./bench schema --out configs/schema.json`.
4. Add a section to `docs/ROUTING_STRATEGIES.md`.
5. Add a test under `tests/test_router_strategies.py`.

---

## Pull request style

- **One logical change per PR.**
- **Title format:** `<area>(<scope>): <imperative summary>` — e.g. `feat(cli): bench setup subcommand`, `fix(scorer): handle empty stdout`.
- **Body:** what changed, why, and any reproducibility implications. Use the PR template (`.github/PULL_REQUEST_TEMPLATE.md`).

## Code style

- **Python:** ruff with the repo's default config. Type hints encouraged but not required for new code; public functions in `src/hybrid_coding_eval/core/` should have brief docstrings.
- **JavaScript (router):** plain Node, no transpilation; match existing style.

## Project principles

- **Reproducibility beats convenience.** Every published number traces back to `(task_id, route, variant_tag, hardware_profile_ref, git_sha)` in `results/runs/.../raw.jsonl`.
- **Cost honesty.** Costs are derived from `tokens × pinned pricing`. Pricing edits go in `configs/pricing/pricing_tables.json` and ripple through `./bench token-budget` without re-running inference.
- **No silent dependencies.** New runtime deps go in `pyproject.toml` with a pinned range and a one-line justification in the PR.
- **Tests are sandboxed.** Functional scoring runs in Docker with `--network none`, memory caps, and wall-clock timeouts.

---

## Reporting bugs

Use the templates in `.github/ISSUE_TEMPLATE/`:

- `bug_report.md` — crashes, hangs, wrong numbers
- `new_model.md` — propose adding a model to the canonical benchmark
- `reproducibility_issue.md` — "I can't reproduce the published numbers"

Conduct: this project follows [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md).
