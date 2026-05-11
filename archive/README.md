# archive/

Historical material preserved for lineage. Nothing in here is referenced by the canonical OSS surface (`README.md`, `reports/*.md`, `docs/{ARCHITECTURE,METHODOLOGY,REPRODUCING,ROUTING_STRATEGIES,PRIOR_ART,OSS_REVIEW,RUNANYWHERE_INTEGRATION,FINAL_REPORT_PLAN}.md`, `docs/audits/T-22-v3-publish-readiness.md`). If you only care about the published v3 result, skip this directory.

If you want to audit *how* the project evolved — what was tried, what was deferred, what shaped the v3 framing — this is where to look.

## archive/docs/

Planning artefacts, draft narratives, and superseded audits.

| Path | What it is |
|---|---|
| `PLAN.md` | Original multi-phase MVP plan. Superseded by `docs/FINAL_REPORT_PLAN.md` (the 22-task plan that drove the v3 cycle). |
| `article-draft-v1.md` | Long-form v1 narrative (MVP era) plus a v2 postscript. Superseded by `reports/ARTICLE.md` (v3 canonical). |
| `T-12-deferred.md` | Honest deferral note explaining why the planned seed-threading experiment was not run. |
| `T-13-analysis.md` | Prompt-caching analysis that was scoped as a sweep, then descoped to analysis-only. |
| `audits/T-21-publish-readiness.md` | Pre-public audit on the MVP (2026-05-05). Superseded by the v3 audit at `docs/audits/T-22-v3-publish-readiness.md`. |
| `history/OVERNIGHT_SUMMARY.md` | Pre-MVP build notes from the qwen3-coder overnight prototype run. |
| `history/HOW_TO_TEST.md` | Pre-MVP test guide. Superseded by `docs/REPRODUCING.md`. |
| `history/hybrid_local_cloud2.md` | Pre-MVP architectural sketch. |

## archive/research/

External research inputs that informed `docs/PRIOR_ART.md`. Each subdir is one Exa/Perplexity sonar-deep-research snapshot with a `report.md` (narrative), `results.json` (raw query data), and `metadata.json` (query parameters).

| Subdir | Topic |
|---|---|
| `2026-04_agentic_and_tool_aware_routing_research/` | Agentic / tool-aware routing literature |
| `2026-04_open_source_router_models/` | Open-source classifier-style routers |
| `2026-04_production_hybrid_coding_agents/` | Aider, Cline, Cursor — production hybrid patterns |
| `2026-04_production_hybrid_general_use_cases/` | General-purpose hybrid agents |
| `2026-04_routing_evaluation_benchmarks_calibration/` | Existing routing benchmark efforts |
| `2026-05_coding_eval_benchmarks/` | Coding eval benchmark landscape |
| `2026-05_hardware_reality_and_cost_calibration/` | M-series Mac hardware reality + pricing data |
| `2026-05_hybrid_coding_architectures_with_empirics/` | Hybrid coding architectures with measured numbers |
| `2026-05_local_coding_model_performance/` | Local coding-model performance (devstral, qwen, etc.) |

Plus the two runner scripts (`_run_research_2026-04.py`, `_run_research_2026-05.py`) that produced the snapshots. The research snapshots are frozen; the runner scripts are kept for reproducibility, not active use.

## archive/examples/

Pre-MVP proof-of-concept comparisons. Three small tasks (wordcount CLI, todo API, URL shortener) each run under cloud-only and hybrid routes, with metrics and a comparison write-up. Pedagogically useful but the comparison signal is weak (N=3, no scoring rubric). Superseded by the 250-row v3 sweep.

The live `examples/` directory still contains the user-facing "drop in a new model" walkthrough (`examples/drop-in-a-new-model.md`, `examples/RESULTS.md`, `examples/run-comparison.mjs`).

| Subdir | Task |
|---|---|
| `01-wordcount-cli/` | "Write a CLI that counts words in a file" |
| `02-todo-api/` | "Build a TODO REST API" |
| `03-url-shortener/` | "Build a URL shortener service" |
