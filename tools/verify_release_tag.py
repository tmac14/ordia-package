#!/usr/bin/env python3
"""Verify git release tag matches ordia-core package version."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "packages" / "ordia-core" / "pyproject.toml"
TAG_RE = re.compile(r"^ordia-core-v(.+)$")


def _read_package_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise ValueError(f"invalid version in {PYPROJECT.relative_to(ROOT)}")
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ordia-core release tag matches pyproject version")
    parser.add_argument("--check", action="store_true", help="Verify tag from GITHUB_REF_NAME (CI default)")
    parser.add_argument("--tag", help="Release tag (default: GITHUB_REF_NAME env)")
    args = parser.parse_args()

    tag = args.tag or os.environ.get("GITHUB_REF_NAME", "").strip()
    if not tag:
        print("ERROR: no tag provided (use --tag or set GITHUB_REF_NAME)", file=sys.stderr)
        return 1

    match = TAG_RE.match(tag)
    if not match:
        print(f"ERROR: tag must match ordia-core-v{{version}}, got: {tag}", file=sys.stderr)
        return 1

    tag_version = match.group(1)
    if not PYPROJECT.is_file():
        print(f"ERROR: pyproject missing: {PYPROJECT}", file=sys.stderr)
        return 1

    try:
        package_version = _read_package_version()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Release tag verification")
    print(f"- tag: {tag}")
    print(f"- tag version: {tag_version}")
    print(f"- package version: {package_version}")

    if tag_version != package_version:
        print(
            f"ERROR: tag version {tag_version!r} != package version {package_version!r}",
            file=sys.stderr,
        )
        return 1

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
