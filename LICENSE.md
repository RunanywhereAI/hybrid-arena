# Licensing overview

This repository is dual-licensed:

| Material | License | File |
| --- | --- | --- |
| **Code** (harness, router, runners, scorers, analysis, viz, CLI, tests) | MIT | [`LICENSE`](./LICENSE) |
| **Data and prose** (results, metrics, figures, run-notes, docs, article) | CC-BY-4.0 | [`LICENSE-DATA`](./LICENSE-DATA) |
| **Third-party vendored code** | Per-upstream (Apache 2.0, MIT) | [`NOTICE.md`](./NOTICE.md) + per-vendor `LICENSE` files |

## What falls under which license

| Path | License |
| --- | --- |
| `src/hybrid_coding_eval/**` | MIT |
| `router/**` | MIT |
| `tests/**` | MIT |
| `configs/**` | MIT |
| `bench`, `pyproject.toml`, `requirements.txt`, `.env.example` | MIT |
| `results/**` (raw.jsonl, env-manifest.json, charts, REPORT.md, DECISION_MATRIX.md, run-notes) | CC-BY-4.0 |
| `docs/**`, `examples/**`, `README.md`, `AGENTS.md`, `CHANGELOG.md`, `CONTRIBUTING.md` | CC-BY-4.0 |
| `vendor/lm-eval-harness-judge/**` | Apache 2.0 (upstream FastChat; see `NOTICE.md`) |
| `vendor/minions/**` | MIT (upstream HazyResearch/minions; gitignored, see `NOTICE.md`) |

## Why dual-license

The code is intended to be copied, modified, and embedded in other projects with minimal friction — MIT keeps that path open. The data and prose carry an attribution requirement because the published numbers are the value-add of this project: citing them honestly is the only obligation we ask of downstream users.

## Attribution

If you use code from this repo, the MIT notice header is sufficient. If you cite the data, methodology, or article, please use:

> Monga, Sanchit and contributors. *hybrid-coding-eval: reproducible cost/latency/quality benchmark for local vs cloud vs hybrid LLM routing on coding tasks.* 2026. <https://github.com/RunanywhereAI/hybrid-coding-eval>.

A BibTeX entry is in the project `README.md`.

## Third-party obligations

Where this project vendors or builds on upstream work, those obligations are itemized in [`NOTICE.md`](./NOTICE.md). Nothing in this `LICENSE.md` overrides or narrows those obligations.
