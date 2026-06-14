#!/usr/bin/env python3
"""Run the full Ordia test suite (ordia-package CI equivalent)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUITES = (
    "test_ordia_cli.py",
    "test_ordia_validator.py",
    "test_ordia_bundle_drift.py",
    "test_ordia_greenfield.py",
    "test_ordia_wheel.py",
    "test_ordia_commands.py",
    "test_ordia_command_coverage.py",
    "test_ordia_model_routing.py",
    "test_ordia_workflows.py",
    "test_ordia_package_boundary.py",
)

CATALOG_SUITES = (
    "test_ordia_config.py",
    "test_ordia_manifest.py",
    "test_ordia_doc_links.py",
    "test_ordia_slice4_coverage.py",
    "test_ordia_docs_inventory.py",
    "test_ordia_docs_slice8.py",
)


def main() -> int:
    failed = 0
    catalog_mode = (ROOT / "ordia.yaml").is_file() and (ROOT / "AGENTS.md").is_file()
    suites = list(SUITES) + (list(CATALOG_SUITES) if catalog_mode else [])
    for suite in suites:
        path = ROOT / "scripts" / suite
        if not path.is_file():
            print(f"SKIP missing {suite}")
            continue
        print(f"=== {suite} ===")
        proc = subprocess.run([sys.executable, str(path)], cwd=ROOT)
        if proc.returncode != 0:
            failed += 1
    if failed:
        print(f"FAILED: {failed} suite(s)")
        return 1
    print("OK: all Ordia suites passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
