#!/usr/bin/env python3
"""Verify docs/ordia product docs stay in sync with bundled ordia/product_docs/."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO_PRODUCT_DOCS = ROOT / "docs" / "ordia"
BUNDLED_PRODUCT_DOCS = ROOT / "packages" / "ordia-core" / "ordia" / "product_docs"

core = ROOT / "packages" / "ordia-core"
sys.path.insert(0, str(core))

from ordia.cli import PRODUCT_DOC_NAMES  # noqa: E402


def audit_sync() -> list[str]:
    errors: list[str] = []
    for name in PRODUCT_DOC_NAMES:
        repo_path = REPO_PRODUCT_DOCS / name
        bundled_path = BUNDLED_PRODUCT_DOCS / name
        if not repo_path.is_file():
            errors.append(f"missing repo product doc: {repo_path.relative_to(ROOT)}")
            continue
        if not bundled_path.is_file():
            errors.append(f"missing bundled product doc: {bundled_path.relative_to(ROOT)}")
            continue
        if repo_path.read_bytes() != bundled_path.read_bytes():
            errors.append(f"drift: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit repo vs bundled product docs")
    parser.add_argument("--check", action="store_true", help="Exit non-zero on drift or missing files")
    parser.add_argument("--sync", action="store_true", help="Copy docs/ordia portable subset into product_docs/")
    args = parser.parse_args()

    if args.sync:
        synced = 0
        for name in PRODUCT_DOC_NAMES:
            src = REPO_PRODUCT_DOCS / name
            dest = BUNDLED_PRODUCT_DOCS / name
            if not src.is_file():
                print(f"WARNING: missing source {src.relative_to(ROOT)}", file=sys.stderr)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            synced += 1
        print(f"Synced {synced} product doc(s) into {BUNDLED_PRODUCT_DOCS.relative_to(ROOT)}")
        return 0

    errors = audit_sync()
    print("Product docs sync audit")
    print(f"- tracked docs: {len(PRODUCT_DOC_NAMES)}")
    print(f"- issues: {len(errors)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1 if args.check else 0

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
