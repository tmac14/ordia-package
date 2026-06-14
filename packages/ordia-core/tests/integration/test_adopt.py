"""Tests for ordia adopt brownfield pipeline."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]


class AdoptCliTests(unittest.TestCase):
    def test_adopt_on_empty_repo_scaffolds_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "README.md").write_text("# Demo\n", encoding="utf-8")
            proc = subprocess.run(
                [*CLI_CMD, "adopt", "--directory", str(target), "--profile", "adopt-test"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            self.assertTrue((target / "ordia.yaml").is_file())
            self.assertTrue((target / "docs" / "control" / "ADOPTION_REPORT.md").is_file())
            self.assertTrue((target / "docs" / "control" / "NAVIGATION.md").is_file())


if __name__ == "__main__":
    unittest.main()
