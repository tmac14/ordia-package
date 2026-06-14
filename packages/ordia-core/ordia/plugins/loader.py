"""Profile validator plugin loading."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ordia.config import OrdiaConfig
from ordia.validator.common import Validation
from ordia.validator.project import ProjectValidationOptions

logger = logging.getLogger(__name__)

ProfileValidator = Callable[
    [Path, OrdiaConfig, Validation, ProjectValidationOptions],
    None,
]


def _iter_entry_points(group: str = "ordia.validators") -> list[tuple[str, str]]:
    try:
        from importlib.metadata import entry_points
    except ImportError:  # pragma: no cover
        return []

    eps = entry_points()
    selected = eps.select(group=group) if hasattr(eps, "select") else eps.get(group, [])
    result: list[tuple[str, str]] = []
    for ep in selected:
        name = getattr(ep, "name", str(ep))
        value = getattr(ep, "value", None) or f"{ep.module}:{ep.attr}"
        result.append((name, str(value)))
    return result


def _load_callable(target: str) -> ProfileValidator | None:
    module_name, _, attr = target.partition(":")
    if not module_name or not attr:
        return None
    module = importlib.import_module(module_name)
    obj = getattr(module, attr, None)
    return obj if callable(obj) else None


def run_profile_validators(
    root: Path,
    config: OrdiaConfig,
    result: Validation,
    *,
    options: ProjectValidationOptions,
    strict: bool = False,
) -> None:
    """Run installed profile validator plugins matching config.profile."""
    profile = config.profile
    for name, target in _iter_entry_points():
        if name != profile and not name.startswith(f"{profile}."):
            continue
        validator = _load_callable(target)
        if validator is None:
            message = f'profile validator plugin "{name}" could not be loaded ({target})'
            if strict:
                result.error(message)
            else:
                result.warn(message)
            continue
        try:
            validator(root, config, result, options)
        except Exception as exc:  # noqa: BLE001
            message = f'profile validator plugin "{name}" failed: {exc}'
            logger.debug(message)
            if strict:
                result.error(message)
            else:
                result.warn(message)
