#!/usr/bin/env python
"""Calibrate the P1.3 D3/D4 rubrics.

For each task in ``src/hybrid_coding_eval/benchmarks/real_dev/tasks-d3-d4.jsonl``:

- Build the full model prompt using ``real_dev.adapter.task_prompt``.
- Construct a "gold" candidate output from the fixtures under
  ``fixtures/<slug>/_reference/`` (for D3 this is the refactored file
  tree; for D4 this is ``gold_review.md``).
- Construct an "obviously wrong" candidate output (renamed-file-only
  for D3; ``LGTM, merge.`` for D4).
- Run the LLM judge with the gold candidate as A and the wrong as B,
  then print each side's per-dimension score.
- Assert gold ≥ 4.5 on every dim and wrong ≤ 2.5 on every dim.

The judge treats rubric values as objects with a ``.description``
attribute (see ``llm_judge._rubric_lines``) — the real_dev Task exposes
them as plain strings, so we wrap each task in a small adapter that
inflates the strings into shim dimension objects before calling the
judge.

Run once. The script is intentionally single-purpose and lives in
``bin/`` for P1.3; P2.1 may relocate it into ``tests/``.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from hybrid_coding_eval.benchmarks.real_dev.adapter import (  # noqa: E402
    Task as RealDevTask,
    load_tasks,
    task_prompt,
)
from hybrid_coding_eval.scorers.llm_judge import judge_pairwise  # noqa: E402

_TASKS_PATH = _REPO_ROOT / "src/hybrid_coding_eval/benchmarks/real_dev/tasks-d3-d4.jsonl"
_FIXTURES_ROOT = _REPO_ROOT / "src/hybrid_coding_eval/benchmarks/real_dev/fixtures"

_DIMENSIONS = ("correctness", "completeness", "style", "reasoning_depth", "practicality")

_GOLD_MIN = 4.5
_WRONG_MAX = 2.5


# --------------------------------------------------------------------------- #
# rubric-string adapter
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _RubricShim:
    """Thin object with a ``.description`` attribute.

    ``llm_judge._rubric_lines`` does ``getattr(rubric[dim], 'description', '')``
    — it needs an object, not a bare string. We wrap each real_dev rubric
    value in this shim so the judge sees the description.
    """

    description: str


@dataclass(frozen=True)
class _JudgeTask:
    """Duck-typed task the judge expects: needs ``prompt`` and ``rubric``."""

    prompt: str
    rubric: dict[str, _RubricShim] = field(default_factory=dict)


def _to_judge_task(task: RealDevTask, *, full_prompt: str) -> _JudgeTask:
    shim = {
        dim: _RubricShim(description=(task.rubric or {}).get(dim, ""))
        for dim in _DIMENSIONS
    }
    return _JudgeTask(prompt=full_prompt, rubric=shim)


# --------------------------------------------------------------------------- #
# fixture loaders
# --------------------------------------------------------------------------- #


def _read_reference_tree(fixtures_dir: Path) -> str:
    """Return a single string that concatenates every file under
    ``fixtures_dir/_reference/`` in the same ``### name\n```...``` `` block
    format used by ``task_prompt``. This mirrors how a model's final answer
    would look if it wrote every post-refactor file verbatim.
    """
    ref_dir = fixtures_dir / "_reference"
    if not ref_dir.is_dir():
        raise FileNotFoundError(f"missing reference dir: {ref_dir}")
    parts: list[str] = []
    for path in sorted(ref_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ref_dir).as_posix()
        contents = path.read_text(encoding="utf-8")
        parts.append(f"### {rel}\n```\n{contents}\n```")
    if not parts:
        raise FileNotFoundError(f"reference dir is empty: {ref_dir}")
    return "\n\n".join(parts)


def _read_gold_review(fixtures_dir: Path) -> str:
    path = fixtures_dir / "_reference" / "gold_review.md"
    if not path.is_file():
        raise FileNotFoundError(f"missing gold review: {path}")
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# wrong-answer constructors
# --------------------------------------------------------------------------- #


_WRONG_D3 = """\
I renamed the file from `utils.py` to `helpers.py` but did not change any
of the code inside. All the original duplication is still present. No
extraction, no new helper, no call-site updates.

