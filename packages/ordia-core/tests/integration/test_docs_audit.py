"""Integration tests for ordia docs audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ordia.adoption.audit import run_docs_audit

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]
SAMPLE_REPO = REPO_ROOT / "examples" / "brownfield-adoption" / "sample-repo"


class DocsAuditIntegrationTests(unittest.TestCase):
    def test_audit_finds_markdown_and_scripts(self) -> None:
        if not SAMPLE_REPO.is_dir():
            self.skipTest("sample-repo missing")
        result = run_docs_audit(SAMPLE_REPO)
        paths = {row["path"] for row in result.markdown_files}
        self.assertIn("README.md", paths)
        self.assertIn("docs/ARCHITECTURE.md", paths)
        self.assertIn("src", result.directory_hints or ["src"])
        self.assertTrue(any("tunnel:start" in script for script in result.uncataloged_scripts))
        self.assertIn("ordia.yaml missing", result.ordia_gaps)

    def test_cli_docs_audit_json_and_write_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "README.md").write_text("# Demo\n", encoding="utf-8")
            (target / "package.json").write_text('{"scripts":{"dev:web":"vite"}}', encoding="utf-8")
            json_proc = subprocess.run(
                [*CLI_CMD, "docs", "audit", "--directory", str(target), "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(json_proc.returncode, 0, json_proc.stderr or json_proc.stdout)
            payload = json.loads(json_proc.stdout)
            self.assertEqual(payload["command"], "docs audit")
            self.assertGreater(payload["metadata"]["markdown_count"], 0)

            write_proc = subprocess.run(
                [
                    *CLI_CMD,
                    "docs",
                    "audit",
                    "--directory",
                    str(target),
                    "--write-report",
                    "--write-inventory",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(write_proc.returncode, 0, write_proc.stderr or write_proc.stdout)
            self.assertTrue((target / "docs" / "control" / "ADOPTION_REPORT.md").is_file())
            self.assertTrue((target / "docs" / "control" / "DOCUMENTATION_INVENTORY.md").is_file())


if __name__ == "__main__":
    unittest.main()
