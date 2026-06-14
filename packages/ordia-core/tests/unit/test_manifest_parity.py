"""Parity between stdlib ordia_manifest hook loader and ordia.config PyYAML loader."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from ordia.config import load_ordia_config

REPO_ROOT = Path(__file__).resolve().parents[4]
CORE_ROOT = REPO_ROOT / "packages" / "ordia-core"
HOOKS_LIB = CORE_ROOT / "ordia" / "cursor_bundle" / "hooks" / "lib"
sys.path.insert(0, str(HOOKS_LIB))

from ordia_manifest import (  # noqa: E402
    is_control_path as manifest_is_control_path,
    is_product_path as manifest_is_product_path,
    load_manifest_config,
)

MINIMAL_V03 = """\
version: "0.3"
profile: parity-test

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


def _write_greenfield(root: Path) -> None:
    control = root / "docs" / "control"
    control.mkdir(parents=True)
    (control / "ORCHESTRATION_STATE.md").write_text("# state\n", encoding="utf-8")
    (control / "PROFILE.md").write_text("# profile\n", encoding="utf-8")
    (control / "COMMANDS.md").write_text("# commands\n", encoding="utf-8")
    (control / "commands.catalog.json").write_text('{"meta":{},"sections":[]}', encoding="utf-8")
    (root / "ordia.yaml").write_text(MINIMAL_V03, encoding="utf-8")


def test_manifest_parity_v03_profile_and_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_greenfield(root)
        py_config = load_ordia_config(root)
        hook_config = load_manifest_config(root)
        assert py_config is not None
        assert hook_config is not None

        assert py_config.profile == hook_config.profile == "parity-test"
        assert py_config.project_profile_path.resolve() == hook_config.project_profile_path.resolve()
        assert py_config.control_root.resolve() == (root / "docs" / "control").resolve()

        sample_product = "src/app.ts"
        sample_control = "docs/control/PROFILE.md"
        assert manifest_is_product_path(sample_product, hook_config) == True  # noqa: E712
        assert manifest_is_control_path(sample_control, hook_config) == True  # noqa: E712
        assert manifest_is_control_path("ordia.yaml", hook_config) == True  # noqa: E712

        from ordia.config import is_control_path, is_product_path

        assert is_product_path(sample_product, py_config)
        assert is_control_path(sample_control, py_config)
        assert is_control_path("ordia.yaml", py_config)
