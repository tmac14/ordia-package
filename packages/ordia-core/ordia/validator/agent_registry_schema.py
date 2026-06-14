"""JSON Schema validation for AGENT_REGISTRY.yaml."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ordia.validator.common import Validation
from ordia.validator.task_registry_schema import _validate_node


def schema_path() -> Path:
    return Path(__file__).resolve().parent.parent / "schemas" / "agent_registry.schema.json"


def load_schema() -> dict[str, Any]:
    path = schema_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def validate_agent_registry_schema(agent_registry: dict[str, Any], result: Validation) -> None:
    """Validate agent registry document against bundled JSON Schema."""
    schema = load_schema()
    if not schema:
        result.warn("AGENT_REGISTRY JSON Schema unavailable — skipped structural schema check")
        return
    _validate_node(agent_registry, schema, "AGENT_REGISTRY", result)
