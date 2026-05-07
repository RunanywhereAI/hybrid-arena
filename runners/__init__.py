"""Compat shim — real code lives at :mod:`hybrid_coding_eval.runners`."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import hybrid_coding_eval.runners as _new  # noqa: E402

globals().update({k: v for k, v in _new.__dict__.items() if not k.startswith("_")})
for _sub in ("_shared", "r1_cloud_only", "r2_local_only",
             "r3_hybrid_architect", "r4_minion"):
    _mod = __import__(f"hybrid_coding_eval.runners.{_sub}", fromlist=[_sub])
    sys.modules[f"runners.{_sub}"] = _mod
