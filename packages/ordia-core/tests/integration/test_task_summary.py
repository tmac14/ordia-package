"""Integration tests for ordia task summary CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]

pytestmark = pytest.mark.integration


class TaskSummaryCliTests(unittest.TestCase):
    def test_task_summary_after_greenfield_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [*CLI_CMD, "init", "--directory", str(target), "--profile", "ts-test"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)

            summary = subprocess.run(
                [*CLI_CMD, "task", "summary", "--directory", str(target)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(summary.returncode, 0, summary.stderr or summary.stdout)
            self.assertIn("in_flight: (none)", summary.stdout)

            summary_json = subprocess.run(
                [*CLI_CMD, "task", "summary", "--json", "--directory", str(target)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(summary_json.returncode, 0, summary_json.stderr or summary_json.stdout)
            payload = json.loads(summary_json.stdout)
            self.assertTrue(payload.get("ok"))
            self.assertIn("summary", payload.get("metadata", {}))
