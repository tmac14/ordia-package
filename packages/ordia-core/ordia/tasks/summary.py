"""Task registry and orchestration state summaries."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ordia.config import OrdiaConfig, load_ordia_config
from ordia.validator.common import Validation
from ordia.validator.project import load_yaml_file


def _state_field(text: str, field: str) -> str | None:
    match = re.search(rf"- {re.escape(field)}: `([^`]+)`", text)
    return match.group(1) if match else None


def _state_plain_field(text: str, field: str) -> str | None:
    match = re.search(rf"- {re.escape(field)}:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def read_state_summary(state_path: Path) -> dict[str, str | None]:
    if not state_path.is_file():
        return {}
    text = state_path.read_text(encoding="utf-8")
    active_task = _state_field(text, "Active task ID")
    if active_task is None:
        match = re.search(r"- Active task ID: `([^`]+)`", text)
        active_task = match.group(1) if match else None
    return {
        "recovery_status": _state_field(text, "Recovery status"),
        "control_plane_runtime": _state_field(text, "control_plane_runtime"),
        "active_protocol": _state_field(text, "active_protocol"),
        "session_mode": _state_field(text, "session_mode"),
        "handoff_from": _state_field(text, "handoff_from"),
        "active_task_id": active_task,
        "active_objective": _state_plain_field(text, "Active objective"),
        "waiting_for": _state_plain_field(text, "Waiting for"),
        "next_safe_action": _state_plain_field(text, "Next safe action"),
    }


def _task_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    tasks = registry.get("tasks", [])
    if isinstance(tasks, list):
        for task in tasks:
            if isinstance(task, dict) and task.get("id"):
                mapping[str(task["id"])] = task
    return mapping


def _active_locks(registry: dict[str, Any], active_task_id: str | None) -> list[dict[str, str]]:
    locks = registry.get("locks", [])
    if not isinstance(locks, list) or not active_task_id or active_task_id in {"NONE", "NONE_SELECTED_FOR_NEXT_TASK"}:
        return []
    rows: list[dict[str, str]] = []
    for lock in locks:
        if not isinstance(lock, dict):
            continue
        holder = str(lock.get("task_id", lock.get("holder", "")))
        if holder == active_task_id:
            rows.append(
                {
                    "path": str(lock.get("path", "")),
                    "task_id": holder,
                    "reason": str(lock.get("reason", "")),
                }
            )
    return rows


def _packet_next_safe_action(packet_path: Path) -> str | None:
    if not packet_path.is_file():
        return None
    text = packet_path.read_text(encoding="utf-8")
    match = re.search(r"## Next Safe Action\s*\n+(.+?)(?:\n## |\Z)", text, re.DOTALL)
    if not match:
        return None
    body = match.group(1).strip()
    return body or None


def build_task_summary(root: Path, config: OrdiaConfig | None = None) -> dict[str, Any]:
    root = root.resolve()
    cfg = config or load_ordia_config(root)
    if cfg is None:
        raise FileNotFoundError("ordia.yaml missing or invalid")

    validation = Validation()
    registry = load_yaml_file(cfg.task_registry_path, root, validation)
    state = read_state_summary(cfg.state_path)
    task_map = _task_by_id(registry)
    queues = registry.get("queues", {}) if isinstance(registry.get("queues"), dict) else {}

    in_flight: list[dict[str, Any]] = []
    for task_id in queues.get("in_flight", []) or []:
        tid = str(task_id)
        task = task_map.get(tid, {})
        in_flight.append(
            {
                "id": tid,
                "status": str(task.get("status", "UNKNOWN")),
                "owner": task.get("owner"),
                "runtime": task.get("runtime"),
                "protocol": task.get("protocol"),
                "planned_write_paths": task.get("planned_write_paths", []),
            }
        )

    active_id = state.get("active_task_id")
    active_task: dict[str, Any] | None = None
    packet_next: str | None = None
    if active_id and active_id not in {"NONE", "NONE_SELECTED_FOR_NEXT_TASK"}:
        active_task = dict(task_map.get(str(active_id), {}))
        active_task.setdefault("id", str(active_id))
        packet_path = cfg.task_packets_dir / f"{active_id}.md"
        packet_next = _packet_next_safe_action(packet_path)

    locks = _active_locks(registry, str(active_id) if active_id else None)

    return {
        "profile": cfg.profile,
        "state": state,
        "queues": {key: list(value or []) for key, value in queues.items() if isinstance(value, list)},
        "in_flight": in_flight,
        "active_task": active_task,
        "active_locks": locks,
        "packet_next_safe_action": packet_next,
        "registry_updated_at": registry.get("updated_at"),
        "load_errors": list(validation.errors),
    }


def format_task_summary_text(summary: dict[str, Any]) -> str:
    lines = [
        "Ordia task summary",
        f"- profile: {summary.get('profile')}",
        f"- registry updated_at: {summary.get('registry_updated_at')}",
    ]
    state = summary.get("state", {})
    if state:
        lines.append(f"- recovery_status: {state.get('recovery_status')}")
        lines.append(f"- control_plane_runtime: {state.get('control_plane_runtime')}")
        lines.append(f"- active_protocol: {state.get('active_protocol')}")
        lines.append(f"- session_mode: {state.get('session_mode')}")
        lines.append(f"- active_task_id: {state.get('active_task_id')}")
        if state.get("next_safe_action"):
            lines.append(f"- state next_safe_action: {state.get('next_safe_action')}")

    in_flight = summary.get("in_flight", [])
    if in_flight:
        lines.append("- in_flight:")
        for row in in_flight:
            lines.append(f"  - {row['id']} ({row.get('status')}) owner={row.get('owner')}")
    else:
        lines.append("- in_flight: (none)")

    locks = summary.get("active_locks", [])
    if locks:
        lines.append("- active_locks:")
        for lock in locks:
            lines.append(f"  - {lock.get('path')} ({lock.get('reason')})")

    if summary.get("packet_next_safe_action"):
        lines.append(f"- packet next_safe_action: {summary['packet_next_safe_action']}")

    if summary.get("load_errors"):
        lines.append("- errors:")
        for err in summary["load_errors"]:
            lines.append(f"  - {err}")

    return "\n".join(lines)
