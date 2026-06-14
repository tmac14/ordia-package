"""JSON Schema validation for ordia.yaml manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ordia.validator.common import Validation
from ordia.validator.task_registry_schema import _validate_node


def schema_path() -> Path:
    return Path(__file__).resolve().parent.parent / "schemas" / "ordia.manifest.schema.json"


def load_schema() -> dict[str, Any]:
    path = schema_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def validate_manifest_schema(raw: dict[str, Any], result: Validation) -> None:
    """Validate loaded ordia.yaml dict against bundled JSON Schema."""
    schema = load_schema()
    if not schema:
        result.warn("ordia.yaml JSON Schema unavailable — skipped structural schema check")
        return
    _validate_node(raw, schema, "ordia.yaml", result)
