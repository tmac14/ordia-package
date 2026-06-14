"""Tests for ordia.output JSON reports."""

from __future__ import annotations

import json

from ordia.output import OrdiaReport, emit_json, report_from_doctor, report_from_validation
from ordia.validator.common import Validation


def test_report_from_validation_ok() -> None:
    result = Validation()
    result.warn("minor")
    report = report_from_validation(result, command="validate")
    assert report.ok is True
    assert report.warnings == ["minor"]
    assert report.command == "validate"


def test_report_from_doctor_splits_warnings() -> None:
    report = report_from_doctor(
        issues=[],
        hints=["manifest: ordia.yaml", "warning: hook drift"],
        metadata={"hooks_installed": True},
    )
    assert report.ok is True
    assert report.warnings == ["hook drift"]
    assert report.hints == ["manifest: ordia.yaml"]
    assert report.metadata["hooks_installed"] is True


def test_emit_json_writes_stdout(capsys) -> None:
    from ordia.output import emit_json

    emit_json(OrdiaReport(command="doctor", ok=True))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["command"] == "doctor"
    assert data["ok"] is True


def test_ordia_report_to_dict() -> None:
    report = OrdiaReport(command="doctor", ok=False, issues=["x"])
    data = report.to_dict()
    assert data["schema_version"] == "1"
    assert data["issues"] == ["x"]
    assert data["ok"] is False


def test_report_from_validation_with_errors() -> None:
    result = Validation()
    result.error("fatal")
    report = report_from_validation(result, command="validate")
    assert report.ok is False
    assert report.issues == ["fatal"]
