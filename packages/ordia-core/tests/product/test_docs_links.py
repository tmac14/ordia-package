"""Product audit: docs link integrity."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
AUDIT = REPO_ROOT / "tools" / "audits" / "docs_links.py"


@pytest.mark.product
def test_docs_links_strict() -> None:
    if not AUDIT.is_file():
        pytest.skip(f"audit script not found: {AUDIT}")
    proc = subprocess.run(
        [sys.executable, str(AUDIT), "--strict"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
