"""Manifest-driven control document path resolution."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ordia.config import OrdiaConfig


def control_root_from(root: Path, config: OrdiaConfig | None = None) -> Path:
    if config is not None:
        return config.control_root
    manifest = root / "ordia.yaml"
    if manifest.is_file():
        try:
            from ordia.config import load_ordia_config

            loaded = load_ordia_config(root)
            if loaded is not None:
                return loaded.control_root
        except ImportError:
            pass
    if (root / "docs" / "control").is_dir():
        return root / "docs" / "control"
    if (root / "docs" / "coordination").is_dir():
        return root / "docs" / "coordination"
    return root / "docs" / "control"


def resolve_control_doc(
    root: Path,
    basename: str,
    *,
    config: OrdiaConfig | None = None,
    control_root: Path | None = None,
) -> Path | None:
    """Resolve a control document by basename (greenfield + legacy layouts)."""
    base = control_root or control_root_from(root, config)
    candidates = [
        base / "protocols" / f"{basename}.md",
        base / f"{basename}_PROTOCOL.md",
        base / f"{basename}.md",
    ]
    if basename == "RECOVERY_RUNBOOK":
        candidates.insert(1, base / "CONTROL_PLANE_RECOVERY_RUNBOOK.md")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def basename_from_protocol_path(path: str) -> str | None:
    """Extract protocol basename from a registry path string."""
    name = Path(path).name
    if name == "CONTROL_PLANE_RECOVERY_RUNBOOK.md":
        return "RECOVERY_RUNBOOK"
    if name.endswith("_PROTOCOL.md"):
        return name[: -len("_PROTOCOL.md")]
    if name.endswith(".md"):
        return name[: -len(".md")]
    return None


def resolve_registry_protocol_path(root: Path, path: str, *, config: OrdiaConfig | None = None) -> Path | None:
    """Return existing path or resolve via basename fallback."""
    direct = root / path
    if direct.is_file():
        return direct
    basename = basename_from_protocol_path(path)
    if basename is None:
        return None
    return resolve_control_doc(root, basename, config=config)
