"""Unit tests for atomic task transitions."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia.config import load_ordia_config
from ordia.tasks.transition import TransitionRequest, apply_transition, plan_transition


class TaskTransitionTests(unittest.TestCase):
    def _scaffold(self, root: Path) -> None:
        control = root / "docs" / "control"
        (control / "tasks").mkdir(parents=True)
        (root / "ordia.yaml").write_text(
            """
version: "0.3"
profile: transition-test
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
schema_version: 1
updated_at: "2026-06-01"
queues:
  in_flight: [TASK-200]
  ready_for_parallel: []
  model_tier_pending: []
  waiting_for_user_decision: []
  waiting_for_agent_report: []
  validation_pending: []
tasks:
  - id: TASK-200
    status: IN_FLIGHT
    owner: orchestrator
    runtime: ONLY_CURSOR
    protocol: IMPLEMENTATION
locks: []
""".strip(),
            encoding="utf-8",
        )
        (control / "ORCHESTRATION_STATE.md").write_text(
            """
**Last updated:** 2026-06-01

## 0. Active Execution Control
- Active task ID: `TASK-200`
- Next safe action: continue work

## 1. In-flight summary
- Tasks in `queues.in_flight`: TASK-200

## 2. Waiting (user / agent)
- `waiting_for_user_decision`: none
- `waiting_for_agent_report`: none
- `model_tier_pending`: none

## 3. Pending evidence
- `validation_pending`: none
""".strip(),
            encoding="utf-8",
        )

    def test_transition_to_validation_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._scaffold(root)
            request = TransitionRequest(
                task_id="TASK-200",
                status="VALIDATION_PENDING",
                next_safe_action="run ordia validate --project",
            )
            result = apply_transition(root, request)
            self.assertTrue(result.ok, result.errors)
            cfg = load_ordia_config(root)
            assert cfg is not None
            registry_text = cfg.task_registry_path.read_text(encoding="utf-8")
            state_text = cfg.state_path.read_text(encoding="utf-8")
            self.assertIn("VALIDATION_PENDING", registry_text)
            self.assertIn("validation_pending:", registry_text)
            self.assertIn("TASK-200", state_text)
            self.assertIn("2026-06-14", state_text)

    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._scaffold(root)
            cfg = load_ordia_config(root)
            assert cfg is not None
            before = cfg.task_registry_path.read_text(encoding="utf-8")
            result = apply_transition(
                root,
                TransitionRequest(task_id="TASK-200", status="IMPLEMENTED"),
                dry_run=True,
            )
            self.assertTrue(result.ok, result.errors)
            after = cfg.task_registry_path.read_text(encoding="utf-8")
            self.assertEqual(before, after)

    def test_unknown_task_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._scaffold(root)
            plan = plan_transition(root, TransitionRequest(task_id="TASK-999", status="CLOSED"))
            self.assertFalse(plan.ok)
            self.assertTrue(any("Unknown task" in err for err in plan.errors))


if __name__ == "__main__":
    unittest.main()
