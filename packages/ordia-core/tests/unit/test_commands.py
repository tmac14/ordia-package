"""Tests for Ordia command catalog module and CLI help/commands."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ordia.commands.catalog import load_catalog, validate_catalog_sync
from ordia.commands.schema import validate_catalog_structure

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]
CATALOG = REPO_ROOT / "scripts" / "commands.catalog.json"
PACKAGE = REPO_ROOT / "package.json"


class OrdiaCommandsTests(unittest.TestCase):
    def test_reference_catalog_structure_and_sync(self) -> None:
        if not CATALOG.is_file() or not PACKAGE.is_file():
            self.skipTest("reference npm command catalog not present")
        catalog = load_catalog(CATALOG)
        structure_errors = validate_catalog_structure(catalog)
        self.assertEqual(structure_errors, [], structure_errors)
        sync_errors, count = validate_catalog_sync(REPO_ROOT, CATALOG, PACKAGE)
        self.assertEqual(sync_errors, [], sync_errors)
        self.assertGreater(count, 50)

    def test_catalog_rejects_duplicate_names(self) -> None:
        catalog = {
            "sections": [
                {
                    "id": "a",
                    "commands": [
                        {"name": "dup", "description": "one"},
                        {"name": "dup", "description": "two"},
                    ],
                }
            ]
        }
        errors = validate_catalog_structure(catalog)
        self.assertTrue(any("duplicate" in err for err in errors))

    def test_cli_help_list_includes_ordia(self) -> None:
        if not CATALOG.is_file():
            self.skipTest("reference npm command catalog not present")
        proc = subprocess.run(
            [*CLI_CMD, "help", "--list", "-C", str(REPO_ROOT)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        names = proc.stdout.splitlines()
        self.assertIn("ordia:validate", names)
        self.assertIn("ordia:doctor", names)

    def test_cli_help_detail_ordia_validate(self) -> None:
        if not CATALOG.is_file():
            self.skipTest("reference npm command catalog not present")
        proc = subprocess.run(
            [*CLI_CMD, "help", "ordia:validate", "-C", str(REPO_ROOT)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("Command: ordia:validate", proc.stdout)
        self.assertIn("npm run ordia:validate", proc.stdout)

    def test_cli_commands_validate_passes_on_repo(self) -> None:
        if not CATALOG.is_file() or not PACKAGE.is_file():
            self.skipTest("reference npm command catalog not present")
        proc = subprocess.run(
            [*CLI_CMD, "commands", "validate", "-C", str(REPO_ROOT)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("RESULT: PASS", proc.stdout)

    def test_sync_detects_missing_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            catalog_path = target / "catalog.json"
            package_path = target / "package.json"
            catalog_path.write_text(
                json.dumps(
                    {
                        "sections": [
                            {
                                "id": "x",
                                "commands": [{"name": "only-in-catalog", "description": "x"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            package_path.write_text(json.dumps({"scripts": {}}), encoding="utf-8")
            errors, _ = validate_catalog_sync(target, catalog_path, package_path)
            self.assertTrue(any("only-in-catalog" in err for err in errors))
