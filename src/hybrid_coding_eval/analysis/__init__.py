"""Post-experiment analysis pipeline.

The ``analysis`` package turns raw ``results/*/raw.jsonl`` sweeps into the
three offline artefacts the report needs:

  * :mod:`analysis.cost_scenarios` — re-price every row under N named
    pricing scenarios (same ``pricing_tables.json`` as the proxy).
  * :mod:`analysis.aggregate` — per-(category, route) medians, totals,
    success rates, plus headline tiles.
  * :mod:`analysis.arqgc` — Bounded area-under quality-cost curve, the
    IPRBench-style aggregate score.
  * :mod:`analysis.decision_matrix` — category × route recommendation
    grid rendered as Markdown.
  * :mod:`analysis.all` — convenience CLI that wires the four together.

Nothing in this package mutates ``raw.jsonl``. Every output is derived
(JSON / Markdown / PNG) and safe to regenerate.
"""
