"""Category × route heatmap.

Rows = categories (A / B / C). Columns = routes (R1 / R2 / R3).
Cells = the chosen metric (quality / cost / ARQGC). Each cell is
annotated with the numeric value.

Run from the repo root::

    python -m viz.decision_heatmap results/full-sweep/aggregate.json \\
        --metric quality \\
        --out results/full-sweep/charts/heatmap_quality.png
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Repo-root import dance.
_here = Path(__file__).resolve()
for _p in (_here, *_here.parents):
    if (_p / "pyproject.toml").is_file():
        _REPO_ROOT = _p
        break
else:  # pragma: no cover
    _REPO_ROOT = _here.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from hybrid_coding_eval.analysis.arqgc import bounded_arqgc  # noqa: E402
from hybrid_coding_eval.core.results import load_results  # noqa: E402

__all__ = ["plot_heatmap"]


def _build_grid(
    aggregate_json: dict,
    metric: str,
    scenario: str,
    arqgc: dict | None = None,
) -> tuple[list[str], list[str], np.ndarray]:
    """Return (categories, routes, matrix) for the chosen metric.

    Supported metrics:

      * ``quality`` — quality_median per cell.
      * ``cost`` — cost_<scenario>_median per cell.
      * ``cost_total`` — cost_<scenario>_total per cell.
      * ``wall_ms`` — wall_ms_median per cell.
      * ``arqgc`` — per-(cat, route) arqgc score (needs ``arqgc`` arg).
    """
    per_cat_route: dict = aggregate_json.get("per_category_route", {})
    categories = sorted({k.split("/")[0] for k in per_cat_route.keys()})
    routes = sorted({k.split("/")[1] for k in per_cat_route.keys()})

    matrix = np.full((len(categories), len(routes)), np.nan, dtype=float)

    for i, cat in enumerate(categories):
        for j, route in enumerate(routes):
            key = f"{cat}/{route}"
            if metric == "arqgc":
                if arqgc is None:
                    raise ValueError("metric='arqgc' requires arqgc dict")
                v = arqgc.get("per_category_route", {}).get(key)
            else:
                cell = per_cat_route.get(key, {})
                if metric == "quality":
                    v = cell.get("quality_median")
                elif metric == "cost":
                    v = cell.get(f"cost_{scenario}_median")
                elif metric == "cost_total":
                    v = cell.get(f"cost_{scenario}_total")
                elif metric == "wall_ms":
                    v = cell.get("wall_ms_median")
                else:
                    raise ValueError(f"unknown metric {metric!r}")
            if v is None:
                matrix[i, j] = np.nan
            else:
                matrix[i, j] = float(v)
    return categories, routes, matrix


def _annotate_value(v: float, metric: str) -> str:
    if np.isnan(v):
        return "—"
    if metric == "quality":
        return f"{v:.2f}"
    if metric == "arqgc":
        return f"{v:.3f}"
    if metric == "cost" or metric == "cost_total":
        if v == 0:
            return "$0"
        if v < 0.01:
            return f"${v:.4f}"
        if v < 1:
            return f"${v:.3f}"
        return f"${v:.2f}"
    if metric == "wall_ms":
        return f"{int(round(v)):,}ms"
    return f"{v:.3f}"


def plot_heatmap(
    aggregate_json: dict,
    output_path: Path | str,
    metric: str = "quality",
    scenario: str = "openai-gpt5.5",
    arqgc: dict | None = None,
    dpi: int = 150,
) -> Path:
    """Render the heatmap. Returns the output path."""
    op = Path(output_path)
    op.parent.mkdir(parents=True, exist_ok=True)

    categories, routes, matrix = _build_grid(aggregate_json, metric, scenario, arqgc)

    fig, ax = plt.subplots(figsize=(max(5, 1.6 * len(routes) + 2), max(3, 1.1 * len(categories) + 1.5)), dpi=dpi)

    # Higher = better for quality/arqgc, lower = better for cost/wall.
    cmap = "YlGn" if metric in ("quality", "arqgc") else "YlOrRd"

    # ``np.nanmin`` / ``np.nanmax`` so the colour scale ignores empty cells.
    finite = matrix[np.isfinite(matrix)]
    vmin = float(finite.min()) if finite.size else 0.0
    vmax = float(finite.max()) if finite.size else 1.0
    if vmin == vmax:
        vmax = vmin + 1e-9  # avoid zero-range colormap

    im = ax.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")

    ax.set_xticks(range(len(routes)))
    ax.set_xticklabels(routes)
    ax.set_yticks(range(len(categories)))
    ax.set_yticklabels(categories)
    ax.set_xlabel("Route")
    ax.set_ylabel("Category")

    pretty = {
        "quality": "Quality (median)",
        "cost": f"Cost per task (median, {scenario})",
        "cost_total": f"Cost total ({scenario})",
        "wall_ms": "Wall time (median ms)",
        "arqgc": f"Bounded-ARQGC ({scenario})",
    }.get(metric, metric)
    ax.set_title(pretty)

    # Text annotations. Use white text on dark cells, black on light.
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            if not np.isfinite(val):
                colour = "#666666"
                text = "—"
            else:
                # Normalise to [0, 1] for contrast decision.
                norm = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.0
                colour = "white" if norm > 0.6 else "black"
                text = _annotate_value(val, metric)
            ax.text(j, i, text, ha="center", va="center", color=colour, fontsize=10)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(op, dpi=dpi)
    plt.close(fig)
    return op


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


_METRIC_CHOICES = ("quality", "cost", "cost_total", "wall_ms", "arqgc")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="viz.decision_heatmap",
        description="Category × route heatmap of a chosen metric.",
    )
    p.add_argument("aggregate_json", type=Path, help="Path to aggregate.json")
    p.add_argument(
        "--metric",
        choices=_METRIC_CHOICES,
        default="quality",
        help="Which number to plot in each cell.",
    )
    p.add_argument(
        "--scenario",
        type=str,
        default="openai-gpt5.5",
        help="Pricing scenario (used for cost metrics and arqgc).",
    )
    p.add_argument(
        "--raw",
        type=Path,
        default=None,
        help="Path to raw.jsonl — required when metric=arqgc.",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output PNG path. Default: <aggregate dir>/charts/heatmap_<metric>.png",
    )
    args = p.parse_args(argv)

    agg = json.loads(args.aggregate_json.read_text())
    arqgc = None
    if args.metric == "arqgc":
        raw = args.raw or (args.aggregate_json.parent / "raw.jsonl")
        arqgc = bounded_arqgc(load_results(raw), scenario=args.scenario)

    out = args.out or (args.aggregate_json.parent / "charts" / f"heatmap_{args.metric}.png")
    path = plot_heatmap(agg, out, metric=args.metric, scenario=args.scenario, arqgc=arqgc)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
