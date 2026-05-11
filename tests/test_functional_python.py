"""Tests for ``scorers.functional_python``.

Each test that needs Docker is skipped cleanly on hosts without a
reachable daemon. The first test exercising the custom image may be
slow because Docker has to load it from disk; build it with::

    docker build -f scorers/Dockerfile.functional_python \
        -t hybrid-eval-python:latest .

These tests hit both task-type branches (HumanEval+ + BigCodeBench-Hard)
and all four code-extraction paths required by T3.1.
"""

from __future__ import annotations

import pytest

from hybrid_coding_eval.core.metrics import Quality
from hybrid_coding_eval.scorers.functional_python import (
    DEFAULT_IMAGE,
    extract_python_code,
    score,
)

# ---------------------------------------------------------------------------
# Docker availability probe
# ---------------------------------------------------------------------------


def _docker_available() -> bool:
    try:
        import docker  # type: ignore[import-untyped]
    except ImportError:
        return False
    try:
        client = docker.from_env()
        client.ping()
    except Exception:
        return False
    return True


def _image_available(tag: str) -> bool:
    try:
        import docker  # type: ignore[import-untyped]
    except ImportError:
        return False
    try:
        client = docker.from_env()
        client.images.get(tag)
    except Exception:
        return False
    return True


requires_docker = pytest.mark.skipif(
    not _docker_available(), reason="docker daemon not reachable"
)

requires_scorer_image = pytest.mark.skipif(
    not _image_available(DEFAULT_IMAGE),
    reason=f"scorer image {DEFAULT_IMAGE} not built; run `docker build -f scorers/Dockerfile.functional_python -t {DEFAULT_IMAGE} .`",
)


# ---------------------------------------------------------------------------
# Code-extraction unit tests (no Docker needed)
# ---------------------------------------------------------------------------


def test_extract_raw_code():
    """Plain code with no fences is returned verbatim."""
    src = "def foo():\n    return 1\n"
    assert extract_python_code(src).strip() == src.strip()


def test_extract_python_fence():
    """```python fenced block is extracted cleanly."""
    src = "Here you go:\n```python\ndef foo():\n    return 1\n```\nCheers."
    out = extract_python_code(src)
    assert "def foo()" in out
    assert "Cheers" not in out
    assert "Here you go" not in out


def test_extract_generic_fence():
    """Untagged ``` fence is still recognised."""
    src = "```\ndef foo():\n    return 1\n```"
    out = extract_python_code(src)
    assert "def foo()" in out
    assert "```" not in out


def test_extract_multiple_fences_concatenated():
    """Multiple python fences are concatenated; largest first."""
    src = (
        "```python\ndef helper():\n    return 2\n```\n"
        "some prose\n"
        "```python\ndef main():\n    return helper() + 1\n```\n"
    )
    out = extract_python_code(src)
    assert "def helper" in out
    assert "def main" in out
    assert "some prose" not in out


def test_extract_empty():
    """Empty / whitespace input returns empty string."""
    assert extract_python_code("") == ""
    assert extract_python_code("   \n") == ""


# ---------------------------------------------------------------------------
# Fixtures: load a real HumanEval+ + BigCodeBench-Hard task from the
# pinned jsonl caches (no network).
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def humaneval_task():
    from hybrid_coding_eval.benchmarks.humaneval_plus.adapter import load_tasks

    tasks = load_tasks()
    assert tasks, "no HumanEval+ tasks loaded from cache"
    return tasks[0]


@pytest.fixture(scope="module")
def bigcodebench_task():
    from hybrid_coding_eval.benchmarks.bigcodebench_hard.adapter import load_tasks

    tasks = load_tasks()
    assert tasks, "no BigCodeBench-Hard tasks loaded from cache"
    return tasks[0]


# ---------------------------------------------------------------------------
# End-to-end tests (need Docker + the scorer image)
# ---------------------------------------------------------------------------


@requires_docker
@requires_scorer_image
def test_humaneval_canonical_passes(humaneval_task):
    """The dataset's own canonical solution must score as a full pass."""
    # For HumanEval+ the canonical_solution is the function body; the
    # scorer's body-detection prepends ``task.prompt`` automatically.
    q = score(humaneval_task, humaneval_task.canonical_solution, timeout_s=120)
    assert isinstance(q, Quality)
    assert q.functional_pass is True, (
        f"canonical HumanEval+ should pass; got {q}"
    )
    assert q.tests_passed == q.tests_total and q.tests_total > 0
    assert q.composite == 1.0


@requires_docker
@requires_scorer_image
def test_humaneval_wrong_solution_fails(humaneval_task):
    """A stub that returns ``None`` must be flagged as a failure."""
    wrong = f"def {humaneval_task.entry_point}(*args, **kwargs):\n    return None\n"
    q = score(humaneval_task, wrong, timeout_s=120)
    assert q.functional_pass is False
    assert (q.tests_passed or 0) < (q.tests_total or 1) or q.tests_total == 0
    assert (q.composite or 0.0) < 1.0


@requires_docker
@requires_scorer_image
def test_humaneval_markdown_fence_extracts(humaneval_task):
    """Wrapping the canonical in ```python fences still scores full-pass."""
    body = humaneval_task.canonical_solution
    # Build a proper top-level function the extractor can lift cleanly.
    full = humaneval_task.prompt.rstrip() + "\n" + body + "\n"
    wrapped = f"```python\n{full}\n```"
    q = score(humaneval_task, wrapped, timeout_s=120)
    assert q.functional_pass is True, f"fenced canonical should pass; got {q}"
    assert q.composite == 1.0


@requires_docker
@requires_scorer_image
def test_humaneval_prose_around_code(humaneval_task):
    """Prose before + after a python fence is stripped; canonical passes."""
    body = humaneval_task.canonical_solution
    full = humaneval_task.prompt.rstrip() + "\n" + body + "\n"
    wrapped = (
        "Sure! Here is the answer to your problem:\n\n"
        f"```python\n{full}\n```\n\n"
        "Hope this helps — let me know if you need more edge cases covered."
    )
    q = score(humaneval_task, wrapped, timeout_s=120)
    assert q.functional_pass is True, f"prose-wrapped canonical should pass; got {q}"


@requires_docker
@requires_scorer_image
def test_bigcodebench_canonical_passes(bigcodebench_task):
    """The BigCodeBench-Hard canonical solution must also pass.

    Exercises the Category-C branch: ``unittest.TestCase`` tests,
    third-party libs from the custom image, and the body-detection
    prepending ``complete_prompt``.
    """
    q = score(
        bigcodebench_task,
        bigcodebench_task.canonical_solution,
        timeout_s=180,
    )
    assert isinstance(q, Quality)
    assert q.functional_pass is True, (
        f"canonical BigCodeBench-Hard should pass; got {q}"
    )
    assert q.tests_passed == q.tests_total and q.tests_total > 0
    assert q.composite == 1.0
