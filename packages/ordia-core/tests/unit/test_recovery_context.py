"""Unit tests for recovery_context in-flight summary."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CORE_ROOT))
HOOKS_DIR = CORE_ROOT / "ordia" / "cursor_bundle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from lib.control_context import load_in_flight_entries, parallel_edit_blocked, recovery_context  # noqa: E402

ORDIA_YAML = """
version: "0.3"
profile: test
control:
  root: docs/control
  state: ORCHESTRATION_STATE.md
  taskRegistry: TASK_REGISTRY.yaml
enforcement:
  productRoots: [src/]
closure:
  validator: ordia validate --project
""".strip()


class RecoveryContextTests(unittest.TestCase):
    def test_load_in_flight_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "control"
            control.mkdir(parents=True)
            (root / "ordia.yaml").write_text(ORDIA_YAML, encoding="utf-8")
            (control / "TASK_REGISTRY.yaml").write_text(
                """
queues:
  in_flight: [TASK-001]
tasks:
  - id: TASK-001
    status: IN_FLIGHT
""".strip(),
                encoding="utf-8",
            )
            (control / "ORCHESTRATION_STATE.md").write_text(
                "- Active task ID: `TASK-001`\n- control_plane_runtime: `ONLY_CURSOR`\n"
                "- active_protocol: `IMPLEMENTATION`\n- session_mode: `MULTI_CHAT`\n"
                "- Recovery status: `RECOVERY_READY`\n",
                encoding="utf-8",
            )
            rows = load_in_flight_entries(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["id"], "TASK-001")
            self.assertEqual(rows[0]["status"], "IN_FLIGHT")
            context = recovery_context(root)
            self.assertIn("queues.in_flight: TASK-001 (IN_FLIGHT, owner=-)", context)

    def test_parallel_edit_blocked_foreign_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "control"
            control.mkdir(parents=True)
            (root / "ordia.yaml").write_text(ORDIA_YAML, encoding="utf-8")
            (control / "TASK_REGISTRY.yaml").write_text(
                """
queues:
  in_flight: [TASK-001, TASK-002]
active_locks:
  - path: src/api/
    task_id: TASK-002
tasks:
  - id: TASK-001
    status: IN_FLIGHT
    planned_write_paths: [src/ui/]
  - id: TASK-002
    status: IN_FLIGHT
""".strip(),
                encoding="utf-8",
            )
            session = {"runtime": "ONLY_CURSOR", "protocol": "IMPLEMENTATION", "task_id": "TASK-001"}
            blocked, reason = parallel_edit_blocked(session, "src/api/handler.py", root)
            self.assertTrue(blocked)
            self.assertIn("TASK-002", reason)


if __name__ == "__main__":
    unittest.main()
