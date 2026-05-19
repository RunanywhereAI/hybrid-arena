# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) starting with v1.0.0.

## [Unreleased]

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

[Unreleased]: https://github.com/RunanywhereAI/hybrid-coding-eval/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/RunanywhereAI/hybrid-coding-eval/releases/tag/v1.0.0
