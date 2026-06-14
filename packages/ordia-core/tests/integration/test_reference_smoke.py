"""End-to-end smoke tests for reference-monorepo example."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]
REFERENCE = REPO_ROOT / "examples" / "reference-monorepo"
HOOKS_LIB = REPO_ROOT / "packages" / "ordia-core" / "ordia" / "cursor_bundle" / "hooks"
sys.path.insert(0, str(HOOKS_LIB))
from lib.control_context import parallel_edit_blocked  # noqa: E402


class ReferenceMonorepoSmokeTests(unittest.TestCase):
    def test_reference_validate_passes(self) -> None:
        if not REFERENCE.is_dir():
            self.skipTest("reference-monorepo missing")
        proc = subprocess.run(
            [*CLI_CMD, "validate", "--project", "--directory", str(REFERENCE)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

    def test_foreign_lock_blocks_peer_edit(self) -> None:
        if not REFERENCE.is_dir():
            self.skipTest("reference-monorepo missing")
        session = {"runtime": "ONLY_CURSOR", "protocol": "IMPLEMENTATION", "task_id": "TASK-B"}
        blocked, reason = parallel_edit_blocked(session, "apps/api/main.py", REFERENCE)
        self.assertTrue(blocked)
        self.assertIn("TASK-A", reason)

    def test_docs_audit_on_reference(self) -> None:
        if not REFERENCE.is_dir():
            self.skipTest("reference-monorepo missing")
        proc = subprocess.run(
            [*CLI_CMD, "docs", "audit", "--directory", str(REFERENCE), "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)


if __name__ == "__main__":
    unittest.main()
