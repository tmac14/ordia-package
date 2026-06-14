"""End-to-end tests for Ordia greenfield init and hook runtime."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
CORE_ROOT = REPO_ROOT / "packages" / "ordia-core"
CLI_CMD = [sys.executable, "-m", "ordia.cli"]
RECOVERY_RULE = CORE_ROOT / "ordia" / "cursor_bundle" / "rules" / "ordia-recovery-bootstrap.mdc"
if not RECOVERY_RULE.is_file():
    RECOVERY_RULE = REPO_ROOT / ".cursor" / "rules" / "ordia-recovery-bootstrap.mdc"
if not RECOVERY_RULE.is_file():
    RECOVERY_RULE = (
        REPO_ROOT / "packages" / "ordia-cursor" / "templates" / "rules" / "ordia-recovery-bootstrap.mdc"
    )

pytestmark = pytest.mark.integration


class OrdiaGreenfieldTests(unittest.TestCase):
    def _init(self, target: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        cmd = [*CLI_CMD, "init", "--directory", str(target), *extra]
        return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)

    def test_greenfield_with_cursor_validate_and_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = self._init(target, "--with-cursor", "--profile", "gf-test")
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)

            validate = subprocess.run(
                [*CLI_CMD, "validate", "--directory", str(target)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr or validate.stdout)

            doctor = subprocess.run(
                [*CLI_CMD, "doctor", "--directory", str(target)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(doctor.returncode, 0, doctor.stderr or doctor.stdout)
            self.assertIn("Inline manifest loader: installed", doctor.stdout)

    def test_greenfield_hooks_classify_src_product_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = self._init(target, "--with-cursor", "--profile", "gf-test")
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)

            probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; from pathlib import Path; "
                    "sys.path.insert(0, str(Path('.cursor/hooks/lib'))); "
                    "from ordia_manifest import load_manifest_config, is_product_path, is_control_path; "
                    "c = load_manifest_config(Path('.')); "
                    "assert c and is_product_path('src/app.ts', c); "
                    "assert is_control_path('docs/control/TASK_REGISTRY.yaml', c)",
                ],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr or probe.stdout)

    def test_greenfield_session_save_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = self._init(target, "--with-cursor", "--profile", "gf-test")
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)

            probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; from pathlib import Path; "
                    "sys.path.insert(0, '.cursor/hooks'); "
                    "from lib.control_context import save_session, load_full_session, control_root_hint; "
                    "root = Path('.'); "
                    "save_session(root, 'ONLY_CURSOR', 'IMPLEMENTATION', 'test', session_mode='UNIFIED', implementation_approved=False); "
                    "s = load_full_session(root); "
                    "assert s and s['session_mode'] == 'UNIFIED'; "
                    "assert control_root_hint(root) == 'docs/control'",
                ],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr or probe.stdout)

    def test_monorepo_greenfield_with_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = self._init(
                target,
                "--template",
                "monorepo",
                "--with-cursor",
                "--profile",
                "gf-mono",
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            manifest = (target / "ordia.yaml").read_text(encoding="utf-8")
            self.assertIn("apps/", manifest)

            probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; from pathlib import Path; "
                    "sys.path.insert(0, str(Path('.cursor/hooks/lib'))); "
                    "from ordia_manifest import load_manifest_config, is_product_path; "
                    "c = load_manifest_config(Path('.')); "
                    "assert c and is_product_path('apps/desktop/src/App.tsx', c)",
                ],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr or probe.stdout)

    def test_greenfield_scaffold_includes_profile_commands_catalog_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = self._init(target, "--with-cursor", "--profile", "gf-scaffold")
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            control = target / "docs" / "control"
            for name in ("PROFILE.md", "COMMANDS.md", "commands.catalog.json"):
                self.assertTrue((control / name).is_file(), f"missing {name}")
            self.assertTrue((control / "tasks").is_dir(), "tasks/ directory missing")
            self.assertTrue(
                (control / "tasks" / "TASK_PACKET_TEMPLATE.md").is_file(),
                "TASK_PACKET_TEMPLATE.md missing",
            )
            manifest = (target / "ordia.yaml").read_text(encoding="utf-8")
            self.assertIn('version: "0.3"', manifest)
            self.assertIn("projectProfile: PROFILE.md", manifest)
            self.assertIn("profileDoc: COMMANDS.md", manifest)

    def test_greenfield_agents_template_documents_control_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = self._init(target, "--profile", "gf-test")
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("PROFILE.md", agents)
            self.assertIn("docs/control/", agents)

    def test_recovery_rule_is_manifest_driven(self) -> None:
        text = RECOVERY_RULE.read_text(encoding="utf-8")
        self.assertIn("manifest-driven", text.lower())
        self.assertIn("{controlRoot}/ORCHESTRATION_STATE.md", text)
        self.assertIn("{projectProfile}", text)

    def test_greenfield_validate_project_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = self._init(target, "--with-cursor", "--profile", "gf-test")
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            validate = subprocess.run(
                [*CLI_CMD, "validate", "--project", "--directory", str(target)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr or validate.stdout)

    def test_greenfield_protocols_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = self._init(target, "--profile", "gf-proto")
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)

            protocols_dir = target / "docs" / "control" / "protocols"
            self.assertTrue(protocols_dir.is_dir(), "protocols directory missing")
            expected = {
                "TASK_EXECUTION.md",
                "CURSOR_ORCHESTRATION.md",
                "CURSOR_IMPLEMENTATION.md",
                "CODEX_ORCHESTRATION.md",
                "CODEX_IMPLEMENTATION.md",
                "RECOVERY_RUNBOOK.md",
                "RUNTIME_HANDOFF.md",
            }
            installed = {p.name for p in protocols_dir.glob("*.md")}
            self.assertEqual(expected, installed, f"missing protocols: {expected - installed}")

            agents = (target / "docs" / "control" / "AGENT_REGISTRY.yaml").read_text(encoding="utf-8")
            self.assertIn("docs/control/protocols/CURSOR_ORCHESTRATION.md", agents)
            self.assertIn("docs/control/protocols/CODEX_ORCHESTRATION.md", agents)
            self.assertIn("docs/control/protocols/RECOVERY_RUNBOOK.md", agents)

            task_exec = (protocols_dir / "TASK_EXECUTION.md").read_text(encoding="utf-8")
            self.assertIn("gf-proto", task_exec)

    def test_greenfield_product_docs_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = self._init(target, "--profile", "gf-docs")
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            ordia_docs = target / "docs" / "ordia"
            for name in ("README.md", "DAILY_USAGE.md", "SPEC_v0.8.md"):
                self.assertTrue((ordia_docs / name).is_file(), f"missing {name}")

    def test_init_sync_commands_seeds_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "package.json").write_text(
                '{"name":"sync-test","scripts":{"ordia:doctor":"ordia doctor","build":"echo build"}}',
                encoding="utf-8",
            )
            init = self._init(target, "--profile", "sync-test", "--sync-commands")
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            catalog = target / "docs" / "control" / "commands.catalog.json"
            self.assertTrue(catalog.is_file(), "expected commands.catalog.json")
            text = catalog.read_text(encoding="utf-8")
            self.assertIn("ordia:doctor", text)
