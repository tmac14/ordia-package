"""Tests for agent registry schema and parallel validation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia.validator.agent_registry_schema import validate_agent_registry_schema
from ordia.validator.common import Validation
from ordia.validator.parallel import paths_overlap
from ordia.validator.project import validate_agents, validate_tasks


class ParallelPathTests(unittest.TestCase):
    def test_paths_overlap_prefix(self) -> None:
        self.assertTrue(paths_overlap("src/api/", "src/api/foo.ts"))
        self.assertFalse(paths_overlap("src/api/", "src/web/foo.ts"))


class AgentRegistryValidationTests(unittest.TestCase):
    def test_owner_must_be_registered_when_agents_defined(self) -> None:
        registry = {
            "queues": {
                "in_flight": ["T1"],
                "ready_for_parallel": [],
                "planning_pending": [],
                "locks_pending": [],
                "model_tier_pending": [],
                "waiting_for_user_decision": [],
                "waiting_for_agent_report": [],
                "validation_pending": [],
            },
            "tasks": [
                {
                    "id": "T1",
                    "status": "IN_FLIGHT",
                    "owner": "unknown-agent",
                    "runtime": "ONLY_CURSOR",
                    "protocol": "IMPLEMENTATION",
                    "task_packet": "docs/control/tasks/T1.md",
                    "planned_write_paths": ["src/a.ts"],
                }
            ],
        }
        agent_registry = {
            "agents": [
                {
                    "id": "agent-backend",
                    "role": "backend",
                    "scopes": ["src/"],
                }
            ]
        }
        result = Validation()
        agent_by_id = validate_agents(registry, agent_registry, result)
        valid_owners = set(agent_by_id) | {"Cursor Control Plane"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/control/tasks").mkdir(parents=True)
            (root / "docs/control/tasks/T1.md").write_text("# T1\n", encoding="utf-8")
            validate_tasks(
                registry,
                set(),
                root,
                result,
                valid_owners=valid_owners,
                agent_by_id=agent_by_id,
            )
        self.assertTrue(any("unknown-agent" in err for err in result.errors))

    def test_mutual_exclusion_overlap(self) -> None:
        registry = {
            "queues": {
                "in_flight": ["T1", "T2"],
                "ready_for_parallel": [],
                "planning_pending": [],
                "locks_pending": [],
                "model_tier_pending": [],
                "waiting_for_user_decision": [],
                "waiting_for_agent_report": [],
                "validation_pending": [],
            },
            "tasks": [
                {
                    "id": "T1",
                    "status": "IN_FLIGHT",
                    "owner": "agent-data",
                    "runtime": "ONLY_CURSOR",
                    "protocol": "IMPLEMENTATION",
                    "task_packet": "docs/control/tasks/T1.md",
                    "planned_write_paths": ["db/schema.sql"],
                },
                {
                    "id": "T2",
                    "status": "IN_FLIGHT",
                    "owner": "agent-infra",
                    "runtime": "ONLY_CURSOR",
                    "protocol": "IMPLEMENTATION",
                    "task_packet": "docs/control/tasks/T2.md",
                    "planned_write_paths": ["db/"],
                },
            ],
        }
        agent_registry = {
            "agents": [
                {"id": "agent-data", "role": "data", "excludes": "infra-data"},
                {"id": "agent-infra", "role": "infra", "excludes": "infra-data"},
            ]
        }
        result = Validation()
        agent_by_id = validate_agents(registry, agent_registry, result)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/control/tasks").mkdir(parents=True)
            (root / "docs/control/tasks/T1.md").write_text("# T1\n", encoding="utf-8")
            (root / "docs/control/tasks/T2.md").write_text("# T2\n", encoding="utf-8")
            validate_tasks(
                registry,
                set(),
                root,
                result,
                valid_owners=set(agent_by_id),
                agent_by_id=agent_by_id,
            )
        self.assertTrue(any("Mutual exclusion" in err for err in result.errors))

    def test_agent_registry_schema_valid(self) -> None:
        result = Validation()
        validate_agent_registry_schema(
            {
                "schema_version": 1,
                "updated_at": "2026-06-14",
                "agents": [{"id": "agent-backend", "role": "API"}],
            },
            result,
        )
        self.assertEqual(result.errors, [])


if __name__ == "__main__":
    unittest.main()
