"""BigCodeBench-Hard adapter.

Loads the `bigcode/bigcodebench-hard` dataset from the Hugging Face hub and
exposes a small, deterministic N-task sample for our eval harness.

Category-C of the plan: library-intensive programming tasks that require
using specific Python APIs (numpy, pandas, flask, cv2, ...). These are
more realistic than HumanEval's pure-algorithm problems and act as a
bridge between the "tiny function-completion" tier and the full agentic
SWE-bench tier.

Upstream: https://huggingface.co/datasets/bigcode/bigcodebench-hard
Paper:    https://arxiv.org/abs/2406.15877
License:  Apache 2.0 (see README.md in this directory).
"""

from __future__ import annotations

import ast
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Hugging Face dataset repo id.
DATASET_ID = "bigcode/bigcodebench-hard"

#: Split to pull from. BigCodeBench is versioned — splits correspond to
#: successive curation passes. ``v0.1.4`` is the latest stable release
#: (see upstream README for the version cadence). Pinning here makes our
#: sample reproducible across future dataset updates.
DATASET_SPLIT = "v0.1.4"

#: Our namespace prefix. Every task id we emit has this form:
#: ``bigcodebench-hard/<upstream_task_id>`` which matches the convention
#: used by other adapters (humaneval+/..., swebench-verified/...).
ID_PREFIX = "bigcodebench-hard"

#: Location of the pinned jsonl cache, relative to this file.
_PKG_DIR = Path(__file__).resolve().parent
_PINNED_JSONL = _PKG_DIR / "tasks.jsonl"


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class Task:
    """A single BigCodeBench-Hard task in our uniform shape.

    Fields mirror what the runners/scorers consume across every benchmark
    adapter. ``metadata`` carries source-specific extras (upstream task_id,
    doc_struct, raw libs string, q_idx, score) that scorers may ignore.
    """

    id: str                  # e.g. "bigcodebench-hard/BigCodeBench/1234"
    instruct_prompt: str     # instruct-style prompt we send to the model
    complete_prompt: str     # complete-style prompt (stub + docstring)
    canonical_solution: str  # reference solution body
    test: str                # pytest / unittest code
    entry_point: str         # function name the test calls
    libs: list[str]          # libraries this task requires
    category: str = "C"
    metadata: dict[str, Any] = field(default_factory=dict)

    # --- serialization helpers ------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "instruct_prompt": self.instruct_prompt,
            "complete_prompt": self.complete_prompt,
            "canonical_solution": self.canonical_solution,
            "test": self.test,
            "entry_point": self.entry_point,
            "libs": list(self.libs),
            "category": self.category,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Task":
        return cls(
            id=d["id"],
            instruct_prompt=d["instruct_prompt"],
            complete_prompt=d["complete_prompt"],
            canonical_solution=d["canonical_solution"],
            test=d["test"],
            entry_point=d["entry_point"],
            libs=list(d.get("libs", [])),
            category=d.get("category", "C"),
            metadata=dict(d.get("metadata", {})),
        )


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------


def _parse_libs(raw: Any) -> list[str]:
    """The upstream ``libs`` column is a *string* representation of a
    Python list (e.g. ``"['numpy', 'pandas']"``). Parse it robustly."""
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return []
        try:
            val = ast.literal_eval(raw)
        except (SyntaxError, ValueError):
            return []
        if isinstance(val, list):
            return [str(x) for x in val]
    return []


def _row_to_task(row: dict[str, Any]) -> Task:
    upstream_id = row["task_id"]
    libs = _parse_libs(row.get("libs"))
    return Task(
        id=f"{ID_PREFIX}/{upstream_id}",
        instruct_prompt=row["instruct_prompt"],
        complete_prompt=row["complete_prompt"],
        canonical_solution=row["canonical_solution"],
        test=row["test"],
        entry_point=row["entry_point"],
        libs=libs,
        category="C",
        metadata={
            "upstream_task_id": upstream_id,
            "upstream_dataset": DATASET_ID,
            "upstream_split": DATASET_SPLIT,
            "code_prompt": row.get("code_prompt", ""),
            "doc_struct": row.get("doc_struct", ""),
            "libs_raw": row.get("libs", ""),
            "q_idx": row.get("q_idx"),
            "score": row.get("score"),
        },
    )


