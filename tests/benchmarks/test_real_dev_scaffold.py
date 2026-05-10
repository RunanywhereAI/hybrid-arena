"""Scaffold tests for the real_dev (Category-D) benchmark adapter (P0.3).

These tests verify plumbing only: the adapter can be imported, parses a
well-formed JSONL row into a Task, handles an empty tasks.jsonl
gracefully, and the orchestrator recognises category ``"D"``. Actual
tasks land in P1.1–P1.4.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hybrid_coding_eval.benchmarks.real_dev import scorers as real_dev_scorers
from hybrid_coding_eval.benchmarks.real_dev.adapter import (
    Task,
    load_tasks,
    task_prompt,
)
from hybrid_coding_eval.core.experiment import CATEGORY_SOURCES, load_category_tasks
from hybrid_coding_eval.core.metrics import Quality


def test_load_tasks_empty_file_returns_empty_list(tmp_path: Path) -> None:
    """Empty tasks.jsonl must not crash — it just yields no tasks."""
    empty = tmp_path / "tasks.jsonl"
    empty.write_text("", encoding="utf-8")

    tasks = load_tasks(path=empty)

    assert tasks == [], f"expected empty list, got {tasks!r}"


def test_load_tasks_missing_file_returns_empty_list(tmp_path: Path) -> None:
    """Non-existent tasks.jsonl also returns [] (no FileNotFoundError)."""
    missing = tmp_path / "does-not-exist.jsonl"

    tasks = load_tasks(path=missing)

    assert tasks == []


def test_load_tasks_default_path_does_not_crash() -> None:
    """The real on-disk tasks.jsonl (currently empty) must load cleanly."""
    tasks = load_tasks()
    # Empty today; becomes non-empty once P1.1–P1.4 populate it.
    assert isinstance(tasks, list)
    assert all(isinstance(t, Task) for t in tasks)


def test_load_tasks_parses_one_placeholder_row(tmp_path: Path) -> None:
    """A single well-formed JSONL line yields exactly one Task with the
    expected fields populated."""
    row = {
        "id": "real-dev/d1-placeholder",
        "shape": "D1",
        "prompt": "Add a hello-world handler.",
        "fixtures_dir": "d1-placeholder",
        "tests": "d1-placeholder/test_hello.py",
        "source_url": "https://example.com/foo",
        "source_license": "MIT",
    }
    fixture = tmp_path / "tasks.jsonl"
    fixture.write_text(json.dumps(row) + "\n", encoding="utf-8")

    tasks = load_tasks(path=fixture)

    assert len(tasks) == 1
    t = tasks[0]
    assert t.id == "real-dev/d1-placeholder"
    assert t.category == "D"
    assert t.shape == "D1"
    assert t.prompt == "Add a hello-world handler."
    assert t.fixtures_dir == "d1-placeholder"
    assert t.tests == "d1-placeholder/test_hello.py"
    assert t.source_url == "https://example.com/foo"
    assert t.source_license == "MIT"
    assert t.rubric is None


def test_load_tasks_n_caps_count(tmp_path: Path) -> None:
    """``n=1`` on a two-row file returns just the first row."""
    rows = [
        {"id": "real-dev/d1-a", "shape": "D1", "prompt": "a"},
        {"id": "real-dev/d2-b", "shape": "D2", "prompt": "b"},
    ]
    fixture = tmp_path / "tasks.jsonl"
    fixture.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    tasks = load_tasks(n=1, path=fixture)

    assert len(tasks) == 1
    assert tasks[0].id == "real-dev/d1-a"


def test_load_tasks_rejects_bad_shape(tmp_path: Path) -> None:
    """An unknown shape letter must raise — protects downstream dispatch."""
    row = {"id": "real-dev/bogus", "shape": "Z9", "prompt": "x"}
    fixture = tmp_path / "tasks.jsonl"
    fixture.write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="shape"):
        load_tasks(path=fixture)


def test_task_prompt_returns_raw_prompt_when_no_fixtures() -> None:
    """Tasks without fixtures_dir pass through unchanged."""
    t = Task(id="real-dev/x", shape="D1", prompt="Just this.")
    assert task_prompt(t) == "Just this."


def test_task_prompt_inlines_fixture_files(tmp_path: Path) -> None:
    """For any shape with fixtures, the file contents are appended."""
    fixtures_root = tmp_path / "fixtures"
    slug_dir = fixtures_root / "d1-demo"
    slug_dir.mkdir(parents=True)
    (slug_dir / "test_demo.py").write_text("assert 1 == 1\n", encoding="utf-8")

    t = Task(
        id="real-dev/d1-demo",
        shape="D1",
        prompt="Write code that makes this test pass.",
        fixtures_dir="d1-demo",
        tests="d1-demo/test_demo.py",
    )

    rendered = task_prompt(t, fixtures_root=fixtures_root)

    assert "Write code that makes this test pass." in rendered
    assert "test_demo.py" in rendered
    assert "assert 1 == 1" in rendered


def test_category_d_registered_in_source_map() -> None:
    """Orchestrator must know ``"D" → ["real_dev"]``."""
    assert "D" in CATEGORY_SOURCES, (
        "Category 'D' must be registered in core.experiment.CATEGORY_SOURCES"
    )
    assert CATEGORY_SOURCES["D"] == ["real_dev"]


def test_category_d_dispatch_does_not_crash() -> None:
    """``load_category_tasks('D')`` must return a list (possibly empty) without
    raising. This is the end-to-end wiring check."""
    pairs = load_category_tasks("D")
    assert isinstance(pairs, list)
    # Empty today; every pair should be ("real_dev", Task) once populated.
    for source, task in pairs:
        assert source == "real_dev"
        assert isinstance(task, Task)


def test_scorers_score_returns_quality_for_each_shape() -> None:
    """The P2.1 dispatcher must not crash for any valid shape and must
    return a :class:`Quality` object.

    Task inputs here are deliberately minimal (no fixtures_dir, no tests,
    no rubric) so each branch hits its early-return guard rather than
    actually running pytest or the judge. The contract checked here is
    structural (never raises, always returns a ``Quality``); behavioural
    assertions on each branch live in ``tests/scorers/test_real_dev_scorers.py``.
    """
    for shape in ("D1", "D2", "D3", "D4", "D5"):
        t = Task(id=f"real-dev/{shape.lower()}-x", shape=shape, prompt="stub")
        q = real_dev_scorers.score(t, model_output="", context={})
        assert isinstance(q, Quality)
        # Branches are allowed to return either:
        #   - all-None ("not graded" — D2 deferred, D3/D4 missing fixtures)
        #   - a zero/failing Quality (D1/D5 short-circuit when fixtures_dir
        #     is missing — the model can't possibly have passed tests).
        # We just assert they don't crash and return the right type.
