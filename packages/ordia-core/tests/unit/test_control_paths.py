"""Unit tests for control document path resolution."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia.control.paths import (
    basename_from_protocol_path,
    resolve_control_doc,
    resolve_registry_protocol_path,
)


class ControlPathsTests(unittest.TestCase):
    def test_basename_legacy_recovery(self) -> None:
        self.assertEqual(
            basename_from_protocol_path("docs/control/CONTROL_PLANE_RECOVERY_RUNBOOK.md"),
            "RECOVERY_RUNBOOK",
        )

    def test_resolve_greenfield_protocol_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "control"
            proto_dir = control / "protocols"
            proto_dir.mkdir(parents=True)
            (proto_dir / "TASK_EXECUTION.md").write_text("# task", encoding="utf-8")
            resolved = resolve_control_doc(root, "TASK_EXECUTION")
            self.assertIsNotNone(resolved)
            assert resolved is not None
            self.assertEqual(resolved.name, "TASK_EXECUTION.md")
            self.assertEqual(resolved.parent.name, "protocols")

    def test_resolve_legacy_protocol_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "control"
            control.mkdir(parents=True)
            (control / "RUNTIME_HANDOFF_PROTOCOL.md").write_text("# handoff", encoding="utf-8")
            resolved = resolve_control_doc(root, "RUNTIME_HANDOFF")
            self.assertIsNotNone(resolved)
            assert resolved is not None
            self.assertEqual(resolved.name, "RUNTIME_HANDOFF_PROTOCOL.md")

    def test_resolve_registry_protocol_path_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "control" / "protocols"
            control.mkdir(parents=True)
            (control / "RECOVERY_RUNBOOK.md").write_text("# recovery", encoding="utf-8")
            resolved = resolve_registry_protocol_path(
                root,
                "docs/control/CONTROL_PLANE_RECOVERY_RUNBOOK.md",
            )
            self.assertIsNotNone(resolved)
            assert resolved is not None
            self.assertTrue(resolved.is_file())


if __name__ == "__main__":
    unittest.main()