def _load_from_pinned() -> list[Task] | None:
    """Return tasks from the pinned jsonl if it exists, else None."""
    if not _PINNED_JSONL.exists():
        return None
    out: list[Task] = []
    with _PINNED_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(Task.from_dict(json.loads(line)))
    return out


def _load_from_hub(cache_dir: Path | None) -> list[dict[str, Any]]:
    """Load the full BigCodeBench-Hard split from HF hub."""
    # Import lazily so that loading the pinned jsonl does not require the
    # `datasets` package to be installed.
    from datasets import load_dataset  # type: ignore

    kwargs: dict[str, Any] = {"split": DATASET_SPLIT}
    if cache_dir is not None:
        kwargs["cache_dir"] = str(cache_dir)
    ds = load_dataset(DATASET_ID, **kwargs)
    return [dict(row) for row in ds]


def load_tasks(
    n: int = 5,
    seed: int = 42,
    cache_dir: Path | None = None,
) -> list[Task]:
    """Load ``n`` BigCodeBench-Hard tasks, sampled deterministically.

    Strategy:

    1. If a pinned ``tasks.jsonl`` already exists next to this adapter and
       it contains at least ``n`` rows, return the first ``n`` of those.
       This is the path used in CI, on offline machines, and during
       normal eval runs so results stay reproducible even if the upstream
       dataset gets revised.
    2. Otherwise, pull the dataset from the Hugging Face hub, sample
       ``n`` rows with ``random.Random(seed).sample(...)``, convert to
       our ``Task`` shape and return.

    The ``seed`` argument pins the sampling. With ``seed=42`` and
    ``n=5`` against the ``v0.1.4`` split (148 rows) the selected indices
    are ``[28, 6, 70, 62, 57]`` → task_ids ``BigCodeBench/214, /82, /530,
    /501, /458``. These are frozen in ``tasks.jsonl``.
    """
    if n <= 0:
        return []

    pinned = _load_from_pinned()
    if pinned is not None and len(pinned) >= n:
        return pinned[:n]

    rows = _load_from_hub(cache_dir)
    rng = random.Random(seed)
    indices = rng.sample(range(len(rows)), n)
    return [_row_to_task(rows[i]) for i in indices]


# ---------------------------------------------------------------------------
# CLI (used by maintainers to refresh tasks.jsonl)
# ---------------------------------------------------------------------------


def _write_pinned(tasks: list[Task], path: Path = _PINNED_JSONL) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t.to_dict(), ensure_ascii=False))
            f.write("\n")


def _main() -> None:  # pragma: no cover — maintainer tool
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="HF datasets cache directory (optional).",
    )
    ap.add_argument(
        "--write",
        action="store_true",
        help=f"Write the sampled tasks to {_PINNED_JSONL.name}.",
    )
    args = ap.parse_args()

    # Force a fresh pull from the hub by moving the pinned file aside.
    tmp_pin = _PINNED_JSONL.with_suffix(".jsonl.bak") if _PINNED_JSONL.exists() else None
    if tmp_pin is not None:
        _PINNED_JSONL.rename(tmp_pin)
    try:
        tasks = load_tasks(n=args.n, seed=args.seed, cache_dir=args.cache_dir)
    finally:
        if tmp_pin is not None and tmp_pin.exists() and not _PINNED_JSONL.exists():
            tmp_pin.rename(_PINNED_JSONL)

    union: set[str] = set()
    for t in tasks:
        union.update(t.libs)
        print(f"{t.id}  libs={t.libs}")
    print(f"\nUnion libs ({len(union)}): {sorted(union)}")

    if args.write:
        if tmp_pin is not None and tmp_pin.exists():
            tmp_pin.unlink()
        _write_pinned(tasks)
        print(f"\nWrote {len(tasks)} tasks → {_PINNED_JSONL}")


if __name__ == "__main__":  # pragma: no cover
    _main()
