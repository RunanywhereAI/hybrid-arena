"""Category C: hand-curated architecture/reasoning tasks."""

from .adapter import RUBRIC_DIMENSIONS, RubricDimension, Task, load_tasks

__all__ = ["Task", "RubricDimension", "RUBRIC_DIMENSIONS", "load_tasks"]
