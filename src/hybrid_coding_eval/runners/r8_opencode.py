"""R8 — opencode CLI agent on real-dev D1+D5 fixtures.

opencode (github.com/anomalyco/opencode) is a TypeScript+Bun coding agent
with Read/Write/Edit/Bash/Grep/Glob tools. The user's
``~/.config/opencode/opencode.json`` already registers a ``hybrid-router``
provider pointed at ``http://127.0.0.1:8787/v1`` with 7 router strategies
as model IDs, so we invoke opencode with ``--model
hybrid-router/router/<strategy>`` and routing happens in the proxy.

What R8 does, per task:
  1. Copy the real-dev fixture into a per-run scratch dir.
  2. Subprocess ``opencode run --cwd <scratch> --model
     hybrid-router/router/<strategy> --message <prompt>``.
  3. Score by running pytest on the (modified) fixture.
  4. Reconstruct token attribution from ``decisions.jsonl``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hybrid_coding_eval.core.metrics import (
    Latency,
    Quality,
    ResultRow,
    Routing,
    TokenUsage,
)
from hybrid_coding_eval.core.paths import repo_root as _resolve_repo_root

__all__ = ["run", "ROUTE"]

ROUTE = "R8"
_REPO_ROOT: Path = _resolve_repo_root()

DEFAULT_TIMEOUT_S: int = 900


def _task_slug(task_id: str) -> str:
    return task_id.replace("/", "__").replace(" ", "_")


def _attribute_from_decisions_log(
    started_at: datetime,
    finished_at: datetime,
    strategy: str,
) -> tuple[TokenUsage, Routing]:
    from hybrid_coding_eval.runners.r6_mini_swe_agent import (
        _attribute_from_decisions_log as _attr,
    )

    return _attr(started_at, finished_at, strategy)


_REAL_DEV_FIXTURES_ROOT: Path = (
    _REPO_ROOT / "src" / "hybrid_coding_eval" / "benchmarks" / "real_dev" / "fixtures"
)


def _copy_fixture(task: Any, dst: Path) -> Path:
    """Copy real-dev fixture (D1-D5) into ``dst``.

    Real-dev tasks expose ``fixtures_dir`` as a *relative* slug; the actual
    fixture lives at
    ``src/hybrid_coding_eval/benchmarks/real_dev/fixtures/<slug>/``. We
    mirror it under ``dst`` so the agent edits in isolation.
    """
    slug = getattr(task, "fixtures_dir", None) or getattr(task, "fixture_dir", None)
    if not slug:
        # Adapters that ship a Path object (exercism-style) instead of a slug.
        fixture_dir = getattr(task, "fixture_dir", None)
        if isinstance(fixture_dir, Path) and fixture_dir.is_dir():
            slug_path = fixture_dir
        else:
            raise FileNotFoundError(f"task {task.id} has no fixtures_dir")
    else:
        slug_path = _REAL_DEV_FIXTURES_ROOT / str(slug)
    if not slug_path.is_dir():
        raise FileNotFoundError(f"fixture {slug_path} not found")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(slug_path, dst)
    return dst


def _score_via_pytest(scratch: Path) -> Quality:
    """Run pytest in the scratch dir.

    pytest exit codes:
      0 — all tests passed
      1 — some tests failed
      2 — interrupted
      3 — internal error
      4 — usage error
      5 — no tests collected

    For D1/D5 tasks scratch holds stub + test files → exit 0/1 are meaningful.
    For D2 (issue patches), D3 (refactor prose), D4 (review prose) — no
    pytest tests exist, so exit 5 ("no tests collected") returns Quality()
    with functional_pass=None (not measured).
    """
    # Detect whether any pytest tests exist before invoking.
    has_tests = any(
        p.name.startswith("test_") or p.name.endswith("_test.py")
        for p in scratch.rglob("*.py")
    )
    if not has_tests:
        # No functional scorer applicable.
        return Quality()

    py = shutil.which("python3") or shutil.which("python") or "python3"
    try:
        proc = subprocess.run(
            [py, "-m", "pytest", "-q"],
            cwd=scratch,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if proc.returncode == 5:
            return Quality()
        passed = proc.returncode == 0
        return Quality(
            functional_pass=passed,
            tests_passed=1 if passed else 0,
            tests_total=1,
            composite=1.0 if passed else 0.0,
        )
    except subprocess.TimeoutExpired:
        return Quality(functional_pass=False, composite=0.0)


def run(
    task: Any,
    *,
    proxy_url: str = "http://127.0.0.1:8787",
    hardware_profile_ref: str = "",
    output_dir: Path | None = None,
    router_strategy: str = "heuristic",
    timeout_s: int = DEFAULT_TIMEOUT_S,
    **_unused: Any,
) -> ResultRow:
    """Run one real-dev D1/D5 task through opencode."""
    if output_dir is None:
        output_dir = _REPO_ROOT / "results" / "r8"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = _task_slug(task.id)
    run_dir = output_dir / f"r8_{slug}_{router_strategy}"
    scratch = run_dir / "scratch"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Copy fixture
    try:
        _copy_fixture(task, scratch)
    except Exception as exc:
        return ResultRow(
            task_id=task.id,
            category=getattr(task, "category", "D"),
            route=ROUTE,
            hardware_profile_ref=hardware_profile_ref,
            tokens=TokenUsage(),
            latency=Latency(wall_ms=0, per_call_ms=[]),
            quality=Quality(),
            routing=Routing(total_calls=0, local_calls=0, cloud_calls=0),
            output_ref="",
            error=f"fixture_copy_failed: {exc}",
            router_strategy=router_strategy,
        )

    prompt = getattr(task, "prompt", None) or getattr(task, "instruction", "")
    if not prompt:
        prompt = f"Complete the task in the README.md of {scratch.name}."

    model_id = f"hybrid-router/router/{router_strategy}"

    # opencode CLI shape: `opencode run [message..]` — message is positional,
    # `--cwd` is not a flag; run with cwd=scratch.
    cmd = [
        "opencode",
        "run",
        "-m",
        model_id,
        "--format",
        "json",
        "--log-level",
        "WARN",
        prompt,
    ]

    env = os.environ.copy()
    env["OPENAI_API_KEY"] = env.get("OPENAI_API_KEY", "bench-eval-key")

    started_at = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    err: str | None = None
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(scratch),
            timeout=timeout_s,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        (run_dir / "stdout.log").write_text(proc.stdout or "", encoding="utf-8")
        (run_dir / "stderr.log").write_text(proc.stderr or "", encoding="utf-8")
        if proc.returncode != 0:
            err = f"opencode_exit_{proc.returncode}"
    except subprocess.TimeoutExpired:
        err = f"agent_timeout_{timeout_s}s"
    except FileNotFoundError:
        err = "opencode_not_installed"

    wall_ms = int((time.perf_counter() - t0) * 1000)
    finished_at = datetime.now(timezone.utc)

    # Score
    quality = _score_via_pytest(scratch)

    answer_path = run_dir / "answer.txt"
    # The "output" of an agentic run is the modified scratch dir; we
    # snapshot a recursive listing for traceability.
    snapshot_lines: list[str] = []
    for p in sorted(scratch.rglob("*")):
        if p.is_file() and p.stat().st_size < 100_000:
            try:
                snapshot_lines.append(f"### {p.relative_to(scratch)}\n")
                snapshot_lines.append(p.read_text(encoding="utf-8"))
                snapshot_lines.append("\n")
            except (UnicodeDecodeError, OSError):
                continue
    answer_path.write_text("".join(snapshot_lines), encoding="utf-8")

    tokens, routing = _attribute_from_decisions_log(
        started_at, finished_at, router_strategy
    )

    try:
        output_ref = str(answer_path.resolve().relative_to(_REPO_ROOT))
    except ValueError:
        output_ref = str(answer_path.resolve())

    return ResultRow(
        task_id=task.id,
        category=getattr(task, "category", "D"),
        route=ROUTE,
        hardware_profile_ref=hardware_profile_ref,
        tokens=tokens,
        latency=Latency(wall_ms=wall_ms, per_call_ms=[wall_ms]),
        quality=quality,
        routing=routing,
        output_ref=output_ref,
        started_at=started_at.isoformat(),
        finished_at=finished_at.isoformat(),
        error=err,
        router_strategy=router_strategy,
    )
