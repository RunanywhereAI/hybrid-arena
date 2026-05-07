"""Compat shim — real code lives at :mod:`hybrid_coding_eval.benchmarks`.

Redirects ``from benchmark.X.adapter import Y`` to
``hybrid_coding_eval.benchmarks.X.adapter`` by aliasing each
subpackage in :data:`sys.modules`. Removed at T-06.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Import the real package and alias it under the legacy name. After this
# both ``benchmark`` and ``hybrid_coding_eval.benchmarks`` point at the
# exact same module object — ``from benchmark.humaneval_plus import X``
# resolves through the new tree.
import hybrid_coding_eval.benchmarks as _new  # noqa: E402

# Splice: inject the new package's public attributes onto this module,
# then alias child submodules. Doing both makes ``from benchmark import
# humaneval_plus`` work alongside ``import benchmark.humaneval_plus``.
globals().update({k: v for k, v in _new.__dict__.items() if not k.startswith("_")})
for _sub in ("humaneval_plus", "swebench_verified", "bigcodebench_hard", "custom_arch"):
    _mod = __import__(f"hybrid_coding_eval.benchmarks.{_sub}", fromlist=[_sub])
    sys.modules[f"benchmark.{_sub}"] = _mod
    # Eagerly load the adapter submodule too, since every call site is
    # ``from benchmark.<src>.adapter import ...``.
    _adapter = __import__(
        f"hybrid_coding_eval.benchmarks.{_sub}.adapter", fromlist=["adapter"]
    )
    sys.modules[f"benchmark.{_sub}.adapter"] = _adapter
