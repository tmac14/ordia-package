"""Integration tests for ordia cursor sync."""

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


class CursorSyncTests(unittest.TestCase):
    def test_cursor_sync_refreshes_bundle_without_touching_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [*CLI_CMD, "init", "--with-cursor", "--directory", str(target), "--profile", "cs-test"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            registry = target / "docs" / "control" / "TASK_REGISTRY.yaml"
            before = registry.read_text(encoding="utf-8")
            marker = target / ".cursor" / "hooks.json"
            self.assertTrue(marker.is_file())

            sync = subprocess.run(
                [*CLI_CMD, "cursor", "sync", "--directory", str(target)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(sync.returncode, 0, sync.stderr or sync.stdout)
            self.assertEqual(registry.read_text(encoding="utf-8"), before)
            self.assertTrue(marker.is_file())
