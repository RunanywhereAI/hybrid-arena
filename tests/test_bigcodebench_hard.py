"""Tests for benchmark/bigcodebench_hard/adapter.py (T1.3).

Three tests:

1. ``load_tasks(n=5)`` returns exactly 5 ``Task`` instances with the
   expected id namespace and category.
2. Every required field is populated (non-empty and of the right type)
   and the libs list is parsed into a proper list of strings.
3. Reproducibility — repeated calls return identical id sequences, and
   the pinned jsonl on disk has exactly 5 entries matching what
   ``load_tasks`` returns.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmark.bigcodebench_hard.adapter import (
    ID_PREFIX,
    Task,
    _PINNED_JSONL,
    load_tasks,
)


def test_load_tasks_returns_five_with_default_seed() -> None:
    tasks = load_tasks(n=5, seed=42)
    assert isinstance(tasks, list)
    assert len(tasks) == 5
    for t in tasks:
        assert isinstance(t, Task)
        assert t.id.startswith(f"{ID_PREFIX}/")
        assert t.category == "C"


def test_required_fields_are_non_empty() -> None:
    tasks = load_tasks(n=5, seed=42)
    for t in tasks:
        assert t.id and isinstance(t.id, str)
        assert t.instruct_prompt and isinstance(t.instruct_prompt, str)
        assert t.complete_prompt and isinstance(t.complete_prompt, str)
        assert t.canonical_solution and isinstance(t.canonical_solution, str)
        assert t.test and isinstance(t.test, str)
        assert t.entry_point and isinstance(t.entry_point, str)
        # Libraries must parse into a proper list[str] — the upstream
        # column is a JSON-ish string and our adapter owns the parsing.
        assert isinstance(t.libs, list)
        assert len(t.libs) > 0
        for lib in t.libs:
            assert isinstance(lib, str) and lib
        # The entry-point name must appear somewhere in both prompt
        # flavours (sanity check that the stub matches the function
        # the test will call).
        assert t.entry_point in t.complete_prompt
        # Metadata must track the upstream task id so the scorer can
        # cross-reference bigcodebench's own harness if we ever want to.
        assert t.metadata.get("upstream_task_id")


def test_reproducibility_and_pinned_jsonl() -> None:
    first = load_tasks(n=5, seed=42)
    second = load_tasks(n=5, seed=42)

    first_ids = [t.id for t in first]
    second_ids = [t.id for t in second]

    # Determinism: two calls in the same process return the same ids.
    assert first_ids == second_ids

    # The pinned file exists and has exactly 5 lines, whose ids match
    # what `load_tasks` returns. This is what makes the sample
    # reproducible across machines / datasets releases.
    assert _PINNED_JSONL.exists(), "tasks.jsonl must ship with the adapter"

    jsonl_lines = [
        line for line in _PINNED_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(jsonl_lines) == 5

    pinned_ids = [json.loads(line)["id"] for line in jsonl_lines]
    assert pinned_ids == first_ids
