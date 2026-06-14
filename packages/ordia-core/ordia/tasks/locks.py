"""Task lock management in TASK_REGISTRY.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from ordia.config import OrdiaConfig, load_ordia_config
from ordia.validator.common import Validation
from ordia.validator.project import load_yaml_file


@dataclass
class LockResult:
    ok: bool
    task_id: str
    path: str
    action: str
    locks: list[dict[str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False


def _dump_yaml(data: dict[str, Any]) -> str:
    import yaml

    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def _load_registry(root: Path, cfg: OrdiaConfig) -> tuple[dict[str, Any], Validation]:
    validation = Validation()
    registry = load_yaml_file(cfg.task_registry_path, root, validation)
    return registry, validation


def list_locks(root: Path, *, task_id: str | None = None) -> LockResult:
    cfg = load_ordia_config(root)
    if cfg is None:
        return LockResult(False, task_id or "", "list", errors=["ordia.yaml missing or invalid"])
    registry, validation = _load_registry(root, cfg)
    if validation.errors:
        return LockResult(False, task_id or "", "list", errors=list(validation.errors))
    locks = registry.get("active_locks", registry.get("locks", []))
    if not isinstance(locks, list):
        locks = []
    rows: list[dict[str, str]] = []
    for lock in locks:
        if not isinstance(lock, dict):
            continue
        holder = str(lock.get("task_id", lock.get("holder", "")))
        if task_id and holder != task_id:
            continue
        rows.append(
            {
                "path": str(lock.get("path", "")),
                "task_id": holder,
                "holder": str(lock.get("holder", holder)),
                "reason": str(lock.get("reason", "")),
            }
        )
    return LockResult(ok=True, task_id=task_id or "", path="", action="list", locks=rows)


def add_lock(
    root: Path,
    *,
    task_id: str,
    path: str,
    reason: str = "",
    holder: str | None = None,
    dry_run: bool = False,
) -> LockResult:
    cfg = load_ordia_config(root)
    if cfg is None:
        return LockResult(False, task_id, path, "add", errors=["ordia.yaml missing or invalid"])
    registry, validation = _load_registry(root, cfg)
    if validation.errors:
        return LockResult(False, task_id, path, "add", errors=list(validation.errors))
    tasks = registry.get("tasks", [])
    known = {str(task.get("id")) for task in tasks if isinstance(task, dict) and task.get("id")}
    if task_id not in known:
        return LockResult(False, task_id, path, "add", errors=[f"Unknown task id: {task_id}"])
    key = "active_locks" if "active_locks" in registry else "locks"
    locks = registry.get(key, [])
    if not isinstance(locks, list):
        locks = []
    normalized = path.strip().replace("\\", "/")
    for lock in locks:
        if isinstance(lock, dict) and str(lock.get("path", "")).strip() == normalized:
            return LockResult(
                False,
                task_id,
                path,
                "add",
                errors=[f"Lock already exists for path {normalized!r}"],
            )
    entry = {
        "path": normalized,
        "task_id": task_id,
        "holder": holder or task_id,
        "reason": reason or "parallel-safety",
    }
    locks.append(entry)
    registry[key] = locks
    registry["updated_at"] = date.today().isoformat()
    if dry_run:
        return LockResult(True, task_id, path, "add", locks=[entry], dry_run=True)
    cfg.task_registry_path.write_text(_dump_yaml(registry), encoding="utf-8")
    return LockResult(True, task_id, path, "add", locks=[entry])


def release_lock(
    root: Path,
    *,
    task_id: str,
    path: str,
    dry_run: bool = False,
) -> LockResult:
    cfg = load_ordia_config(root)
    if cfg is None:
        return LockResult(False, task_id, path, "release", errors=["ordia.yaml missing or invalid"])
    registry, validation = _load_registry(root, cfg)
    if validation.errors:
        return LockResult(False, task_id, path, "release", errors=list(validation.errors))
    key = "active_locks" if "active_locks" in registry else "locks"
    locks = registry.get(key, [])
    if not isinstance(locks, list):
        locks = []
    normalized = path.strip().replace("\\", "/")
    kept: list[dict[str, Any]] = []
    removed = False
    for lock in locks:
        if not isinstance(lock, dict):
            continue
        lock_path = str(lock.get("path", "")).strip()
        holder = str(lock.get("task_id", lock.get("holder", "")))
        if lock_path == normalized and holder == task_id:
            removed = True
            continue
        kept.append(lock)
    if not removed:
        return LockResult(False, task_id, path, "release", errors=[f"No lock for {normalized!r} on task {task_id}"])
    registry[key] = kept
    registry["updated_at"] = date.today().isoformat()
    if dry_run:
        return LockResult(True, task_id, path, "release", dry_run=True)
    cfg.task_registry_path.write_text(_dump_yaml(registry), encoding="utf-8")
    return LockResult(True, task_id, path, "release")


def format_lock_text(result: LockResult) -> str:
    if result.errors:
        return "Lock operation failed:\n" + "\n".join(f"- {err}" for err in result.errors)
    if result.action == "list":
        if not result.locks:
            return "No active locks."
        lines = ["Active locks:"]
        for lock in result.locks:
            lines.append(
                f"- {lock.get('path')} task={lock.get('task_id')} reason={lock.get('reason') or '—'}"
            )
        return "\n".join(lines)
    prefix = "[dry-run] " if result.dry_run else ""
    return f"{prefix}Lock {result.action} OK: task={result.task_id} path={result.path}"
