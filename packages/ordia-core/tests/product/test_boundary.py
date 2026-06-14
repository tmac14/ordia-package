"""Package boundary tests — profile/project content must not leak into wheel or greenfield."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CORE_ROOT = REPO_ROOT / "packages" / "ordia-core"
CLI_CMD = [sys.executable, "-m", "ordia.cli"]
PRODUCT_DOCS = CORE_ROOT / "ordia" / "product_docs"
CURSOR_BUNDLE = CORE_ROOT / "ordia" / "cursor_bundle"
NESTED_MINIMAL = CORE_ROOT / "ordia" / "templates" / "monorepo" / "minimal"

PROFILE_LEAK_PATTERNS = (
    re.compile(r"docs/coordination/tasks", re.I),
    re.compile(r"intents\.narofitness\.yaml", re.I),
    re.compile(r"\bAPP-PLATFORM-", re.I),
    re.compile(r"\bIMPORT-FDL", re.I),
    re.compile(r"profile:\s*narofitness", re.I),
    re.compile(r"narofitness-permanent-guardrails", re.I),
)


def _collect_leaks(text: str, label: str) -> list[str]:
    hits: list[str] = []
    for pattern in PROFILE_LEAK_PATTERNS:
        if pattern.search(text):
            hits.append(f"{label}: matched {pattern.pattern}")
    return hits


def _scan_tree(root: Path, glob: str = "**/*") -> list[str]:
    leaks: list[str] = []
    for path in sorted(root.glob(glob)):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".py", ".mdc", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        leaks.extend(_collect_leaks(text, str(path.relative_to(root))))
    return leaks


class OrdiaPackageBoundaryTests(unittest.TestCase):
    def test_product_docs_no_profile_leaks(self) -> None:
        leaks = _scan_tree(PRODUCT_DOCS)
        self.assertEqual(leaks, [], "product_docs must be portable:\n" + "\n".join(leaks))

    def test_cursor_bundle_no_profile_leaks(self) -> None:
        self.assertTrue(CURSOR_BUNDLE.is_dir(), "cursor_bundle must exist — run sync_cursor_bundle.py --sync")
        leaks = _scan_tree(CURSOR_BUNDLE)
        self.assertEqual(leaks, [], "cursor_bundle must be portable:\n" + "\n".join(leaks))

    def test_cursor_bundle_matches_template(self) -> None:
        template = REPO_ROOT / "packages" / "ordia-cursor" / "templates"
        self.assertTrue(template.is_dir())
        for path in template.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            relative = path.relative_to(template)
            wheel_copy = CURSOR_BUNDLE / relative
            self.assertTrue(wheel_copy.is_file(), f"missing wheel bundle copy: {relative}")
            self.assertEqual(
                path.read_bytes(),
                wheel_copy.read_bytes(),
                f"wheel bundle drift: {relative}",
            )

    def test_no_nested_monorepo_minimal_template(self) -> None:
        self.assertFalse(
            NESTED_MINIMAL.exists(),
            f"nested template debt must not exist: {NESTED_MINIMAL}",
        )

    def test_greenfield_init_uses_bundled_product_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [
                    *CLI_CMD,
                    "init",
                    "--directory",
                    str(target),
                    "--profile",
                    "boundary-test",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            daily = target / "docs" / "ordia" / "DAILY_USAGE.md"
            self.assertTrue(daily.is_file())
            text = daily.read_text(encoding="utf-8")
            self.assertIn("{controlRoot}", text)
            self.assertNotIn("docs/coordination/tasks", text)
            self.assertNotIn("APP-PLATFORM", text)

    def test_from_repo_docs_is_opt_in_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [
                    *CLI_CMD,
                    "init",
                    "--directory",
                    str(target),
                    "--from-repo-docs",
                    "--profile",
                    "ref-copy",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            readme = (target / "docs" / "ordia" / "README.md").read_text(encoding="utf-8")
            self.assertIn("ordia-package", readme)

    def test_wheel_product_docs_no_profile_leaks(self) -> None:
        if shutil.which("pip") is None:
            self.skipTest("pip not available")
        build_pkg = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "build"],
            capture_output=True,
            text=True,
            check=False,
        )
        if build_pkg.returncode != 0:
            self.skipTest("build package not installable")
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "dist"
            wheel_build = subprocess.run(
                [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist)],
                cwd=CORE_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(wheel_build.returncode, 0, wheel_build.stderr or wheel_build.stdout)
            wheels = list(dist.glob("ordia_core-*.whl"))
            self.assertTrue(wheels)
            leaks: list[str] = []
            with zipfile.ZipFile(wheels[0]) as archive:
                for name in archive.namelist():
                    if name.startswith("ordia/product_docs/") and name.endswith(".md"):
                        body = archive.read(name).decode("utf-8", errors="replace")
                        leaks.extend(_collect_leaks(body, name))
                    if name.startswith("ordia/cursor_bundle/") and name.endswith(
                        (".md", ".py", ".mdc", ".json")
                    ):
                        body = archive.read(name).decode("utf-8", errors="replace")
                        leaks.extend(_collect_leaks(body, name))
            self.assertEqual(leaks, [], "wheel portable content leaks:\n" + "\n".join(leaks))
