"""Atomic task status and queue transitions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from ordia.config import OrdiaConfig, load_ordia_config
from ordia.validator.common import DEFAULT_ALLOWED_STATUSES, QUEUE_STATUS, Validation
from ordia.validator.project import load_yaml_file

QUEUE_NAMES = tuple(QUEUE_STATUS.keys())


def queue_for_status(status: str) -> str | None:
    for queue, allowed in QUEUE_STATUS.items():
        if status in allowed:
            return queue
    return None


def _task_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    tasks = registry.get("tasks", [])
    if isinstance(tasks, list):
        for task in tasks:
            if isinstance(task, dict) and task.get("id"):
                mapping[str(task["id"])] = task
    return mapping


def _remove_from_queues(queues: dict[str, Any], task_id: str) -> list[str]:
    removed: list[str] = []
    for queue in QUEUE_NAMES:
        entries = queues.get(queue, [])
        if not isinstance(entries, list):
            continue
        if task_id in entries:
            removed.append(queue)
            queues[queue] = [item for item in entries if item != task_id]
    return removed


def _format_queue_list(task_ids: list[str]) -> str:
    return ", ".join(task_ids) if task_ids else "none"


def _sync_state_sections(state_text: str, registry: dict[str, Any]) -> str:
    queues = registry.get("queues", {})
    if not isinstance(queues, dict):
        queues = {}

    replacements = {
        r"(## 1\. In-flight summary\s*\n\s*- Tasks in `queues\.in_flight`:)\s*.+$": (
            rf"\1 {_format_queue_list(list(queues.get('in_flight', []) or []))}"
        ),
        r"(- `waiting_for_user_decision`:)\s*.+$": (
            rf"\1 {_format_queue_list(list(queues.get('waiting_for_user_decision', []) or []))}"
        ),
        r"(- `waiting_for_agent_report`:)\s*.+$": (
            rf"\1 {_format_queue_list(list(queues.get('waiting_for_agent_report', []) or []))}"
        ),
        r"(- `model_tier_pending`:)\s*.+$": (
            rf"\1 {_format_queue_list(list(queues.get('model_tier_pending', []) or []))}"
        ),
        r"(- `validation_pending`:)\s*.+$": (
            rf"\1 {_format_queue_list(list(queues.get('validation_pending', []) or []))}"
        ),
    }
    text = state_text
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text, count=1, flags=re.MULTILINE)
    return text


def _update_state_field(text: str, field: str, value: str, *, backtick: bool = True) -> str:
    if backtick:
        replacement = f"- {field}: `{value}`"
        pattern = rf"- {re.escape(field)}: `[^`]*`"
    else:
        replacement = f"- {field}: {value}"
        pattern = rf"- {re.escape(field)}:\s*.+$"
    if re.search(pattern, text, re.MULTILINE):
        return re.sub(pattern, replacement, text, count=1, flags=re.MULTILINE)
    return text


def _update_last_updated(text: str, stamp: str) -> str:
    pattern = r"\*\*Last updated:\*\*\s*.+$"
    replacement = f"**Last updated:** {stamp}"
    if re.search(pattern, text, re.MULTILINE):
        return re.sub(pattern, replacement, text, count=1, flags=re.MULTILINE)
    return text


@dataclass
class TransitionRequest:
    task_id: str
    status: str
    set_active: bool = False
    clear_active: bool = False
    next_safe_action: str | None = None
    waiting_for: str | None = None


@dataclass
class TransitionResult:
    ok: bool
    task_id: str
    previous_status: str | None = None
    new_status: str | None = None
    removed_queues: list[str] = field(default_factory=list)
    target_queue: str | None = None
    registry_updated_at: str | None = None
    state_updated_at: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dry_run: bool = False


def plan_transition(
    root: Path,
    request: TransitionRequest,
    *,
    config: OrdiaConfig | None = None,
) -> TransitionResult:
    root = root.resolve()
    cfg = config or load_ordia_config(root)
    result = TransitionResult(ok=False, task_id=request.task_id)
    if cfg is None:
        result.errors.append("ordia.yaml missing or invalid")
        return result

    validation = Validation()
    registry = load_yaml_file(cfg.task_registry_path, root, validation)
    if validation.errors:
        result.errors.extend(validation.errors)
        return result

    task_map = _task_by_id(registry)
    task_id = request.task_id.strip()
    task = task_map.get(task_id)
    if task is None:
        result.errors.append(f"Unknown task id: {task_id}")
        return result

    allowed_statuses = set(registry.get("allowed_statuses") or DEFAULT_ALLOWED_STATUSES)
    new_status = request.status.strip().upper()
    if new_status not in allowed_statuses:
        result.errors.append(f"Unsupported status {new_status!r}")
        return result

    queues = registry.setdefault("queues", {})
    if not isinstance(queues, dict):
        result.errors.append("TASK_REGISTRY queues must be a mapping")
        return result
    for queue in QUEUE_NAMES:
        queues.setdefault(queue, [])

    previous_status = str(task.get("status") or "")
    result.previous_status = previous_status
    result.new_status = new_status

    removed = _remove_from_queues(queues, task_id)
    result.removed_queues = removed

    target_queue = queue_for_status(new_status)
    result.target_queue = target_queue
    if target_queue:
        entries = queues.setdefault(target_queue, [])
        if not isinstance(entries, list):
            result.errors.append(f"Queue {target_queue} must be a list")
            return result
        if task_id not in entries:
            entries.append(task_id)

    task["status"] = new_status
    if request.next_safe_action:
        task["next_safe_action"] = request.next_safe_action

    stamp = date.today().isoformat()
    result.registry_updated_at = stamp
    result.state_updated_at = stamp

    if not cfg.state_path.is_file():
        result.errors.append("ORCHESTRATION_STATE.md missing")
        return result

    state_text = cfg.state_path.read_text(encoding="utf-8")
    active_match = re.search(r"- Active task ID: `([^`]+)`", state_text)
    active_id = active_match.group(1) if active_match else None

    if request.set_active:
        state_text = _update_state_field(state_text, "Active task ID", task_id)
    elif request.clear_active:
        state_text = _update_state_field(state_text, "Active task ID", "NONE")
    elif active_id == task_id and target_queue != "in_flight":
        result.warnings.append(
            f"{task_id} left in_flight but remains Active task ID — consider --clear-active"
        )

    if request.next_safe_action:
        state_text = _update_state_field(
            state_text, "Next safe action", request.next_safe_action, backtick=False
        )
    if request.waiting_for:
        state_text = _update_state_field(
            state_text, "Waiting for", request.waiting_for, backtick=False
        )

    state_text = _update_last_updated(state_text, stamp)
    state_text = _sync_state_sections(state_text, registry)

    result.ok = True
    result._registry = registry  # type: ignore[attr-defined]
    result._state_text = state_text  # type: ignore[attr-defined]
    result._cfg = cfg  # type: ignore[attr-defined]
    return result


def apply_transition(
    root: Path,
    request: TransitionRequest,
    *,
    config: OrdiaConfig | None = None,
    dry_run: bool = False,
) -> TransitionResult:
    plan = plan_transition(root, request, config=config)
    plan.dry_run = dry_run
    if not plan.ok or dry_run:
        return plan

    cfg: OrdiaConfig = plan._cfg  # type: ignore[attr-defined]
    registry: dict[str, Any] = plan._registry  # type: ignore[attr-defined]
    state_text: str = plan._state_text  # type: ignore[attr-defined]

    try:
        import yaml
    except ImportError:
        plan.ok = False
        plan.errors.append("pyyaml required for task transition")
        return plan

    registry["updated_at"] = plan.registry_updated_at
    registry_path = cfg.task_registry_path
    state_path = cfg.state_path

    registry_tmp = registry_path.with_suffix(".yaml.tmp")
    state_tmp = state_path.with_suffix(".md.tmp")
    registry_tmp.write_text(
        yaml.safe_dump(registry, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    state_tmp.write_text(state_text, encoding="utf-8")
    registry_tmp.replace(registry_path)
    state_tmp.replace(state_path)
    return plan


def format_transition_text(result: TransitionResult) -> str:
    lines = [
        "Ordia task transition",
        f"- task: {result.task_id}",
        f"- status: {result.previous_status} -> {result.new_status}",
    ]
    if result.removed_queues:
        lines.append(f"- removed from queues: {', '.join(result.removed_queues)}")
    if result.target_queue:
        lines.append(f"- added to queue: {result.target_queue}")
    if result.registry_updated_at:
        lines.append(f"- registry updated_at: {result.registry_updated_at}")
    if result.dry_run:
        lines.append("- dry_run: true (no files written)")
    for warning in result.warnings:
        lines.append(f"- warning: {warning}")
    for error in result.errors:
        lines.append(f"- error: {error}")
    lines.append(f"- result: {'OK' if result.ok else 'FAIL'}")
    return "\n".join(lines)
