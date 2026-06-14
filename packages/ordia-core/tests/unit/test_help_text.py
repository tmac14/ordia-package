"""Tests for ordia.commands.help_text formatting."""

from __future__ import annotations

from ordia.commands.help_text import (
    format_command_detail,
    format_help_list,
    format_help_overview,
)


def test_format_help_overview_minimal() -> None:
    text = format_help_overview({})
    assert "Command catalog overview" in text
    assert "ordia help --list" in text


def test_format_help_overview_quick_flows_and_intents() -> None:
    catalog = {
        "quickFlows": [
            {"goal": "Validate", "commands": ["ordia:validate", "ordia:doctor"]},
            {"goal": "Legacy", "command": "build"},
            "ignored",
        ],
        "workflowIntents": [
            {"goal": "Recover", "emitCommand": "ordia prompt emit --intent recover"},
            "ignored",
        ],
        "localUrls": {"docs": "docs/ordia/README.md"},
        "sections": [
            {
                "title": "Ordia core",
                "notes": ["pip install ordia-core"],
                "commands": [
                    {"name": "ordia:doctor", "description": "Health check"},
                    "ignored",
                ],
            },
            "ignored",
        ],
        "desktopCommands": [
            {"name": "desktop:dev", "description": "Run desktop app"},
            "ignored",
        ],
    }
    text = format_help_overview(catalog)
    assert "Validate" in text
    assert "npm run ordia:validate" in text
    assert "Workflow intents" in text
    assert "Recover" in text
    assert "docs/ordia/README.md" in text
    assert "Ordia core" in text
    assert "ordia:doctor" in text
    assert "desktop:dev" in text


def test_format_help_list_includes_desktop() -> None:
    catalog = {
        "sections": [
            {"id": "a", "commands": [{"name": "ordia:validate", "description": "x"}]},
        ],
        "desktopCommands": [{"name": "desktop:build", "description": "y"}],
    }
    names = format_help_list(catalog).splitlines()
    assert "desktop:build" in names
    assert "ordia:validate" in names


def test_format_command_detail_full_entry() -> None:
    catalog = {
        "sections": [
            {
                "id": "ordia",
                "title": "Ordia",
                "commands": [
                    {
                        "name": "ordia:validate",
                        "description": "Validate manifest",
                        "profile": "default",
                        "requires": ["ordia.yaml"],
                        "underlyingScript": "ordia validate",
                        "flags": [
                            {"name": "--project", "description": "Full project", "default": False},
                            "ignored",
                        ],
                        "examples": ["npm run ordia:validate -- --project"],
                        "related": ["ordia:doctor"],
                    }
                ],
            }
        ]
    }
    scripts = {"ordia:validate": "ordia validate"}
    text, code = format_command_detail("ordia:validate", catalog, scripts)
    assert code == 0
    assert "Command: ordia:validate" in text
    assert "Profile:     default" in text
    assert "Requires:    ordia.yaml" in text
    assert "Script:      ordia validate" in text
    assert "--project" in text
    assert "ordia:doctor" in text


def test_format_command_detail_desktop() -> None:
    catalog = {
        "desktopCommands": [
            {
                "name": "desktop:test",
                "description": "Desktop tests",
                "prefix": "apps/desktop",
            }
        ]
    }
    text, code = format_command_detail("desktop:test", catalog, {})
    assert code == 0
    assert "Desktop command: desktop:test" in text
    assert "apps/desktop" in text


def test_format_command_detail_not_found_with_suggestions() -> None:
    catalog = {
        "sections": [
            {
                "id": "a",
                "commands": [
                    {"name": "ordia:validate", "description": "v"},
                    {"name": "ordia:doctor", "description": "d"},
                ],
            }
        ]
    }
    text, code = format_command_detail("ordia:val", catalog, {})
    assert code == 1
    assert 'Command not found: "ordia:val"' in text
    assert "Suggestions:" in text
    assert "ordia:validate" in text
