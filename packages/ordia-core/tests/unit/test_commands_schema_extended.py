"""Tests for ordia.commands.schema validation."""

from __future__ import annotations

from ordia.commands.schema import validate_catalog_structure


def test_validate_catalog_structure_rejects_empty_sections() -> None:
    errors = validate_catalog_structure({})
    assert any("sections" in err.lower() for err in errors)


def test_validate_catalog_structure_rejects_bad_command() -> None:
    catalog = {
        "sections": [
            {
                "id": "a",
                "commands": [{"description": "missing name"}],
            }
        ]
    }
    errors = validate_catalog_structure(catalog)
    assert len(errors) >= 1


def test_validate_catalog_structure_accepts_minimal() -> None:
    catalog = {
        "sections": [
            {
                "id": "ordia",
                "title": "Ordia",
                "commands": [{"name": "ordia:doctor", "description": "Doctor"}],
            }
        ]
    }
    errors = validate_catalog_structure(catalog)
    assert errors == []
