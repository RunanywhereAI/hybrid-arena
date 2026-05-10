"""Scorers for Category-D (real-developer) tasks.

Dispatches on ``task.shape``. Real implementations land in **P2.1**:

- **D1 / D2 / D5** — functional: run ``task.tests`` against the model's
  patched fixture tree in a sandbox, compute ``tests_passed / tests_total``.
- **D3 / D4** — judge-based: feed the model output + rubric to the
  LLM-judge (``hybrid_coding_eval.scorers.llm_judge``) and turn the
  rubric scores into a composite.

This file is intentionally a stub so the orchestrator import graph and
``score_row`` dispatch wire up cleanly today. Every branch returns an
empty :class:`Quality` (all ``None``) so rows produced before P2.1 are
flagged as unscored rather than crashing the sweep.
"""

from __future__ import annotations

from typing import Any

from hybrid_coding_eval.core.metrics import Quality

from .adapter import Task


def score(task: Task, model_output: str, *, context: dict | None = None) -> Quality:
    """Dispatch scoring on ``task.shape``.

    Parameters
    ----------
    task
        The Category-D task that was run.
    model_output
        The raw text produced by the runner (already dereferenced from
        ``ResultRow.output_ref`` by :func:`core.experiment.score_row`).
    context
        Scorer-specific side-channel (e.g. a judge-model handle, a
        sandbox runner). Ignored by the stub.

    Returns
    -------
    Quality
        Empty (all-``None``) for now. P2.1 will populate
        ``functional_pass`` / ``tests_passed`` / ``tests_total`` for
        D1, D2, D5 and ``judge_win_rate`` / ``composite`` for D3, D4.
    """
    del model_output, context  # stubs don't use them yet.

    if task.shape in ("D1", "D2", "D5"):
        # TODO: P2.1 — run task.tests against model-patched fixture tree,
        # return Quality(tests_passed=..., tests_total=..., functional_pass=...).
        return Quality()
    if task.shape in ("D3", "D4"):
        # TODO: P2.1 — feed model_output + task.rubric to llm_judge, turn
        # rubric scores into Quality(judge_win_rate=..., composite=...).
        return Quality()

    # Unknown shape — adapter validation should have rejected this. Defensive
    # empty quality rather than raising, so a malformed row doesn't kill the
    # whole sweep.
    return Quality()


__all__ = ["score"]

# Re-export the type so ``from real_dev.scorers import score, Task`` works
# symmetrically to the other benchmark packages.
_ = Any  # keep the import used if downstream callers extend the signature.
