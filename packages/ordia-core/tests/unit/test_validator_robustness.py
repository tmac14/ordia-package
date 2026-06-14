"""Validator staleness and in-flight limbo checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia.validator.common import Validation
from ordia.validator.project import validate_registry_state_staleness, validate_tasks


class ValidatorRobustnessTests(unittest.TestCase):
    def test_staleness_warns_on_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "ORCHESTRATION_STATE.md"
            state.write_text("**Last updated:** 2026-06-01\n", encoding="utf-8")
            registry = {"updated_at": "2026-06-14", "queues": {}, "tasks": []}
            result = Validation()
            validate_registry_state_staleness(registry, state, result)
            self.assertTrue(any("staleness" in warn for warn in result.warnings))

    def test_implemented_limbo_warns(self) -> None:
        registry = {
            "tasks": [
                {
                    "id": "TASK-LIMBO",
                    "status": "IMPLEMENTED",
                    "owner": "agent-1",
                    "runtime": "ONLY_CURSOR",
                    "protocol": "IMPLEMENTATION",
                    "task_packet": "src/**",
                }
            ],
            "queues": {
                "in_flight": ["TASK-LIMBO"],
                "ready_for_parallel": [],
                "model_tier_pending": [],
                "waiting_for_user_decision": [],
                "waiting_for_agent_report": [],
                "validation_pending": [],
            },
        }
        result = Validation()
        validate_tasks(registry, set(), Path("/tmp/unused"), result)
        self.assertTrue(
            any("IMPLEMENTED in in_flight without validation_pending" in warn for warn in result.warnings)
        )


if __name__ == "__main__":
    unittest.main()
