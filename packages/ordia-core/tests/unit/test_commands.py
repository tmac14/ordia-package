"""Tests for Ordia command catalog module and CLI help/commands."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ordia.commands.catalog import (
    collect_command_map,
    collect_command_names,
    load_catalog,
    load_package_scripts,
    resolve_catalog_paths,
    seed_catalog_from_package,
    validate_catalog_sync,
)
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

    def test_seed_catalog_from_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            catalog_path = target / "docs" / "control" / "commands.catalog.json"
            package_path = target / "package.json"
            package_path.write_text(
                json.dumps(
                    {
                        "scripts": {
                            "help": "echo help",
                            "ordia:doctor": "ordia doctor",
                            "build": "echo build",
                        }
                    }
                ),
                encoding="utf-8",
            )
            count = seed_catalog_from_package(target, catalog_path, package_path, profile="demo")
            self.assertEqual(count, 2)
            self.assertTrue(catalog_path.is_file())
            catalog = load_catalog(catalog_path)
            names = collect_command_names(catalog)
            self.assertIn("ordia:doctor", names)
            self.assertIn("build", names)
            self.assertNotIn("help", names)

    def test_load_package_scripts_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "package.json"
            path.write_text('{"scripts": "not-a-dict"}', encoding="utf-8")
            scripts = load_package_scripts(path)
            self.assertEqual(scripts, {})

    def test_validate_catalog_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            errors, count = validate_catalog_sync(target)
            self.assertGreater(len(errors), 0)
            self.assertEqual(count, 0)

    def test_validate_catalog_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            catalog_path = target / "catalog.json"
            package_path = target / "package.json"
            catalog_path.write_text("{bad", encoding="utf-8")
            package_path.write_text('{"scripts": {}}', encoding="utf-8")
            errors, count = validate_catalog_sync(target, catalog_path, package_path)
            self.assertTrue(any("could not load catalog" in err for err in errors))
            self.assertEqual(count, 0)

    def test_collect_command_map(self) -> None:
        catalog = {
            "sections": [
                {
                    "id": "x",
                    "title": "Section",
                    "commands": [{"name": "a", "description": "A"}],
                }
            ]
        }
        mapping = collect_command_map(catalog)
        self.assertIn("a", mapping)
        self.assertEqual(mapping["a"]["section"]["title"], "Section")

    def test_resolve_catalog_paths_without_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            catalog_path, package_path = resolve_catalog_paths(target)
            self.assertEqual(catalog_path, target / "docs/control/commands.catalog.json")
            self.assertEqual(package_path, target / "package.json")

    def test_load_catalog_rejects_non_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_catalog(path)
