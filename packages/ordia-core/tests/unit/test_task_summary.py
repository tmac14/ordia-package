"""Unit tests for task summary builder."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia.config import load_ordia_config
from ordia.tasks.summary import build_task_summary, format_task_summary_text


class TaskSummaryTests(unittest.TestCase):
    def test_build_task_summary_in_flight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "control"
            (control / "tasks").mkdir(parents=True)
            (root / "ordia.yaml").write_text(
                """
version: "0.3"
profile: summary-test
control:
  root: docs/control
  state: ORCHESTRATION_STATE.md
  taskRegistry: TASK_REGISTRY.yaml
  taskPackets: tasks
enforcement:
  productRoots: [src/]
closure:
  validator: ordia validate --project
""".strip(),
                encoding="utf-8",
            )
            (control / "TASK_REGISTRY.yaml").write_text(
                """
updated_at: "2026-06-14"
queues:
  in_flight: [TASK-100]
tasks:
  - id: TASK-100
    status: IN_FLIGHT
    owner: orchestrator
    runtime: ONLY_CURSOR
    protocol: IMPLEMENTATION
    planned_write_paths: [src/app.ts]
locks: []
""".strip(),
                encoding="utf-8",
            )
            (control / "ORCHESTRATION_STATE.md").write_text(
                """
## 0. Active Execution Control
- Recovery status: `RECOVERY_READY`
- control_plane_runtime: `ONLY_CURSOR`
- active_protocol: `IMPLEMENTATION`
- session_mode: `MULTI_CHAT`
- handoff_from: `NONE`
- Active task ID: `TASK-100`
- Next safe action: continue implementation
""".strip(),
                encoding="utf-8",
            )
            (control / "tasks" / "TASK-100.md").write_text(
                "## Next Safe Action\n\nFinish src/app.ts and run validate.\n",
                encoding="utf-8",
            )
            cfg = load_ordia_config(root)
            assert cfg is not None
            summary = build_task_summary(root, cfg)
            self.assertEqual(summary["in_flight"][0]["id"], "TASK-100")
            self.assertEqual(summary["active_task"]["id"], "TASK-100")
            text = format_task_summary_text(summary)
            self.assertIn("TASK-100 (IN_FLIGHT)", text)
            self.assertIn("packet next_safe_action", text)


if __name__ == "__main__":
    unittest.main()
