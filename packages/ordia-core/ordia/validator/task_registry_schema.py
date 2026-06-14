"""JSON Schema validation for TASK_REGISTRY.yaml."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ordia.validator.common import Validation


def schema_path() -> Path:
    return Path(__file__).resolve().parent.parent / "schemas" / "task_registry.schema.json"


def load_schema() -> dict[str, Any]:
    path = schema_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _validate_node(
    value: Any,
    schema: dict[str, Any],
    path: str,
    result: Validation,
) -> None:
    if not schema:
        return

    expected_type = schema.get("type")
    if expected_type:
        if isinstance(expected_type, list):
            if _type_name(value) not in expected_type:
                result.error(f"schema {path}: expected {expected_type}, got {_type_name(value)}")
                return
        elif _type_name(value) != expected_type:
            result.error(f"schema {path}: expected {expected_type}, got {_type_name(value)}")
            return

    if expected_type == "object" and isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    result.error(f"schema {path}: missing required field {key!r}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, subschema in properties.items():
                if key in value and isinstance(subschema, dict):
                    _validate_node(value[key], subschema, f"{path}.{key}", result)
        defs = schema.get("$defs", {})
        for key, item in value.items():
            if key in properties:
                continue
            additional = schema.get("additionalProperties", True)
            if additional is False:
                result.error(f"schema {path}: unexpected field {key!r}")

    if expected_type == "array" and isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_node(item, item_schema, f"{path}[{index}]", result)

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            result.error(f"schema {path}: string shorter than minLength {min_length}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str):
            import re

            if not re.fullmatch(pattern, value):
                result.error(f"schema {path}: value {value!r} does not match pattern {pattern}")
        enum = schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            result.error(f"schema {path}: value {value!r} not in enum {enum}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            result.error(f"schema {path}: value {value} below minimum {minimum}")

    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/$defs/"):
        def_name = ref.split("/")[-1]
        root = load_schema()
        defs = root.get("$defs", {})
        if isinstance(defs, dict) and isinstance(defs.get(def_name), dict):
            _validate_node(value, defs[def_name], path, result)


def validate_task_registry_schema(registry: dict[str, Any], result: Validation) -> None:
    """Validate registry document against bundled TASK_REGISTRY JSON Schema."""
    schema = load_schema()
    if not schema:
        result.warn("TASK_REGISTRY JSON Schema unavailable — skipped structural schema check")
        return
    _validate_node(registry, schema, "TASK_REGISTRY", result)
