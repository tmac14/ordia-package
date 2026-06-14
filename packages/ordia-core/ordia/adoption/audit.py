"""Full-repository documentation and config audit for Ordia adoption."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

MARKDOWN_SKIP = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__"}
CONFIG_FILES = (
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
)
GOVERNANCE_FILES = ("AGENTS.md", "CONTRIBUTING.md", "COMMANDS.md")


@dataclass
class DocsAuditResult:
    root: Path
    markdown_files: list[dict[str, Any]] = field(default_factory=list)
    config_summaries: list[dict[str, Any]] = field(default_factory=list)
    directory_hints: list[str] = field(default_factory=list)
    suggested_product_roots: list[str] = field(default_factory=list)
    suggested_control_root: str = "docs/control"
    uncataloged_scripts: list[str] = field(default_factory=list)
    ordia_gaps: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "markdown_count": len(self.markdown_files),
            "markdown_files": self.markdown_files,
            "config_summaries": self.config_summaries,
            "directory_hints": self.directory_hints,
            "suggested_product_roots": self.suggested_product_roots,
            "suggested_control_root": self.suggested_control_root,
            "uncataloged_scripts": self.uncataloged_scripts,
            "ordia_gaps": self.ordia_gaps,
            "next_steps": self.next_steps,
        }


def _should_skip(path: Path) -> bool:
    return any(part in MARKDOWN_SKIP for part in path.parts)


def _scan_markdown(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates: list[Path] = []
    for name in ("README.md", "README.MD", "Readme.md"):
        candidate = root / name
        if candidate.is_file():
            candidates.append(candidate)
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        candidates.extend(path for path in docs_dir.rglob("*.md") if path.is_file())
    for path in root.glob("*.md"):
        if path.is_file():
            candidates.append(path)
    seen: set[Path] = set()
    for path in sorted(set(candidates)):
        if path in seen or _should_skip(path):
            continue
        seen.add(path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        title = ""
        headings: list[str] = []
        for line in text.splitlines()[:80]:
            if not title and line.startswith("# "):
                title = line[2:].strip()
            if line.startswith("## "):
                headings.append(line[3:].strip())
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "title": title or path.stem,
                "headings": headings[:6],
                "size_bytes": path.stat().st_size,
            }
        )
    return rows


def _read_package_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
    return {
        "path": path.relative_to(path.parent.parent if path.parent.name == "packages" else path.parent).as_posix()
        if path.parent == path.parent.parent
        else path.relative_to(path.anchor and path or path).as_posix(),
        "name": data.get("name") if isinstance(data, dict) else None,
        "scripts": sorted(scripts.keys()) if isinstance(scripts, dict) else [],
    }


def _scan_configs(root: Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
            summaries.append(
                {
                    "path": "package.json",
                    "kind": "npm",
                    "name": data.get("name") if isinstance(data, dict) else None,
                    "scripts": sorted(scripts.keys()) if isinstance(scripts, dict) else [],
                }
            )
        except (OSError, json.JSONDecodeError):
            pass
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            project = data.get("project", {}) if isinstance(data, dict) else {}
            scripts = project.get("scripts", {}) if isinstance(project, dict) else {}
            summaries.append(
                {
                    "path": "pyproject.toml",
                    "kind": "python",
                    "name": project.get("name") if isinstance(project, dict) else None,
                    "scripts": sorted(scripts.keys()) if isinstance(scripts, dict) else [],
                }
            )
        except (OSError, Exception):  # noqa: BLE001
            pass
    for name in CONFIG_FILES[2:]:
        path = root / name
        if path.is_file():
            summaries.append({"path": name, "kind": name.split(".")[0], "scripts": []})
    for gov in GOVERNANCE_FILES:
        if (root / gov).is_file():
            summaries.append({"path": gov, "kind": "governance", "scripts": []})
    return summaries


def _directory_hints(root: Path) -> tuple[list[str], list[str]]:
    hints: list[str] = []
    product_roots: list[str] = []
    mapping = {
        "src": "src/",
        "apps": "apps/",
        "packages": "packages/",
        "infra": "infra/",
        "docker": "docker/",
        "db": "db/",
        "migrations": "migrations/",
    }
    for name, prefix in mapping.items():
        if (root / name).is_dir():
            hints.append(name)
            if name in {"src", "apps", "packages"}:
                product_roots.append(prefix)
    if not product_roots:
        product_roots = ["src/"]
    return hints, product_roots


def _detect_control_root(root: Path) -> str:
    if (root / "docs" / "control").is_dir():
        return "docs/control"
    if (root / "docs" / "coordination").is_dir():
        return "docs/coordination"
    return "docs/control"


def _ordia_gaps(root: Path) -> list[str]:
    gaps: list[str] = []
    if not (root / "ordia.yaml").is_file():
        gaps.append("ordia.yaml missing")
    control = _detect_control_root(root)
    control_dir = root / control
    for name in (
        "TASK_REGISTRY.yaml",
        "AGENT_REGISTRY.yaml",
        "ORCHESTRATION_STATE.md",
        "PROFILE.md",
    ):
        if not (control_dir / name).is_file():
            gaps.append(f"{control}/{name} missing")
    if not (root / ".cursor" / "hooks.json").is_file():
        gaps.append(".cursor/hooks.json missing (run ordia init --with-cursor)")
    return gaps


def _uncataloged_scripts(root: Path, catalog_path: Path | None) -> list[str]:
    pkg = root / "package.json"
    if not pkg.is_file():
        return []
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
        scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(scripts, dict):
        return []
    catalog_names: set[str] = set()
    if catalog_path and catalog_path.is_file():
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            for section in catalog.get("sections", []) or []:
                if not isinstance(section, dict):
                    continue
                for cmd in section.get("commands", []) or []:
                    if isinstance(cmd, dict) and cmd.get("name"):
                        catalog_names.add(str(cmd["name"]))
        except (OSError, json.JSONDecodeError):
            pass
    skip = {"help", "help:validate", "help:list"}
    return sorted(name for name in scripts if name not in catalog_names and name not in skip)


def format_adoption_report(result: DocsAuditResult) -> str:
    lines = [
        "# Ordia Adoption Report",
        "",
        f"**Generated:** {date.today().isoformat()}",
        f"**Repository:** `{result.root}`",
        "",
        "## Documentation map",
        "",
        f"Found **{len(result.markdown_files)}** markdown file(s).",
        "",
    ]
    for row in result.markdown_files[:40]:
        headings = ", ".join(row.get("headings", [])[:3]) or "—"
        lines.append(f"- `{row['path']}` — {row.get('title', '—')} ({headings})")
    if len(result.markdown_files) > 40:
        lines.append(f"- … and {len(result.markdown_files) - 40} more")

    lines.extend(["", "## Config and governance", ""])
    for cfg in result.config_summaries:
        scripts = cfg.get("scripts") or []
        script_note = f" — scripts: {', '.join(scripts[:12])}" if scripts else ""
        lines.append(f"- `{cfg['path']}` ({cfg.get('kind')}){script_note}")

    lines.extend(
        [
            "",
            "## Suggested ordia.yaml (starter)",
            "",
            "```yaml",
            'version: "0.3"',
            "profile: your-profile-id",
            "control:",
            f"  root: {result.suggested_control_root}",
            "  state: ORCHESTRATION_STATE.md",
            "  taskRegistry: TASK_REGISTRY.yaml",
            "  agentRegistry: AGENT_REGISTRY.yaml",
            "  projectProfile: PROFILE.md",
            "enforcement:",
            f"  productRoots: [{', '.join(repr(p) for p in result.suggested_product_roots)}]",
            "closure:",
            "  validator: ordia validate --project",
            "```",
            "",
            "## Directory hints",
            "",
        ]
    )
    lines.append(", ".join(result.directory_hints) or "(none detected)")

    if result.uncataloged_scripts:
        lines.extend(["", "## Uncataloged npm scripts", ""])
        for script in result.uncataloged_scripts[:30]:
            lines.append(f"- `{script}`")
        lines.append("- Run `ordia init --sync-commands` after scaffold to seed catalog.")

    if result.ordia_gaps:
        lines.extend(["", "## Ordia gaps", ""])
        for gap in result.ordia_gaps:
            lines.append(f"- {gap}")

    lines.extend(["", "## Next steps", ""])
    for step in result.next_steps:
        lines.append(f"1. {step}")

    return "\n".join(lines) + "\n"


def format_inventory_markdown(result: DocsAuditResult) -> str:
    lines = [
        "# Documentation inventory",
        "",
        "Top-level coordination and adoption docs. Update when adding/removing `.md`/`.yaml` under control root.",
        "",
        "## Coordination docs",
        "",
    ]
    control = result.suggested_control_root
    for name in (
        "TASK_REGISTRY.yaml",
        "AGENT_REGISTRY.yaml",
        "ORCHESTRATION_STATE.md",
        "PROFILE.md",
        "DECISION_LOG.md",
        "EVIDENCE_INDEX.md",
        "ADOPTION_REPORT.md",
        "commands.catalog.json",
        "COMMANDS.md",
    ):
        lines.append(f"- `{control}/{name}`")
    lines.extend(["", "## Repository docs (sample)", ""])
    for row in result.markdown_files[:25]:
        lines.append(f"- `{row['path']}`")
    return "\n".join(lines) + "\n"


def run_docs_audit(
    root: Path,
    *,
    catalog_path: Path | None = None,
) -> DocsAuditResult:
    root = root.resolve()
    hints, product_roots = _directory_hints(root)
    control_root = _detect_control_root(root)
    result = DocsAuditResult(
        root=root,
        markdown_files=_scan_markdown(root),
        config_summaries=_scan_configs(root),
        directory_hints=hints,
        suggested_product_roots=product_roots,
        suggested_control_root=control_root,
        uncataloged_scripts=_uncataloged_scripts(root, catalog_path),
        ordia_gaps=_ordia_gaps(root),
        next_steps=[
            "pip install ordia-core && ordia init --skip-existing --with-cursor",
            "ordia docs audit --write-report (review ADOPTION_REPORT.md)",
            "ordia cursor sync && ordia validate --project",
            "Map uncataloged scripts with ordia init --sync-commands when package.json exists",
        ],
    )
    return result
