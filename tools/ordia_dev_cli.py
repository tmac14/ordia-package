#!/usr/bin/env python3
"""Shim entrypoint for Ordia CLI (packages/ordia-core)."""

from __future__ import annotations

import sys
from pathlib import Path

core = Path(__file__).resolve().parents[1] / "packages" / "ordia-core"
sys.path.insert(0, str(core))

from ordia.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
