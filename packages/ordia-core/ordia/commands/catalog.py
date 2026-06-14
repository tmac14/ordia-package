"""Load and validate npm command catalogs against package.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ordia.config import OrdiaConfig, resolve_control_relative
from ordia.commands.schema import validate_catalog_structure

EXCLUDED_SCRIPTS = frozenset({"help", "help:validate", "help:list"})


def resolve_catalog_paths(
    root: Path,
    config: OrdiaConfig | None = None,
    *,
    catalog: str | None = None,
    npm_package: str | None = None,
) -> tuple[Path, Path]:
    if config is not None:
        catalog_path = (
            config.commands_catalog_path()
            if catalog is None
            else _resolve_catalog_override(root, config, catalog)
        )
        npm_rel = npm_package or config.commands_npm_package or "package.json"
        if catalog_path is None:
            control_root = config.control_root
            catalog_path = control_root / "commands.catalog.json"
    else:
        catalog_path = root / (catalog or "docs/control/commands.catalog.json")
        npm_rel = npm_package or "package.json"
    return catalog_path, root / npm_rel


def _resolve_catalog_override(root: Path, config: OrdiaConfig, catalog: str) -> Path:
    return resolve_control_relative(config.control_root, root, catalog)


def load_catalog(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("catalog must be a JSON object")
    return data


def load_package_scripts(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
    if not isinstance(scripts, dict):
        return {}
    return {str(key): str(value) for key, value in scripts.items()}


def collect_command_names(catalog: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for section in catalog.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        for cmd in section.get("commands", []) or []:
            if isinstance(cmd, dict) and cmd.get("name"):
                names.append(str(cmd["name"]))
    return names


def collect_command_map(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for section in catalog.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        for cmd in section.get("commands", []) or []:
            if isinstance(cmd, dict) and cmd.get("name"):
                mapping[str(cmd["name"])] = {**cmd, "section": section}
    return mapping


def validate_catalog_sync(
    root: Path,
    catalog_path: Path | None = None,
    package_path: Path | None = None,
    *,
    config: OrdiaConfig | None = None,
) -> tuple[list[str], int]:
    """Return (errors, command_count)."""
    if catalog_path is None or package_path is None:
        catalog_path, package_path = resolve_catalog_paths(root, config)

    errors: list[str] = []
    if not catalog_path.is_file():
        errors.append(f"commands catalog missing: {catalog_path.relative_to(root)}")
        return errors, 0
    if not package_path.is_file():
        errors.append(f"npm package file missing: {package_path.relative_to(root)}")
        return errors, 0

    try:
        catalog = load_catalog(catalog_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"could not load catalog: {exc}")
        return errors, 0

    errors.extend(validate_catalog_structure(catalog))
    catalog_names = collect_command_names(catalog)
    catalog_set = set(catalog_names)

    try:
        scripts = load_package_scripts(package_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"could not load package.json: {exc}")
        return errors, 0

    for script in scripts:
        if script in EXCLUDED_SCRIPTS:
            continue
        if script not in catalog_set:
            errors.append(f'script "{script}" in package.json not documented in catalog')

    for name in catalog_names:
        if name not in scripts:
            errors.append(f'catalog entry "{name}" not found in package.json scripts')

    return errors, len(catalog_names)


def seed_catalog_from_package(
    root: Path,
    catalog_path: Path,
    package_path: Path,
    *,
    profile: str = "default",
) -> int:
    """Create or update commands.catalog.json from package.json scripts."""
    scripts = load_package_scripts(package_path)
    commands = []
    for name in sorted(scripts):
        if name in EXCLUDED_SCRIPTS:
            continue
        commands.append(
            {
                "name": name,
                "description": f"npm script `{name}` (seeded from package.json)",
                "command": f"npm run {name}",
            }
        )
    catalog: dict[str, Any] = {
        "meta": {"version": 1, "profile": profile},
        "sections": [
            {
                "id": "root",
                "title": "Root scripts",
                "commands": commands,
            }
        ],
        "quickFlows": [],
    }
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(commands)


def seed_pip_catalog_stub(
    root: Path,
    catalog_path: Path,
    *,
    profile: str = "default",
) -> int:
    """Write pip-first commands.catalog.json when no package.json is present."""
    catalog: dict[str, Any] = {
        "meta": {"version": 1, "profile": profile, "generatedBy": "ordia init (pip-first stub)"},
        "sections": [
            {
                "id": "ordia-cli",
                "title": "Ordia CLI (pip)",
                "notes": [
                    "Primary validation: ordia validate --project",
                    "Optional npm wrappers can be added to package.json and synced with ordia init --sync-commands",
                ],
                "commands": [
                    {
                        "name": "ordia:doctor",
                        "description": "Check Ordia setup, hooks, and dependencies",
                        "command": "ordia doctor",
                    },
                    {
                        "name": "ordia:validate",
                        "description": "Validate manifest and control-plane registries",
                        "command": "ordia validate --project",
                    },
                    {
                        "name": "ordia:task-summary",
                        "description": "Summarize in-flight tasks, active state, and locks",
                        "command": "ordia task summary",
                    },
                    {
                        "name": "ordia:task-transition",
                        "description": "Atomically update task status, queues, and ORCHESTRATION_STATE",
                        "command": "ordia task transition --task <TASK-ID> --status <STATUS>",
                    },
                    {
                        "name": "ordia:prompt-recover",
                        "description": "Emit recovery bootstrap prompt block",
                        "command": "ordia prompt emit --intent recover",
                    },
                ],
            }
        ],
        "quickFlows": [
            {"goal": "Bootstrap recovery", "command": "ordia prompt emit --intent recover"},
            {"goal": "Validate control plane", "command": "ordia validate --project"},
        ],
        "workflowIntents": [],
    }
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(catalog["sections"][0]["commands"])