### helpers.py
```
# (contents identical to the original — no refactor performed)
```
"""


_WRONG_D4 = "LGTM, merge."


# --------------------------------------------------------------------------- #
# per-task calibration
# --------------------------------------------------------------------------- #


def _load_tasks() -> list[RealDevTask]:
    tasks = load_tasks(path=_TASKS_PATH)
    if len(tasks) != 8:
        raise RuntimeError(f"expected 8 tasks, got {len(tasks)}")
    return tasks


def _calibrate_one(task: RealDevTask) -> dict[str, Any]:
    fixtures_dir = _FIXTURES_ROOT / (task.fixtures_dir or task.id.split("/")[-1])
    full_prompt = task_prompt(task, fixtures_root=_FIXTURES_ROOT)
    judge_task = _to_judge_task(task, full_prompt=full_prompt)

    if task.shape == "D3":
        gold = _read_reference_tree(fixtures_dir)
        wrong = _WRONG_D3
    elif task.shape == "D4":
        gold = _read_gold_review(fixtures_dir)
        wrong = _WRONG_D4
    else:
        raise RuntimeError(f"unexpected shape: {task.shape}")

    result = judge_pairwise(judge_task, gold, wrong)
    return {
        "task": task.id,
        "shape": task.shape,
        "gold_dims": dict(result.a_dimensions),
        "wrong_dims": dict(result.b_dimensions),
        "gold_overall": result.a_score,
        "wrong_overall": result.b_score,
        "winner": result.winner,
        "margin": result.margin,
    }


def _fmt_row(label: str, dims: dict[str, float], overall: float) -> str:
    cells = " ".join(f"{dims[d]:>4.2f}" for d in _DIMENSIONS)
    return f"    {label:<6} {cells}  overall={overall:.2f}"


def _print_matrix(rows: list[dict[str, Any]]) -> None:
    header_cells = " ".join(f"{d[:4]:>4}" for d in _DIMENSIONS)
    print()
    print(f"{'task':<50} shape {header_cells}")
    print("-" * 110)
    for row in rows:
        print(f"{row['task']:<50} {row['shape']}")
        print(_fmt_row("gold", row["gold_dims"], row["gold_overall"]))
        print(_fmt_row("wrong", row["wrong_dims"], row["wrong_overall"]))
        print(f"    winner={row['winner']} margin={row['margin']:.2f}")
    print("-" * 110)


def _check_calibration(rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for row in rows:
        for dim in _DIMENSIONS:
            g = row["gold_dims"][dim]
            w = row["wrong_dims"][dim]
            if g < _GOLD_MIN:
                failures.append(
                    f"{row['task']}: gold.{dim}={g:.2f} < {_GOLD_MIN}"
                )
            if w > _WRONG_MAX:
                failures.append(
                    f"{row['task']}: wrong.{dim}={w:.2f} > {_WRONG_MAX}"
                )
    return failures


def main() -> int:
    # Trigger the judge's .env loader by touching one of its private helpers;
    # importing the module is enough because ``_resolve_api_key`` walks to the
    # repo root on first call. But we want a clear error up front if nothing
    # is set, rather than failing at the first judge call.
    if "ANTHROPIC_API_KEY" not in os.environ:
        env_path = _REPO_ROOT / ".env"
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ANTHROPIC_API_KEY not set and no .env fallback", file=sys.stderr)
        return 2

    tasks = _load_tasks()
    rows: list[dict[str, Any]] = []
    for task in tasks:
        print(f"[calibrating] {task.id} ({task.shape}) ...", flush=True)
        try:
            row = _calibrate_one(task)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR: {exc!r}", file=sys.stderr)
            return 3
        rows.append(row)

    _print_matrix(rows)

    failures = _check_calibration(rows)
    if failures:
        print("\nCALIBRATION FAILURES:")
        for msg in failures:
            print(f"  - {msg}")
        return 1

    print("\nall tasks calibrated: gold >= 4.5, wrong <= 2.5 on every dimension.")

    # Dump a machine-readable summary next to the JSONL in case we want to
    # pin the scores in a follow-up commit.
    summary_path = _REPO_ROOT / "src/hybrid_coding_eval/benchmarks/real_dev" / "_calibration.json"
    summary_path.write_text(
        json.dumps(rows, indent=2, sort_keys=True, default=float) + "\n",
        encoding="utf-8",
    )
    print(f"summary written to {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
