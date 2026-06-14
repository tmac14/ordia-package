"""Unit tests for TASK_REGISTRY JSON Schema validation."""

from __future__ import annotations

import unittest

from ordia.validator.common import Validation
from ordia.validator.task_registry_schema import validate_task_registry_schema


class TaskRegistrySchemaTests(unittest.TestCase):
    def test_valid_minimal_registry(self) -> None:
        registry = {
            "schema_version": 1,
            "updated_at": "2026-06-14",
            "queues": {
                "in_flight": [],
                "ready_for_parallel": [],
                "planning_pending": [],
                "locks_pending": [],
                "model_tier_pending": [],
                "waiting_for_user_decision": [],
                "waiting_for_agent_report": [],
                "validation_pending": [],
            },
            "tasks": [],
        }
        result = Validation()
        validate_task_registry_schema(registry, result)
        self.assertEqual(result.errors, [])

    def test_missing_schema_version_errors(self) -> None:
        registry = {
            "updated_at": "2026-06-14",
            "queues": {
                "in_flight": [],
                "ready_for_parallel": [],
                "planning_pending": [],
                "locks_pending": [],
                "model_tier_pending": [],
                "waiting_for_user_decision": [],
                "waiting_for_agent_report": [],
                "validation_pending": [],
            },
            "tasks": [],
        }
        result = Validation()
        validate_task_registry_schema(registry, result)
        self.assertTrue(any("schema_version" in err for err in result.errors))


if __name__ == "__main__":
    unittest.main()
