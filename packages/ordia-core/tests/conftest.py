"""Shared pytest fixtures for ordia-core tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Monorepo root (ordia-package)."""
    return Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def core_root() -> Path:
    """packages/ordia-core source tree."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def _ensure_ordia_importable(core_root: Path) -> None:
    core_str = str(core_root)
    if core_str not in sys.path:
        sys.path.insert(0, core_str)


@pytest.fixture
def ordia_cli_cmd() -> list[str]:
    return [sys.executable, "-m", "ordia.cli"]
