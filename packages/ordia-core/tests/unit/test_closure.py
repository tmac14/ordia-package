"""Tests for closure command parsing and allowlist."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ordia.validator.closure import (
    CLOSURE_VALIDATOR_ACTIVE_ENV,
    DEFAULT_CLOSURE_VALIDATOR,
    parse_closure_command,
    run_closure_validator_command,
    validated_task_ids,
    validate_closure_gate,
)
from ordia.validator.common import Validation

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_validated_task_ids_extracts_validated_only() -> None:
    registry = {
        "tasks": [
            {"id": "A", "status": "VALIDATED"},
            {"id": "B", "status": "IN_FLIGHT"},
            {"id": "C", "status": "VALIDATED"},
        ]
    }
    assert validated_task_ids(registry) == ["A", "C"]


def test_parse_closure_command_accepts_npm_run() -> None:
    argv = parse_closure_command("npm run ordia:validate")
    assert argv == ["npm", "run", "ordia:validate"]


def test_parse_closure_command_accepts_ordia_cli() -> None:
    argv = parse_closure_command("ordia validate --project")
    assert argv == ["ordia", "validate", "--project"]


def test_parse_closure_command_rejects_shell_injection() -> None:
    assert parse_closure_command("rm -rf /") is None
    assert parse_closure_command("curl http://evil.example") is None


def test_run_closure_validator_rejects_disallowed() -> None:
    code, detail = run_closure_validator_command("curl evil", REPO_ROOT)
    assert code is None
    assert "allowlisted" in detail


def test_validate_closure_gate_skips_without_validated_tasks() -> None:
    result = Validation()
    with patch("ordia.validator.closure.run_closure_validator_command") as mock_run:
        validate_closure_gate(
            {"tasks": [{"id": "T1", "status": "IN_FLIGHT"}]},
            "",
            "",
            REPO_ROOT,
            result,
        )
    mock_run.assert_not_called()


def test_validate_closure_gate_respects_reentrant_env() -> None:
    result = Validation()
    registry = {"tasks": [{"id": "T1", "status": "VALIDATED"}], "queues": {"in_flight": []}}
    with patch("ordia.validator.closure.run_closure_validator_command") as mock_run:
        with patch.dict("os.environ", {CLOSURE_VALIDATOR_ACTIVE_ENV: "1"}):
            validate_closure_gate(registry, "T1", "", REPO_ROOT, result)
    mock_run.assert_not_called()


def test_default_closure_validator_is_ordia_validate() -> None:
    assert DEFAULT_CLOSURE_VALIDATOR == "npm run ordia:validate"
