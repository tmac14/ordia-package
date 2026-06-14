"""Integration test for examples/plugin-validator."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]
PLUGIN_DIR = REPO_ROOT / "examples" / "plugin-validator"


class PluginExampleTests(unittest.TestCase):
    def test_plugin_validator_warns_on_profile_mismatch(self) -> None:
        if not PLUGIN_DIR.is_dir():
            self.skipTest("plugin-validator example missing")
        install = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-e", str(PLUGIN_DIR)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(install.returncode, 0, install.stderr or install.stdout)

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [*CLI_CMD, "init", "--directory", str(target), "--profile", "plugin-demo"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            profile = target / "docs" / "control" / "PROFILE.md"
            profile.write_text("# Profile\n\nNo mention of expected id.\n", encoding="utf-8")

            validate = subprocess.run(
                [*CLI_CMD, "validate", "--project", "--directory", str(target)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr or validate.stdout)
            combined = (validate.stdout + validate.stderr).lower()
            self.assertIn("warning", combined)
            self.assertIn("plugin-demo", combined)


if __name__ == "__main__":
    unittest.main()
