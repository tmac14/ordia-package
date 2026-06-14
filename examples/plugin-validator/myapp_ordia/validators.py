"""Minimal profile validator plugin for ordia-core examples."""

from __future__ import annotations

from pathlib import Path

from ordia.config import OrdiaConfig
from ordia.validator.common import Validation
from ordia.validator.project import ProjectValidationOptions


def validate_profile_mention(
    root: Path,
    config: OrdiaConfig,
    result: Validation,
    options: ProjectValidationOptions,
) -> None:
    profile_path = config.project_profile_path
    if not profile_path.is_file():
        result.warn(f"Profile doc missing for plugin check: {profile_path.name}")
        return
    text = profile_path.read_text(encoding="utf-8")
    if config.profile not in text:
        message = (
            f"PROFILE.md should mention manifest profile {config.profile!r} "
            "(ordia-plugin-validator-example)"
        )
        if options.strict_profile:
            result.error(message)
        else:
            result.warn(message)
