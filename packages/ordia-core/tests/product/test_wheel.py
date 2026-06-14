"""Wheel packaging and package-data tests for ordia-core."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
CORE_ROOT = REPO_ROOT / "packages" / "ordia-core"
CLI_CMD = [sys.executable, "-m", "ordia.cli"]

pytestmark = pytest.mark.wheel


class OrdiaWheelTests(unittest.TestCase):
    def test_package_version_and_resources(self) -> None:
        import ordia  # noqa: WPS433

        self.assertEqual(ordia.__version__, "0.10.0")
        template = CORE_ROOT / "ordia" / "templates" / "minimal" / "ordia.yaml"
        self.assertTrue(template.is_file(), "minimal template must ship in source tree")
        protocol = CORE_ROOT / "ordia" / "protocols" / "TASK_EXECUTION.md"
        self.assertTrue(protocol.is_file(), "protocol templates must ship in source tree")

    def test_wheel_build_and_greenfield_init(self) -> None:
        if shutil.which("pip") is None:
            self.skipTest("pip not available")
        build = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "build"],
            capture_output=True,
            text=True,
            check=False,
        )
        if build.returncode != 0:
            self.skipTest("build package not installable")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dist = tmp_path / "dist"
            wheel_build = subprocess.run(
                [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist)],
                cwd=CORE_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(wheel_build.returncode, 0, wheel_build.stderr or wheel_build.stdout)

            wheels = list(dist.glob("ordia_core-*.whl"))
            self.assertTrue(wheels, "wheel not produced")
            wheel = wheels[0]

            with zipfile.ZipFile(wheel) as archive:
                names = archive.namelist()
                self.assertTrue(
                    any(n.startswith("ordia/templates/minimal/") for n in names),
                    f"wheel missing templates: {names[:20]}",
                )
                self.assertTrue(
                    any(n.startswith("ordia/protocols/") and n.endswith(".md") for n in names),
                    "wheel missing protocol templates",
                )
                self.assertTrue(
                    any(n.startswith("ordia/cursor_bundle/hooks.json") for n in names),
                    "wheel missing embedded cursor bundle",
                )
                self.assertTrue(
                    any("ordia/cursor_bundle/rules/ordia-" in n and n.endswith(".mdc") for n in names),
                    "wheel missing ordia cursor rules",
                )

            venv = tmp_path / "venv"
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv)],
                check=True,
                capture_output=True,
            )
            pip = venv / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
            python = venv / ("Scripts" if sys.platform == "win32" else "bin") / "python"
            subprocess.run([str(pip), "install", "-q", str(wheel)], check=True, capture_output=True)
            target = tmp_path / "greenfield"
            init = subprocess.run(
                [str(python), "-m", "ordia.cli", "init", "--directory", str(target), "--profile", "wheel-test"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            self.assertTrue((target / "ordia.yaml").is_file())

            target_cursor = tmp_path / "greenfield-cursor"
            init_cursor = subprocess.run(
                [
                    str(python),
                    "-m",
                    "ordia.cli",
                    "init",
                    "--with-cursor",
                    "--directory",
                    str(target_cursor),
                    "--profile",
                    "wheel-cursor",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init_cursor.returncode, 0, init_cursor.stderr or init_cursor.stdout)
            self.assertTrue((target_cursor / ".cursor" / "hooks.json").is_file())
            self.assertTrue((target_cursor / ".cursor" / "hooks" / "validate_runtime_header.py").is_file())
            self.assertTrue(any((target_cursor / ".cursor" / "rules").glob("ordia-*.mdc")))
