"""Custom architecture/reasoning task adapter (Category C).

Five hand-curated tasks that complement BigCodeBench-Hard. These are the
kinds of coding work where functional tests don't apply but quality is
real: architecture design, migration planning, code review, trade-off
explanation, and debug reasoning. They are scored pairwise by an
LLM-judge (see T3.3) against the 5-dimension rubric shipped alongside
each task.

The adapter is intentionally trivial — just loads the JSONL into a
typed structure. No fetching, no caching, no network.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_TASKS_PATH = Path(__file__).resolve().parent / "tasks.jsonl"

RUBRIC_DIMENSIONS = (
    "correctness",
    "completeness",
    "style",
    "reasoning_depth",
    "practicality",
)


@dataclass(frozen=True)
class RubricDimension:
    """One axis of the 5-dimension rubric. ``max`` is always 5 for this set."""

    description: str
    max: int


@dataclass(frozen=True)
class Task:
    """A single category-C task."""

    id: str
    category: str  # always "C" for this adapter
    kind: str  # architecture-design | code-review | tradeoff-explanation | debug-reasoning | migration-plan
    prompt: str
    context: str
    rubric: dict[str, RubricDimension]
    expected_topics: list[str] = field(default_factory=list)


def _parse_task(raw: dict[str, Any]) -> Task:
    rubric_raw = raw.get("rubric") or {}
    rubric = {
        dim: RubricDimension(
            description=rubric_raw[dim]["description"],
            max=int(rubric_raw[dim]["max"]),
        )
        for dim in RUBRIC_DIMENSIONS
        if dim in rubric_raw
    }
    return Task(
        id=raw["id"],
        category=raw.get("category", "C"),
        kind=raw["kind"],
        prompt=raw["prompt"],
        context=raw.get("context", "") or "",
        rubric=rubric,
        expected_topics=list(raw.get("expected_topics", []) or []),
    )


def load_tasks(path: Path | None = None) -> list[Task]:
    """Load all custom architecture tasks from ``tasks.jsonl``.

    Parameters
    ----------
    path
        Override for the default JSONL location. Mostly useful in tests.
    """
    tasks_path = path if path is not None else _TASKS_PATH
    out: list[Task] = []
    with tasks_path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{tasks_path}:{lineno}: invalid JSON ({exc})"
                ) from exc
            out.append(_parse_task(raw))
    return out


__all__ = ["Task", "RubricDimension", "RUBRIC_DIMENSIONS", "load_tasks"]
