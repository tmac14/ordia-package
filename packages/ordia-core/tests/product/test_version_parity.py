"""Product test for version parity tool."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
TOOL = REPO_ROOT / "tools" / "verify_version_parity.py"

pytestmark = pytest.mark.product


def test_version_parity_check_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "RESULT: PASS" in proc.stdout
