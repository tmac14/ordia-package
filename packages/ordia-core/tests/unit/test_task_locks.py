"""Tests for task lock CLI."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia.tasks.locks import add_lock, list_locks, release_lock


class TaskLockTests(unittest.TestCase):
    def _scaffold(self, root: Path) -> None:
        (root / "docs" / "control").mkdir(parents=True)
        (root / "ordia.yaml").write_text(
            """
version: "0.3"
profile: lock-test
control:
  root: docs/control
  taskRegistry: TASK_REGISTRY.yaml
""".strip(),
            encoding="utf-8",
        )
        (root / "docs" / "control" / "TASK_REGISTRY.yaml").write_text(
            """
schema_version: 1
updated_at: "2026-06-14"
queues:
  in_flight: [T1]
  ready_for_parallel: []
  planning_pending: []
  locks_pending: []
  model_tier_pending: []
  waiting_for_user_decision: []
  waiting_for_agent_report: []
  validation_pending: []
tasks:
  - id: T1
    status: IN_FLIGHT
    owner: agent-backend
    runtime: ONLY_CURSOR
    protocol: IMPLEMENTATION
locks: []
""".strip(),
            encoding="utf-8",
        )

    def test_add_list_release_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._scaffold(root)
            added = add_lock(root, task_id="T1", path="src/api/", reason="parallel")
            self.assertTrue(added.ok)
            listed = list_locks(root)
            self.assertEqual(len(listed.locks), 1)
            released = release_lock(root, task_id="T1", path="src/api/")
            self.assertTrue(released.ok)
            listed2 = list_locks(root)
            self.assertEqual(listed2.locks, [])


if __name__ == "__main__":
    unittest.main()
