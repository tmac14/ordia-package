"""Tests for ordia.bootstrap repo root discovery."""

from __future__ import annotations

import os
from pathlib import Path

from ordia.bootstrap import repo_root_from_core


def test_repo_root_from_core_finds_monorepo(repo_root: Path, core_root: Path) -> None:
    assert (core_root / "ordia" / "config.py").is_file()
    original = os.getcwd()
    try:
        os.chdir(repo_root)
        discovered = repo_root_from_core()
        assert discovered is not None
        assert discovered.resolve() == repo_root.resolve()
    finally:
        os.chdir(original)


def test_repo_root_from_core_from_core_directory(repo_root: Path, core_root: Path) -> None:
    original = os.getcwd()
    try:
        os.chdir(core_root)
        discovered = repo_root_from_core()
        assert discovered is not None
        assert discovered.resolve() == repo_root.resolve()
    finally:
        os.chdir(original)
