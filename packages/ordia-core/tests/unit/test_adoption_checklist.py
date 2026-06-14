"""Tests for adoption checklist and doctor helpers."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from ordia.adoption.checklist import (
    adoption_report_stale,
    inventory_yaml_missing_paths,
    pending_adoption_steps,
)


class AdoptionChecklistTests(unittest.TestCase):
    def test_stale_report_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "control"
            control.mkdir(parents=True)
            old = (date.today() - timedelta(days=45)).isoformat()
            (control / "ADOPTION_REPORT.md").write_text(
                f"# Report\n\n**Generated:** {old}\n",
                encoding="utf-8",
            )
            message = adoption_report_stale(root, control, max_days=30)
            self.assertIsNotNone(message)
            self.assertIn("45", message or "")

    def test_pending_steps_from_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            control = Path(tmp) / "docs" / "control"
            control.mkdir(parents=True)
            (control / "adoption.checklist.yaml").write_text(
                "steps:\n  - id: a\n    title: Audit\n    status: pending\n",
                encoding="utf-8",
            )
            pending = pending_adoption_steps(control)
            self.assertEqual(pending, ["Audit"])

    def test_inventory_yaml_missing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inv = root / "docs" / "control" / "DOCUMENTATION_INVENTORY.yaml"
            inv.parent.mkdir(parents=True)
            inv.write_text(
                "coordination:\n  - docs/control/MISSING.md\n",
                encoding="utf-8",
            )
            missing = inventory_yaml_missing_paths(root, inv)
            self.assertIn("docs/control/MISSING.md", missing)


if __name__ == "__main__":
    unittest.main()
