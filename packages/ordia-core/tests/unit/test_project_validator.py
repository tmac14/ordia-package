"""Additional unit tests for ordia.validator.project helpers."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from ordia.config import load_ordia_config
from ordia.validator.common import Validation
from ordia.validator.project import (
    ProjectValidationOptions,
    existing_repo_path,
    load_yaml_file,
    markdown_table_ids,
    validate_project,
    validate_task_runtime_protocol,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]


def test_load_yaml_file_missing(tmp_path: Path) -> None:
    result = Validation()
    data = load_yaml_file(tmp_path / "missing.yaml", tmp_path, result)
    assert data == {}
    assert len(result.errors) == 1


def test_existing_repo_path_glob_pattern(tmp_path: Path) -> None:
    assert existing_repo_path(tmp_path, "docs/*.md") is True
    (tmp_path / "ordia.yaml").write_text("x", encoding="utf-8")
    assert existing_repo_path(tmp_path, "ordia.yaml") is True
    assert existing_repo_path(tmp_path, "missing.yaml") is False


def test_markdown_table_ids(tmp_path: Path) -> None:
    path = tmp_path / "DECISION_LOG.md"
    path.write_text("| ORDIA-D001 | decision |\n| not-id | x |\n", encoding="utf-8")
    ids = markdown_table_ids(path)
    assert "ORDIA-D001" in ids


def test_validate_task_runtime_protocol_legacy_warns() -> None:
    result = Validation()
    validate_task_runtime_protocol(
        "T1",
        {"protocol": "CODEX_IMPLEMENTATION"},
        result,
    )
    assert len(result.warnings) == 1


def test_validate_task_runtime_protocol_invalid_runtime() -> None:
    result = Validation()
    validate_task_runtime_protocol(
        "T1",
        {"runtime": "INVALID", "protocol": "IMPLEMENTATION"},
        result,
    )
    assert any("invalid runtime" in err for err in result.errors)


def test_validate_task_runtime_protocol_missing_fields() -> None:
    result = Validation()
    validate_task_runtime_protocol("T1", {}, result)
    assert any("missing runtime" in err for err in result.errors)


def test_greenfield_strict_profile_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        init = subprocess.run(
            [*CLI_CMD, "init", "--directory", str(target), "--profile", "strict-prof"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert init.returncode == 0, init.stderr or init.stdout
        config = load_ordia_config(target)
        assert config is not None
        result = validate_project(
            target,
            config,
            ProjectValidationOptions(strict_profile=True, session_profile="other-profile"),
        )
        assert any("does not match" in err for err in result.errors)


def test_validate_project_invalid_registry_task() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        init = subprocess.run(
            [*CLI_CMD, "init", "--directory", str(target), "--profile", "bad-reg"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert init.returncode == 0, init.stderr or init.stdout
        config = load_ordia_config(target)
        assert config is not None
        registry_path = config.task_registry_path
        registry_path.write_text(
            "tasks:\n  - status: IN_FLIGHT\nqueues: {}\n",
            encoding="utf-8",
        )
        result = validate_project(target, config)
        assert any("must be a mapping with an id" in err for err in result.errors)
