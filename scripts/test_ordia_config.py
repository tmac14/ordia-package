"""Unit tests for Ordia manifest loader."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia_config import (
    OrdiaConfig,
    is_control_path,
    is_product_path,
    load_ordia_config,
    validate_ordia_manifest,
)


MINIMAL_MANIFEST = """\
version: "0.3"
profile: test-profile

control:
  root: docs/control
  projectProfile: PROFILE.md

commands:
  catalog: commands.catalog.json
  profileDoc: COMMANDS.md

enforcement:
  productRoots:
    - src/
  controlRoots:
    - docs/control/
    - ordia.yaml
"""


class OrdiaConfigTests(unittest.TestCase):
    def _write_greenfield(self, root: Path) -> None:
        control = root / "docs" / "control"
        control.mkdir(parents=True)
        (control / "ORCHESTRATION_STATE.md").write_text("# state\n", encoding="utf-8")
        (control / "PROFILE.md").write_text("# profile\n", encoding="utf-8")
        (control / "COMMANDS.md").write_text("# commands\n", encoding="utf-8")
        (control / "commands.catalog.json").write_text('{"meta":{},"sections":[]}', encoding="utf-8")
        (root / "ordia.yaml").write_text(MINIMAL_MANIFEST, encoding="utf-8")

    def test_load_manifest_v03(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_greenfield(root)
            config = load_ordia_config(root)
            self.assertIsNotNone(config)
            assert config is not None
            self.assertEqual(config.version, "0.3")
            self.assertEqual(config.profile, "test-profile")
            self.assertEqual(
                config.project_profile_path.resolve(),
                (root / "docs" / "control" / "PROFILE.md").resolve(),
            )
            catalog_path = config.commands_catalog_path()
            assert catalog_path is not None
            self.assertEqual(
                catalog_path.resolve(),
                (root / "docs" / "control" / "commands.catalog.json").resolve(),
            )
            assert config.commands_profile_doc is not None
            self.assertEqual(
                config.commands_profile_doc.resolve(),
                (root / "docs" / "control" / "COMMANDS.md").resolve(),
            )

    def test_product_and_control_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_greenfield(root)
            config = load_ordia_config(root)
            assert config is not None
            self.assertTrue(is_product_path("src/app.ts", config))
            self.assertFalse(is_product_path("docs/control/TASK_REGISTRY.yaml", config))
            self.assertTrue(is_control_path("ordia.yaml", config))
            self.assertTrue(is_control_path("docs/control/PROFILE.md", config))

    def test_validate_manifest_passes_for_greenfield(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_greenfield(root)
            config = load_ordia_config(root)
            assert config is not None
            errors: list[str] = []
            warnings: list[str] = []
            validate_ordia_manifest(config, errors, warnings)
            self.assertEqual(errors, [])

    def test_legacy_agents_profile_at_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "control"
            control.mkdir(parents=True)
            (control / "ORCHESTRATION_STATE.md").write_text("# state\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# legacy profile\n", encoding="utf-8")
            manifest = MINIMAL_MANIFEST.replace("PROFILE.md", "AGENTS.md")
            (root / "ordia.yaml").write_text(manifest, encoding="utf-8")
            config = load_ordia_config(root)
            assert config is not None
            self.assertEqual(config.project_profile_path.resolve(), (root / "AGENTS.md").resolve())

    def test_fallback_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "control"
            control.mkdir(parents=True)
            (control / "ORCHESTRATION_STATE.md").write_text("# state\n", encoding="utf-8")
            config = load_ordia_config(root)
            self.assertIsNotNone(config)
            assert config is not None
            self.assertEqual(config.profile, "default")
            self.assertEqual(config.control_root.resolve(), control.resolve())
            self.assertEqual(
                config.project_profile_path.resolve(),
                (control / "PROFILE.md").resolve(),
            )


if __name__ == "__main__":
    unittest.main()
