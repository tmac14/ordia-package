"""Tests for validateOnControlCheck wiring."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ordia.config import load_ordia_config
from ordia.validator.project import validate_project


class ValidateOnControlCheckTests(unittest.TestCase):
    def test_catalog_drift_errors_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "control").mkdir(parents=True)
            (root / "ordia.yaml").write_text(
                """
version: "0.3"
profile: catalog-test
control:
  root: docs/control
  taskRegistry: TASK_REGISTRY.yaml
  agentRegistry: AGENT_REGISTRY.yaml
commands:
  catalog: commands.catalog.json
  npmPackage: package.json
  validateOnControlCheck: true
""".strip(),
                encoding="utf-8",
            )
            (root / "package.json").write_text(
                json.dumps({"scripts": {"dev:web": "vite", "missing-in-catalog": "true"}}),
                encoding="utf-8",
            )
            (root / "docs" / "control" / "commands.catalog.json").write_text(
                json.dumps(
                    {
                        "sections": [
                            {
                                "id": "dev",
                                "title": "Dev",
                                "commands": [{"name": "dev:web", "description": "web"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            for name in ("TASK_REGISTRY.yaml", "AGENT_REGISTRY.yaml"):
                (root / "docs" / "control" / name).write_text(
                    "schema_version: 1\nupdated_at: '2026-06-14'\nqueues:\n  in_flight: []\n  ready_for_parallel: []\n  planning_pending: []\n  locks_pending: []\n  model_tier_pending: []\n  waiting_for_user_decision: []\n  waiting_for_agent_report: []\n  validation_pending: []\ntasks: []\n"
                    if "TASK" in name
                    else "schema_version: 1\nupdated_at: '2026-06-14'\nagents: []\n",
                    encoding="utf-8",
                )
            (root / "docs" / "control" / "ORCHESTRATION_STATE.md").write_text(
                """**Last updated:** 2026-06-14

## 0. Active Execution Control

- Recovery status: `RECOVERY_READY`
- control_plane_runtime: `NONE_SELECTED_FOR_NEXT_TASK`
- active_protocol: `NONE_SELECTED_FOR_NEXT_TASK`
- session_mode: `MULTI_CHAT`
- handoff_from: `NONE`
- handoff_at: `NONE`
- handoff_reason: `NONE`
- Active task ID: `NONE`
""",
                encoding="utf-8",
            )
            (root / "docs" / "control" / "DECISION_LOG.md").write_text(
                "| ID | Decision |\n|----|----------|\n",
                encoding="utf-8",
            )
            (root / "docs" / "control" / "EVIDENCE_INDEX.md").write_text("# Evidence\n", encoding="utf-8")
            (root / "docs" / "control" / "PROFILE.md").write_text("# Profile\n", encoding="utf-8")
            cfg = load_ordia_config(root)
            assert cfg is not None
            result = validate_project(root, cfg)
            self.assertTrue(any("missing-in-catalog" in err for err in result.errors))


if __name__ == "__main__":
    unittest.main()
