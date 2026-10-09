"""Machine and software metadata capture.

We record enough about the machine and library versions that a reader can
understand what the measured numbers mean and roughly reproduce them. Nothing
here is sensitive or network-bound; it is all local introspection.
"""

from __future__ import annotations

import datetime as _dt
import platform
import sys
from typing import Dict


def _lib_version(module_name: str) -> str:
    try:
        mod = __import__(module_name)
        return getattr(mod, "__version__", "unknown")
    except Exception:  # pragma: no cover - defensive
        return "not installed"


def collect_metadata() -> Dict[str, object]:
    """Collect a dictionary of machine and software metadata."""
    try:
        import os

        cpu_count = os.cpu_count()
    except Exception:  # pragma: no cover
        cpu_count = None

    return {
        "captured_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "machine": platform.machine(),
        "logical_cpus": cpu_count,
        "libraries": {
            "bcrypt": _lib_version("bcrypt"),
            "argon2_cffi": _lib_version("argon2"),
            "matplotlib": _lib_version("matplotlib"),
            "numpy": _lib_version("numpy"),
        },
        "note": (
            "All timings are single-process, single-worker, CPU-only. "
            "They reflect this machine and these library versions only."
        ),
    }
