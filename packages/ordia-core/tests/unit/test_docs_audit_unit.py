"""Unit tests for docs audit."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia.adoption.audit import run_docs_audit


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


if __name__ == "__main__":
    unittest.main()
