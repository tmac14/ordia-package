"""Tests for profile validator plugins."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from ordia.config import load_ordia_config
from ordia.plugins.loader import run_profile_validators
from ordia.validator.common import Validation
from ordia.validator.project import ProjectValidationOptions, validate_project

REPO_ROOT = Path(__file__).resolve().parents[4]
CLI_CMD = [sys.executable, "-m", "ordia.cli"]


def test_run_profile_validators_no_plugins() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        init = subprocess.run(
            [*CLI_CMD, "init", "--directory", str(target), "--profile", "no-plugins"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert init.returncode == 0, init.stderr or init.stdout
        config = load_ordia_config(target)
        assert config is not None
        result = Validation()
        run_profile_validators(target, config, result, options=ProjectValidationOptions())
        assert result.errors == []
        assert result.warnings == []


def test_run_profile_validators_executes_matching_plugin() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        init = subprocess.run(
            [*CLI_CMD, "init", "--directory", str(target), "--profile", "plugin-demo"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert init.returncode == 0, init.stderr or init.stdout
        config = load_ordia_config(target)
        assert config is not None
        result = Validation()

        def _plugin(
            root: Path,
            cfg: object,
            validation: Validation,
            options: ProjectValidationOptions,
        ) -> None:
            validation.warn("plugin-demo executed")

        with patch(
            "ordia.plugins.loader._iter_entry_points",
            return_value=[("plugin-demo", "fake:plugin")],
        ):
            with patch("ordia.plugins.loader._load_callable", return_value=_plugin):
                run_profile_validators(target, config, result, options=ProjectValidationOptions())
        assert any("plugin-demo executed" in w for w in result.warnings)


def test_plugin_load_failure_warns() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        init = subprocess.run(
            [*CLI_CMD, "init", "--directory", str(target), "--profile", "bad-plugin"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert init.returncode == 0, init.stderr or init.stdout
        config = load_ordia_config(target)
        assert config is not None
        result = Validation()
        with patch(
            "ordia.plugins.loader._iter_entry_points",
            return_value=[("bad-plugin", "missing:plugin")],
        ):
            with patch("ordia.plugins.loader._load_callable", return_value=None):
                run_profile_validators(target, config, result, options=ProjectValidationOptions())
        assert any("could not be loaded" in w for w in result.warnings)


def test_plugin_exception_strict_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        init = subprocess.run(
            [*CLI_CMD, "init", "--directory", str(target), "--profile", "boom"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert init.returncode == 0, init.stderr or init.stdout
        config = load_ordia_config(target)
        assert config is not None
        result = Validation()

        def _boom(*_args, **_kwargs) -> None:
            raise RuntimeError("boom")

        with patch(
            "ordia.plugins.loader._iter_entry_points",
            return_value=[("boom", "fake:plugin")],
        ):
            with patch("ordia.plugins.loader._load_callable", return_value=_boom):
                run_profile_validators(
                    target,
                    config,
                    result,
                    options=ProjectValidationOptions(),
                    strict=True,
                )
        assert any("failed" in err for err in result.errors)


def test_validate_project_invokes_plugins() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        init = subprocess.run(
            [*CLI_CMD, "init", "--directory", str(target), "--profile", "via-project"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert init.returncode == 0, init.stderr or init.stdout
        config = load_ordia_config(target)
        assert config is not None

        def _plugin(
            root: Path,
            cfg: object,
            validation: Validation,
            options: ProjectValidationOptions,
        ) -> None:
            validation.warn("via validate_project")

        with patch(
            "ordia.plugins.loader._iter_entry_points",
            return_value=[("via-project", "fake:plugin")],
        ):
            with patch("ordia.plugins.loader._load_callable", return_value=_plugin):
                result = validate_project(target, config, ProjectValidationOptions())
        assert any("via validate_project" in w for w in result.warnings)
