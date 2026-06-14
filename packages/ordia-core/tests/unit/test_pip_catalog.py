"""Unit tests for seed_pip_catalog and control path helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ordia.commands.catalog import seed_pip_catalog_stub
from ordia.control.paths import control_root_from


class PipCatalogAndPathsTests(unittest.TestCase):
    def test_seed_pip_catalog_stub_writes_ordia_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = root / "docs" / "control" / "commands.catalog.json"
            count = seed_pip_catalog_stub(root, catalog_path, profile="test-profile")
            self.assertEqual(count, 11)
            data = json.loads(catalog_path.read_text(encoding="utf-8"))
            names = [cmd["name"] for section in data["sections"] for cmd in section["commands"]]
            self.assertIn("ordia:validate", names)
            self.assertIn("ordia:task-summary", names)
            self.assertIn("ordia:task-transition", names)

    def test_control_root_from_greenfield(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "control").mkdir(parents=True)
            self.assertEqual(control_root_from(root).name, "control")


if __name__ == "__main__":
    unittest.main()
