"""Integration tests for JSON CLI output."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]

pytestmark = pytest.mark.integration


class JsonCliTests(unittest.TestCase):
    def test_doctor_json_greenfield(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [*CLI_CMD, "init", "--directory", str(target), "--with-cursor", "--profile", "json-doc"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            doctor = subprocess.run(
                [*CLI_CMD, "doctor", "--directory", str(target), "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(doctor.returncode, 0, doctor.stderr or doctor.stdout)
            data = json.loads(doctor.stdout)
            self.assertEqual(data["command"], "doctor")
            self.assertTrue(data["ok"])
            self.assertIn("schema_version", data)
            self.assertIn("metadata", data)

    def test_validate_project_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [*CLI_CMD, "init", "--directory", str(target), "--profile", "json-val"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            validate = subprocess.run(
                [*CLI_CMD, "validate", "--project", "--directory", str(target), "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr or validate.stdout)
            data = json.loads(validate.stdout)
            self.assertEqual(data["command"], "validate")
            self.assertTrue(data["ok"])
            self.assertEqual(data["metadata"]["profile"], "json-val")

    def test_validate_json_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            validate = subprocess.run(
                [*CLI_CMD, "validate", "--json", "--directory", str(target)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 1)
            data = json.loads(validate.stdout)
            self.assertFalse(data["ok"])
            self.assertTrue(data["issues"])
