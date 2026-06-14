"""Integration tests for ordia docs audit."""

from __future__ import annotations

import unittest
from pathlib import Path

from ordia.adoption.audit import run_docs_audit

SAMPLE_REPO = (
    Path(__file__).resolve().parents[4] / "examples" / "brownfield-adoption" / "sample-repo"
)


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


if __name__ == "__main__":
    unittest.main()
