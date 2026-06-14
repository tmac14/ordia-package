"""Tests for manifest strict modes and product roots rendering."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia.cli import _product_roots_list, _render_cursor_rule
from ordia.config import load_ordia_config
from ordia.validator.common import Validation
from ordia.validator.project import ProjectValidationOptions, validate_project


class ManifestStrictModesTests(unittest.TestCase):
    def test_closure_strict_from_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "control").mkdir(parents=True)
            for name in (
                "TASK_REGISTRY.yaml",
                "AGENT_REGISTRY.yaml",
                "ORCHESTRATION_STATE.md",
                "DECISION_LOG.md",
                "EVIDENCE_INDEX.md",
                "PROFILE.md",
            ):
                (root / "docs" / "control" / name).write_text("", encoding="utf-8")
            (root / "ordia.yaml").write_text(
                """
version: "0.3"
profile: strict-closure
control:
  root: docs/control
  state: ORCHESTRATION_STATE.md
  taskRegistry: TASK_REGISTRY.yaml
  agentRegistry: AGENT_REGISTRY.yaml
  projectProfile: PROFILE.md
enforcement:
  productRoots: [src/]
closure:
  validator: ordia validate --project
  strict: true
""".strip(),
                encoding="utf-8",
            )
            cfg = load_ordia_config(root)
            assert cfg is not None
            self.assertTrue(cfg.closure_strict)
            opts = ProjectValidationOptions()
            validate_project(root, cfg, opts)
            self.assertTrue(opts.strict_closure)

    def test_product_roots_list_from_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordia.yaml").write_text(
                """
version: "0.3"
profile: roots-test
enforcement:
  productRoots: [apps/, packages/]
""".strip(),
                encoding="utf-8",
            )
            listed = _product_roots_list(root)
            self.assertIn("apps/", listed)
            self.assertIn("packages/", listed)
            rendered = _render_cursor_rule(
                "roots: {{PRODUCT_ROOTS_LIST}}",
                root,
                "roots-test",
            )
            self.assertIn("apps/", rendered)


if __name__ == "__main__":
    unittest.main()
