"""Tests for commands.catalog.v1 structural validation."""

from __future__ import annotations

from ordia.commands.schema import validate_catalog_structure


def test_valid_minimal_catalog() -> None:
    catalog = {
        "meta": {"version": "1"},
        "sections": [
            {
                "id": "ordia",
                "commands": [{"name": "ordia:validate", "description": "Validate project"}],
            }
        ],
    }
    assert validate_catalog_structure(catalog) == []


def test_rejects_non_object_root() -> None:
    errors = validate_catalog_structure([])  # type: ignore[arg-type]
    assert any("object" in err for err in errors)


def test_rejects_missing_sections() -> None:
    errors = validate_catalog_structure({"meta": {}})
    assert any("sections is required" in err for err in errors)


def test_rejects_duplicate_command_names() -> None:
    catalog = {
        "sections": [
            {
                "id": "a",
                "commands": [
                    {"name": "dup", "description": "one"},
                    {"name": "dup", "description": "two"},
                ],
            }
        ]
    }
    errors = validate_catalog_structure(catalog)
    assert any("duplicate" in err for err in errors)


def test_rejects_missing_description() -> None:
    catalog = {
        "sections": [
            {
                "id": "a",
                "commands": [{"name": "ordia:doctor"}],
            }
        ]
    }
    errors = validate_catalog_structure(catalog)
    assert any("missing description" in err for err in errors)


def test_rejects_invalid_quick_flows_type() -> None:
    catalog = {"sections": [], "quickFlows": "not-a-list"}
    errors = validate_catalog_structure(catalog)
    assert any("quickFlows" in err for err in errors)
