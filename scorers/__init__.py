"""Compat shim — real code lives at :mod:`hybrid_coding_eval.scorers`."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import hybrid_coding_eval.scorers as _new  # noqa: E402

globals().update({k: v for k, v in _new.__dict__.items() if not k.startswith("_")})
for _sub in ("functional_python", "llm_judge", "swebench"):
    _mod = __import__(f"hybrid_coding_eval.scorers.{_sub}", fromlist=[_sub])
    sys.modules[f"scorers.{_sub}"] = _mod
