"""Tests for command catalog layer classification."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ordia.commands.catalog import classify_script, seed_catalog_from_package


class CatalogLayerTests(unittest.TestCase):
    def test_classify_script_domains(self) -> None:
        self.assertEqual(classify_script("dev:web")[2], "dev")
        self.assertEqual(classify_script("tunnel:start")[2], "tunnel")
        self.assertEqual(classify_script("ordia:validate")[0], "ordia")
        self.assertEqual(classify_script("quality:lint")[1], "L2")

    def test_seed_catalog_groups_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "package.json"
            pkg.write_text(
                json.dumps(
                    {
                        "scripts": {
                            "dev:web": "vite",
                            "db:migrate": "migrate",
                            "tunnel:start": "tunnel",
                        }
                    }
                ),
                encoding="utf-8",
            )
            catalog_path = root / "commands.catalog.json"
            count = seed_catalog_from_package(root, catalog_path, pkg)
            self.assertEqual(count, 3)
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            section_ids = {section["id"] for section in catalog["sections"]}
            self.assertIn("dev", section_ids)
            self.assertIn("db", section_ids)
            self.assertIn("tunnel", section_ids)
            self.assertTrue(catalog.get("workflowIntents"))


if __name__ == "__main__":
    unittest.main()
