"""Tests for :mod:`viz.cost_quality_pareto` and :mod:`viz.decision_heatmap`.

Smoke tests only — we verify that each script produces a non-zero-sized
PNG when given a 10-row synthetic fixture. Testing the visual correctness
of matplotlib output is out of scope.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lib.metrics import Latency, Quality, ResultRow, Routing, TokenUsage  # noqa: E402
from lib.results import append_row  # noqa: E402

from analysis.aggregate import aggregate_results  # noqa: E402
from analysis.arqgc import bounded_arqgc  # noqa: E402
from viz.cost_quality_pareto import plot_pareto  # noqa: E402
from viz.decision_heatmap import plot_heatmap  # noqa: E402


def _mk_row(
    task_id: str,
    category: str,
    route: str,
    composite: float,
    cloud_prompt: int = 0,
    cloud_completion: int = 0,
    local_prompt: int = 0,
    local_completion: int = 0,
) -> ResultRow:
    return ResultRow(
        task_id=task_id,
        category=category,
        route=route,
        hardware_profile_ref="hw",
        tokens=TokenUsage(
            prompt=cloud_prompt + local_prompt,
            completion=cloud_completion + local_completion,
            cloud_prompt=cloud_prompt,
            cloud_completion=cloud_completion,
            local_prompt=local_prompt,
            local_completion=local_completion,
        ),
        latency=Latency(wall_ms=1000, per_call_ms=[1000]),
        quality=Quality(composite=composite, functional_pass=composite > 0.5),
        routing=Routing(
            total_calls=1, local_calls=0, cloud_calls=1, per_call_backends=["x"]
        ),
        output_ref="out.txt",
    )


def _make_fixture(tmp_path: Path):
    rows = []
    # 10 rows: 2 categories × 3 routes, varying quality + cost.
    configs = [
        ("A", "R1", 0.9, 1000, 500, 0, 0),
        ("A", "R1", 0.85, 1200, 400, 0, 0),
        ("A", "R2", 0.5, 0, 0, 1000, 500),
        ("A", "R2", 0.55, 0, 0, 1100, 550),
        ("A", "R3", 0.8, 500, 250, 500, 250),
        ("B", "R1", 0.7, 2000, 1000, 0, 0),
        ("B", "R1", 0.75, 1800, 900, 0, 0),
        ("B", "R2", 0.6, 0, 0, 2000, 1000),
        ("B", "R3", 0.72, 1000, 500, 1000, 500),
        ("B", "R3", 0.78, 1200, 600, 800, 400),
    ]
    for i, (cat, route, q, cp, cc, lp, lc) in enumerate(configs):
        rows.append(_mk_row(f"t{i}", cat, route, q, cp, cc, lp, lc))

    raw_path = tmp_path / "raw.jsonl"
    for r in rows:
        append_row(raw_path, r)
    agg = aggregate_results(raw_path, tmp_path / "aggregate.json")
    arqgc = bounded_arqgc(rows, "openai-gpt5.5")
    return rows, agg, arqgc


def test_pareto_png_is_created_non_empty(tmp_path: Path):
    rows, _, _ = _make_fixture(tmp_path)
    out = tmp_path / "charts" / "pareto.png"
    plot_pareto(rows, out, scenario="openai-gpt5.5")
    assert out.exists()
    assert out.stat().st_size > 1000  # PNGs are always > 1 KB, even tiny ones.


def test_heatmap_quality_png(tmp_path: Path):
    _, agg, _ = _make_fixture(tmp_path)
    out = tmp_path / "charts" / "heatmap_quality.png"
    plot_heatmap(agg, out, metric="quality")
    assert out.exists()
    assert out.stat().st_size > 1000


def test_heatmap_cost_png(tmp_path: Path):
    _, agg, _ = _make_fixture(tmp_path)
    out = tmp_path / "charts" / "heatmap_cost.png"
    plot_heatmap(agg, out, metric="cost", scenario="openai-gpt5.5")
    assert out.exists()
    assert out.stat().st_size > 1000


def test_heatmap_arqgc_png(tmp_path: Path):
    _, agg, arqgc = _make_fixture(tmp_path)
    out = tmp_path / "charts" / "heatmap_arqgc.png"
    plot_heatmap(agg, out, metric="arqgc", scenario="openai-gpt5.5", arqgc=arqgc)
    assert out.exists()
    assert out.stat().st_size > 1000


def test_heatmap_missing_arqgc_raises(tmp_path: Path):
    _, agg, _ = _make_fixture(tmp_path)
    import pytest

    out = tmp_path / "charts" / "heatmap_bad.png"
    with pytest.raises(ValueError):
        plot_heatmap(agg, out, metric="arqgc", arqgc=None)
