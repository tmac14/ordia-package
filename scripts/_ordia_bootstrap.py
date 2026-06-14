"""Bootstrap import path for ordia-core in ordia-package development."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_ordia_core() -> Path | None:
    root = Path(__file__).resolve().parents[1]
    core = root / "packages" / "ordia-core"
    if (core / "ordia" / "config.py").is_file():
        core_str = str(core)
        if core_str not in sys.path:
            sys.path.insert(0, core_str)
        return core
    try:
        import ordia  # noqa: F401

        return Path(ordia.__file__).resolve().parent.parent
    except ImportError:
        return None
