"""Tests for benchmark/custom_arch (Category C)."""

from __future__ import annotations

from hybrid_coding_eval.benchmarks.custom_arch import RUBRIC_DIMENSIONS, load_tasks

EXPECTED_KINDS = {
    "architecture-design",
    "migration-plan",
    "code-review",
    "tradeoff-explanation",
    "debug-reasoning",
}


def test_loads_exactly_five_tasks():
    """The category-C bucket is fixed at five hand-curated tasks."""
    tasks = load_tasks()
    assert len(tasks) == 5, f"expected 5 tasks, got {len(tasks)}"

    # Every task has a non-empty ID, category "C", and a substantive prompt.
    ids = [t.id for t in tasks]
    assert len(set(ids)) == 5, f"task IDs must be unique, got: {ids}"
    for t in tasks:
        assert t.id.startswith("custom-arch/"), t.id
        assert t.category == "C", (t.id, t.category)
        # Prompts must be real content, not placeholder.
        word_count = len(t.prompt.split())
        assert 100 <= word_count <= 400, (
            f"{t.id}: prompt must be 100-400 words, got {word_count}"
        )

    # All five 'kind' buckets must appear exactly once.
    kinds = {t.kind for t in tasks}
    assert kinds == EXPECTED_KINDS, (
        f"missing or extra kinds; got {kinds}, expected {EXPECTED_KINDS}"
    )


def test_every_task_has_complete_rubric():
    """Every task must carry the full 5-dimension rubric, each maxing at 5."""
    tasks = load_tasks()
    for t in tasks:
        assert set(t.rubric.keys()) == set(RUBRIC_DIMENSIONS), (
            f"{t.id}: rubric dims {set(t.rubric.keys())} != "
            f"{set(RUBRIC_DIMENSIONS)}"
        )
        for dim_name, dim in t.rubric.items():
            assert dim.max == 5, f"{t.id}.{dim_name}.max != 5"
            assert dim.description.strip(), (
                f"{t.id}.{dim_name}: empty description"
            )
            # Descriptions must be tuned per task, not placeholder.
            assert len(dim.description) >= 40, (
                f"{t.id}.{dim_name}: description too short "
                f"({len(dim.description)} chars) — rubric must be tuned per task"
            )
