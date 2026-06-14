"""Unified brownfield adoption flow: audit → scaffold → cursor sync → validate."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AdoptionResult:
    root: Path
    steps: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    audit: dict[str, Any] | None = None
    validate_exit_code: int | None = None

    @property
    def ok(self) -> bool:
        return not self.errors


def run_adoption(
    root: Path,
    *,
    profile: str = "default",
    template: str = "minimal",
    product_root: str = "src/",
    with_cursor: bool = True,
    with_docs: bool = True,
    sync_commands: bool = True,
    write_inventory: bool = True,
    run_validate: bool = True,
) -> AdoptionResult:
    """Execute the full brownfield adoption pipeline."""
    from ordia.adoption.audit import format_adoption_report, format_inventory_markdown, run_docs_audit
    from ordia.commands.catalog import resolve_catalog_paths
    from ordia.config import load_ordia_config

    root = root.resolve()
    result = AdoptionResult(root=root)
    manifest = root / "ordia.yaml"

    # 1 — Audit existing repository
    cfg = load_ordia_config(root) if manifest.is_file() else None
    catalog_path, _ = resolve_catalog_paths(root, cfg)
    audit = run_docs_audit(root, catalog_path=catalog_path)
    result.audit = audit.to_dict()
    control_dir = root / audit.suggested_control_root
    control_dir.mkdir(parents=True, exist_ok=True)
    report_path = control_dir / "ADOPTION_REPORT.md"
    report_path.write_text(format_adoption_report(audit), encoding="utf-8")
    result.steps.append(f"wrote {report_path.relative_to(root)}")
    if write_inventory:
        inv_path = control_dir / "DOCUMENTATION_INVENTORY.md"
        inv_path.write_text(format_inventory_markdown(audit), encoding="utf-8")
        result.steps.append(f"wrote {inv_path.relative_to(root)}")

    # 2 — Scaffold missing Ordia files (brownfield-safe)
    import argparse

    from ordia.cli import cmd_init

    init_args = argparse.Namespace(
        directory=str(root),
        profile=profile,
        template=template,
        product_root=product_root,
        with_cursor=with_cursor,
        with_docs=with_docs,
        from_repo_docs=False,
        sync_commands=sync_commands,
        force=False,
        skip_existing=True,
        audit_docs=False,
        write_inventory=False,
    )
    init_code = cmd_init(init_args)
    if init_code != 0:
        result.errors.append(f"ordia init --skip-existing failed (exit {init_code})")
        return result
    result.steps.append("ordia init --skip-existing completed")

    # 3 — Refresh Cursor bundle
    if with_cursor:
        from ordia.cli import cmd_cursor_sync

        sync_args = argparse.Namespace(directory=str(root))
        sync_code = cmd_cursor_sync(sync_args)
        if sync_code != 0:
            result.errors.append(f"ordia cursor sync failed (exit {sync_code})")
            return result
        result.steps.append("ordia cursor sync completed")

    # 4 — Validate control plane
    if run_validate:
        from ordia.cli import cmd_validate

        validate_args = argparse.Namespace(
            directory=str(root),
            project=True,
            strict_profile=False,
            strict_limbo=False,
            json=False,
        )
        result.validate_exit_code = cmd_validate(validate_args)
        if result.validate_exit_code != 0:
            result.warnings.append(
                "ordia validate --project reported issues — review ADOPTION_REPORT.md next steps"
            )
        else:
            result.steps.append("ordia validate --project passed")

    return result
