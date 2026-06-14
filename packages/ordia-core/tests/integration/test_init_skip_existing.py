"""Integration tests for init --skip-existing."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]

pytestmark = pytest.mark.integration


class InitSkipExistingTests(unittest.TestCase):
    def test_skip_existing_preserves_ordia_yaml_and_adds_missing_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            first = subprocess.run(
                [*CLI_CMD, "init", "--directory", str(target), "--profile", "first"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
            manifest = target / "ordia.yaml"
            original = manifest.read_text(encoding="utf-8")
            manifest.write_text(original + "\n# marker\n", encoding="utf-8")

            proto = target / "docs" / "control" / "protocols" / "TASK_EXECUTION.md"
            proto.unlink()

            second = subprocess.run(
                [
                    *CLI_CMD,
                    "init",
                    "--skip-existing",
                    "--directory",
                    str(target),
                    "--profile",
                    "second",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            self.assertIn("# marker", manifest.read_text(encoding="utf-8"))
            self.assertTrue(proto.is_file())
