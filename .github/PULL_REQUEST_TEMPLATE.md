## Summary

<!-- One or two sentences: what changes and why. -->

## Type of change

- [ ] Bug fix
- [ ] New feature (CLI, router strategy, scorer, etc.)
- [ ] New model variant (`configs/variants/...`)
- [ ] New benchmark or task category
- [ ] Documentation only
- [ ] Refactor / cleanup (no behavior change)
- [ ] Other (describe):

## Reproducibility impact

- [ ] No existing `results/runs/.../raw.jsonl` row needs re-running
- [ ] Some rows would re-run differently — explained below
- [ ] Pricing tables changed (token-budget output will shift)

If reproducibility is affected, describe which rows or aggregates change and why that's acceptable.

## Verification

```bash
# commands you ran locally
.venv/bin/pytest tests/ -q -m 'not slow'
.venv/bin/ruff check src/ tests/
```

Paste the relevant output if it's short, or attach as a file.

For model-variant PRs, please also include:

- `progress.log` from your smoke run
- A one-line take on what the smoke run showed (works as expected / better than / worse than the baseline)

## Checklist

- [ ] Fast tests pass (`pytest -m 'not slow'`)
- [ ] `ruff check src/ tests/` is clean
- [ ] New runtime deps added to `pyproject.toml` with pinned version range
- [ ] New CLI flags / config keys documented in the relevant `docs/` file
- [ ] `CHANGELOG.md` updated under `## [Unreleased]` (skip for minor doc fixes)
