"""Tests for ordia.bootstrap repo root discovery."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ordia.bootstrap import ensure_ordia_core, ordia_core_src, repo_root_from_core


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


def test_ensure_ordia_core_adds_to_path(repo_root: Path, core_root: Path) -> None:
    original = os.getcwd()
    original_path = list(sys.path)
    try:
        os.chdir(repo_root)
        core_str = str(core_root)
        sys.path[:] = [p for p in sys.path if p != core_str]
        result = ensure_ordia_core()
        assert result is not None
        assert result.resolve() == core_root.resolve()
        assert core_str in sys.path
    finally:
        sys.path[:] = original_path
        os.chdir(original)


def test_ordia_core_src_none_outside_monorepo(tmp_path: Path) -> None:
    original = os.getcwd()
    try:
        os.chdir(tmp_path)
        assert ordia_core_src() is None
        assert repo_root_from_core() is None
        assert ensure_ordia_core() is None
    finally:
        os.chdir(original)
