"""Unit tests for docs audit."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ordia.adoption.audit import format_adoption_report, run_docs_audit


class DocsAuditUnitTests(unittest.TestCase):
    def test_audit_detects_gaps_and_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "package.json").write_text(
                '{"scripts":{"dev:web":"vite","tunnel:start":"t"}}',
                encoding="utf-8",
            )
            result = run_docs_audit(root)
            self.assertIn("ordia.yaml missing", result.ordia_gaps)
            self.assertIn("tunnel:start", result.uncataloged_scripts)
            self.assertIn("src/", result.suggested_product_roots)

    def test_audit_full_repo_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "coordination"
            control.mkdir(parents=True)
            (root / "docs" / "guide.md").write_text("# Guide\n\n## Setup\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
            (root / "CONTRIBUTING.md").write_text("# Contrib\n", encoding="utf-8")
            (root / "apps" / "web").mkdir(parents=True)
            (root / "infra").mkdir()
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "go.mod").write_text("module example.com/demo\n", encoding="utf-8")
            (root / "pyproject.toml").write_text(
                '[project]\nname = "demo"\n[project.scripts]\nordia = "ordia.cli:main"\n',
                encoding="utf-8",
            )
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "name": "demo",
                        "scripts": {"dev:web": "vite", "help": "echo", "tunnel:start": "t"},
                    }
                ),
                encoding="utf-8",
            )
            catalog = control / "commands.catalog.json"
            catalog.write_text(
                json.dumps(
                    {
                        "sections": [
                            {"commands": [{"name": "dev:web"}]},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (root / "ordia.yaml").write_text(
                'version: "0.3"\nprofile: demo\ncontrol:\n  root: docs/coordination\n',
                encoding="utf-8",
            )
            for name in ("TASK_REGISTRY.yaml", "ORCHESTRATION_STATE.md", "PROFILE.md"):
                (control / name).write_text("ok\n", encoding="utf-8")

            result = run_docs_audit(root, catalog_path=catalog)
            payload = result.to_dict()

            self.assertEqual(payload["suggested_control_root"], "docs/coordination")
            self.assertIn("apps", result.directory_hints)
            self.assertIn("apps/", result.suggested_product_roots)
            self.assertIn("pyproject.toml", [c["path"] for c in result.config_summaries])
            self.assertIn("Cargo.toml", [c["path"] for c in result.config_summaries])
            self.assertIn("go.mod", [c["path"] for c in result.config_summaries])
            self.assertIn("AGENTS.md", [c["path"] for c in result.config_summaries])
            self.assertGreaterEqual(len(result.markdown_files), 2)
            self.assertNotIn("dev:web", result.uncataloged_scripts)
            self.assertIn("docs/coordination/AGENT_REGISTRY.yaml missing", result.ordia_gaps)
            report = format_adoption_report(result)
            self.assertIn("docs/coordination", report)
            self.assertIn("Uncataloged npm scripts", report)


if __name__ == "__main__":
    unittest.main()
