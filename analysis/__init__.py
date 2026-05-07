"""Compat shim — real code lives at :mod:`hybrid_coding_eval.analysis`."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import hybrid_coding_eval.analysis as _new  # noqa: E402

globals().update({k: v for k, v in _new.__dict__.items() if not k.startswith("_")})
for _sub in ("aggregate", "all", "arqgc", "cost_scenarios", "decision_matrix"):
    _mod = __import__(f"hybrid_coding_eval.analysis.{_sub}", fromlist=[_sub])
    sys.modules[f"analysis.{_sub}"] = _mod
