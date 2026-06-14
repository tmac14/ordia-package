"""Tests for Ordia workflow intents (v0.8 / ORDIA-D023)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ordia.workflows import (
    describe_intent,
    emit_header,
    emit_prompt,
    intent_ids,
    list_intents,
    load_intent,
)
from ordia.workflows.loader import load_intents_document, overlay_path, workflows_root

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]
INTENTS_PATH = workflows_root() / "intents.yaml"


class WorkflowRegistryTests(unittest.TestCase):
    def test_core_intent_count(self) -> None:
        ids = intent_ids(REPO_ROOT)
        self.assertGreaterEqual(len(ids), 18)
        self.assertIn("implement_feature", ids)
        self.assertIn("recover", ids)
        self.assertIn("close_task", ids)

    def test_list_by_category(self) -> None:
        control = list_intents(REPO_ROOT, category="control")
        self.assertTrue(all(item.category == "control" for item in control))
        self.assertIn("orchestrate_batch", [item.id for item in control])

    def test_unknown_intent(self) -> None:
        self.assertIsNone(load_intent(REPO_ROOT, "not-a-real-intent"))

    def test_describe_intent_runtimes(self) -> None:
        text = describe_intent(REPO_ROOT, "recover")
        self.assertIn("Runtimes:", text)
        self.assertIn("ONLY_CODEX", text)


class WorkflowEmitTests(unittest.TestCase):
    def test_emit_recover_without_task(self) -> None:
        block = emit_prompt(REPO_ROOT, "recover")
        self.assertIn("Runtime:", block)
        self.assertIn("intent: recover", block)
        self.assertIn("## Prompt body", block)
        self.assertIn("## Validation checklist", block)

    def test_emit_header_only(self) -> None:
        header = emit_header(REPO_ROOT, "recover")
        self.assertIn("Runtime: ONLY_CURSOR", header)
        self.assertNotIn("## Prompt body", header)

    def test_emit_implement_feature_requires_task(self) -> None:
        with self.assertRaises(ValueError):
            emit_prompt(REPO_ROOT, "implement_feature")

    def test_emit_implement_feature_with_task(self) -> None:
        block = emit_prompt(REPO_ROOT, "implement_feature", task_id="APP-PLATFORM-UX-3.0-PHASE-2D")
        self.assertIn("intent: implement_feature", block)
        self.assertIn("APP-PLATFORM-UX-3.0-PHASE-2D", block)
        self.assertIn("Model usage", block)

    def test_emit_approve_model_includes_recommend_hint(self) -> None:
        block = emit_prompt(REPO_ROOT, "approve_model", task_id="IMPORT-FDL-FULL-QUALITY-NEXT")
        self.assertIn("approve_model", block)
        self.assertIn("Model recommendation", block)


class WorkflowOverlayTests(unittest.TestCase):
    def test_narofitness_overlay_intents(self) -> None:
        overlay = REPO_ROOT / "docs" / "coordination" / "workflows" / "intents.narofitness.yaml"
        if not overlay.is_file():
            self.skipTest("narofitness profile overlay not present")
        ids = intent_ids(REPO_ROOT)
        self.assertIn("import_regression", ids)
        self.assertIn("import_page_audit", ids)


class WorkflowCliTests(unittest.TestCase):
    def test_cli_workflow_list(self) -> None:
        proc = subprocess.run(
            [*CLI_CMD, "workflow", "list", "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 18)

    def test_cli_prompt_emit_recover(self) -> None:
        proc = subprocess.run(
            [*CLI_CMD, "prompt", "emit", "--intent", "recover"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("intent: recover", proc.stdout)


class WorkflowLoaderTests(unittest.TestCase):
    def test_load_intents_document_core_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [*CLI_CMD, "init", "--directory", str(target), "--profile", "loader-test"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            doc = load_intents_document(target)
            self.assertIn("intents", doc)
            self.assertGreaterEqual(len(doc["intents"]), 18)

    def test_overlay_path_with_profile_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [*CLI_CMD, "init", "--directory", str(target), "--profile", "overlay-demo"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            overlay_dir = target / "docs" / "control" / "workflows"
            overlay_dir.mkdir(parents=True, exist_ok=True)
            overlay_file = overlay_dir / "intents.overlay-demo.yaml"
            overlay_file.write_text(
                "schema_version: 1\nintents:\n  - id: recover\n    body_hint: overlay hint\n",
                encoding="utf-8",
            )
            from ordia.config import load_ordia_config

            config = load_ordia_config(target)
            assert config is not None
            path = overlay_path(target, config)
            self.assertEqual(path.resolve(), overlay_file.resolve())
            merged = load_intents_document(target)
            recover = next(i for i in merged["intents"] if i["id"] == "recover")
            self.assertEqual(recover.get("body_hint"), "overlay hint")
            self.assertEqual(merged.get("overlay_schema_version"), 1)

    def test_overlay_path_custom_rel_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [*CLI_CMD, "init", "--directory", str(target), "--profile", "custom-overlay"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            custom = target / "docs" / "control" / "my-intents.yaml"
            custom.write_text("intents:\n  - id: recover\n    title: Custom recover\n", encoding="utf-8")
            manifest = target / "ordia.yaml"
            text = manifest.read_text(encoding="utf-8")
            manifest.write_text(
                text + "\nworkflows:\n  overlay: docs/control/my-intents.yaml\n",
                encoding="utf-8",
            )
            from ordia.config import load_ordia_config

            config = load_ordia_config(target)
            assert config is not None
            path = overlay_path(target, config)
            self.assertEqual(path.resolve(), custom.resolve())

    def test_intents_no_legacy_control_commands(self) -> None:
        text = INTENTS_PATH.read_text(encoding="utf-8")
        self.assertNotIn("control:validate", text)
        self.assertNotIn("control:test", text)
