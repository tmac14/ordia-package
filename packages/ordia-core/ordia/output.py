"""Structured JSON output for Ordia CLI commands."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

from ordia import __version__
from ordia.validator.common import Validation


@dataclass
class OrdiaReport:
    schema_version: str = "1"
    command: str = ""
    ordia_version: str = ""
    ok: bool = True
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def emit_json(report: OrdiaReport) -> None:
    sys.stdout.write(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n")


def report_from_validation(
    result: Validation,
    *,
    command: str,
    hints: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> OrdiaReport:
    return OrdiaReport(
        command=command,
        ordia_version=__version__,
        ok=not result.errors,
        issues=list(result.errors),
        warnings=list(result.warnings),
        hints=list(hints or []),
        metadata=dict(metadata or {}),
    )


def report_from_doctor(
    *,
    issues: list[str],
    hints: list[str],
    metadata: dict[str, Any] | None = None,
) -> OrdiaReport:
    warnings = [h.removeprefix("warning: ") for h in hints if h.startswith("warning: ")]
    plain_hints = [h for h in hints if not h.startswith("warning: ")]
    return OrdiaReport(
        command="doctor",
        ordia_version=__version__,
        ok=not issues,
        issues=list(issues),
        warnings=warnings,
        hints=plain_hints,
        metadata=dict(metadata or {}),
    )
