"""Additional coverage for adoption and lock helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia.adoption.audit import format_adoption_report, format_inventory_markdown, run_docs_audit
from ordia.commands.catalog import classify_script, validate_catalog_sync
from ordia.tasks.locks import add_lock, release_lock


class AdoptionFormatTests(unittest.TestCase):
    def test_format_report_and_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# X\n", encoding="utf-8")
            result = run_docs_audit(root)
            report = format_adoption_report(result)
            inventory = format_inventory_markdown(result)
            self.assertIn("Ordia Adoption Report", report)
            self.assertIn("ordia.yaml", report)
            self.assertIn("Documentation inventory", inventory)


class CatalogClassifyTests(unittest.TestCase):
    def test_classify_root_and_quality(self) -> None:
        self.assertEqual(classify_script("quality:lint")[1], "L2")
        self.assertEqual(classify_script("plain")[2], "other")


class TaskLockErrorTests(unittest.TestCase):
    def test_add_lock_unknown_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "control").mkdir(parents=True)
            (root / "ordia.yaml").write_text(
                'version: "0.3"\nprofile: t\ncontrol:\n  root: docs/control\n  taskRegistry: TASK_REGISTRY.yaml\n',
                encoding="utf-8",
            )
            (root / "docs" / "control" / "TASK_REGISTRY.yaml").write_text(
                "schema_version: 1\nupdated_at: '2026-06-14'\nqueues:\n  in_flight: []\n  ready_for_parallel: []\n  planning_pending: []\n  locks_pending: []\n  model_tier_pending: []\n  waiting_for_user_decision: []\n  waiting_for_agent_report: []\n  validation_pending: []\ntasks: []\nlocks: []\n",
                encoding="utf-8",
            )
            result = add_lock(root, task_id="MISSING", path="src/")
            self.assertFalse(result.ok)
            result2 = release_lock(root, task_id="T1", path="src/")
            self.assertFalse(result2.ok)


class CatalogSyncTests(unittest.TestCase):
    def test_validate_catalog_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            errors, count = validate_catalog_sync(root, root / "missing.json", root / "missing-package.json")
            self.assertGreater(len(errors), 0)
            self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
