#!/usr/bin/env python3
"""Verify ordia-core and ordia-cursor package versions match."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
CORE_PYPROJECT = ROOT / "packages" / "ordia-core" / "pyproject.toml"
CURSOR_PACKAGE = ROOT / "packages" / "ordia-cursor" / "package.json"


def _read_core_version() -> str:
    data = tomllib.loads(CORE_PYPROJECT.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("invalid ordia-core version")
    return version


def _read_cursor_version() -> str:
    data = json.loads(CURSOR_PACKAGE.read_text(encoding="utf-8"))
    version = data.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("invalid ordia-cursor version")
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ordia-core and ordia-cursor versions match")
    parser.add_argument("--check", action="store_true", help="Exit non-zero on version drift")
    args = parser.parse_args()

    core_version = _read_core_version()
    cursor_version = _read_cursor_version()
    print("Version parity check")
    print(f"- ordia-core: {core_version}")
    print(f"- ordia-cursor: {cursor_version}")

    if core_version != cursor_version:
        print(
            f"ERROR: version drift {core_version!r} != {cursor_version!r}",
            file=sys.stderr,
        )
        return 1

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
