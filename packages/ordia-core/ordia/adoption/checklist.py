"""Adoption checklist and stale-report checks for ordia doctor."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None or not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def adoption_report_stale(root: Path, control_dir: Path, *, max_days: int = 30) -> str | None:
    report = control_dir / "ADOPTION_REPORT.md"
    if not report.is_file():
        return None
    text = report.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines()[:20]:
        if "**Generated:**" in line:
            raw = line.split("**Generated:**", 1)[-1].strip()
            try:
                generated = date.fromisoformat(raw)
            except ValueError:
                return None
            age = (date.today() - generated).days
            if age > max_days:
                return (
                    f"ADOPTION_REPORT.md is {age} days old (>{max_days}) — "
                    "re-run: ordia docs audit --write-report"
                )
            return None
    return None


def pending_adoption_steps(control_dir: Path) -> list[str]:
    checklist = control_dir / "adoption.checklist.yaml"
    doc = _load_yaml(checklist)
    if not doc:
        return []
    pending: list[str] = []
    for step in doc.get("steps", []) or []:
        if not isinstance(step, dict):
            continue
        if str(step.get("status", "pending")).lower() != "completed":
            title = str(step.get("title") or step.get("id") or "step")
            pending.append(title)
    return pending


def inventory_yaml_missing_paths(root: Path, inventory_yaml: Path) -> list[str]:
    doc = _load_yaml(inventory_yaml)
    if not doc:
        return []
    missing: list[str] = []
    for key in ("coordination", "protocols"):
        entries = doc.get(key, [])
        if not isinstance(entries, list):
            continue
        for rel in entries:
            path = root / str(rel).replace("\\", "/")
            if not path.is_file():
                missing.append(str(rel))
    return missing
