#!/usr/bin/env python3
"""Sync or verify Ordia Cursor bundle: live .cursor/, template, and wheel cursor_bundle/."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_CURSOR = ROOT / ".cursor"
TEMPLATE = ROOT / "packages" / "ordia-cursor" / "templates"
WHEEL_BUNDLE = ROOT / "packages" / "ordia-core" / "ordia" / "cursor_bundle"

HOOK_FILES = (
    "hooks/session_start.py",
    "hooks/validate_runtime_header.py",
    "hooks/check_model_tier.py",
    "hooks/log_model_context.py",
    "hooks/guard_mode_before_edit.py",
    "hooks/lib/control_context.py",
    "hooks/lib/ordia_manifest.py",
    "hooks/lib/model_routing_lite.py",
    "hooks/lib/workflow_intents_lite.py",
)

RULE_GLOB = "ordia-*.mdc"

RULE_FILES = tuple(
    f"rules/{name}"
    for name in (
        "ordia-coordination-docs.mdc",
        "ordia-implementation-mode.mdc",
        "ordia-orchestration-mode.mdc",
        "ordia-recovery-bootstrap.mdc",
        "ordia-runtime-protocol-header.mdc",
    )
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_hooks_template(text: str) -> str:
    return text.replace("{PYTHON}", "python")


def _normalize_hooks_live(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if ".cursor/hooks/" in line and "command" in line:
            line = re.sub(r'"[^"]*\.cursor/hooks/', '"python .cursor/hooks/', line)
        lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _compare_hooks_json(left: Path, right: Path, label: str) -> tuple[bool, str]:
    if not left.is_file() or not right.is_file():
        return False, f"hooks.json missing for {label}"
    left_norm = _normalize_hooks_live(left.read_text(encoding="utf-8"))
    right_norm = _normalize_hooks_template(right.read_text(encoding="utf-8"))
    if left.is_file() and right.is_file() and left.parent == LIVE_CURSOR:
        left_norm = _normalize_hooks_live(left.read_text(encoding="utf-8"))
        right_norm = _normalize_hooks_template(right.read_text(encoding="utf-8"))
    elif left.name == "hooks.json" and "{PYTHON}" in right.read_text(encoding="utf-8"):
        left_norm = _normalize_hooks_live(left.read_text(encoding="utf-8"))
        right_norm = _normalize_hooks_template(right.read_text(encoding="utf-8"))
    else:
        left_norm = left.read_text(encoding="utf-8")
        right_norm = right.read_text(encoding="utf-8")
    if left_norm != right_norm:
        return False, f"hooks.json differs: {label}"
    return True, ""


def _template_file_pairs() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for relative in HOOK_FILES:
        pairs.append((LIVE_CURSOR / relative, TEMPLATE / relative))
    for rule in sorted((LIVE_CURSOR / "rules").glob(RULE_GLOB)):
        pairs.append((rule, TEMPLATE / "rules" / rule.name))
    return pairs


def _mirror_template_to_wheel() -> None:
    if WHEEL_BUNDLE.exists():
        shutil.rmtree(WHEEL_BUNDLE)
    shutil.copytree(TEMPLATE, WHEEL_BUNDLE)


def write_hooks_manifest() -> None:
    manifest: dict[str, str] = {}
    for relative in HOOK_FILES:
        path = WHEEL_BUNDLE / relative
        if path.is_file():
            manifest[relative] = _sha256(path)
    manifest_path = WHEEL_BUNDLE / "hooks.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_rules_manifest() -> None:
    manifest: dict[str, str] = {}
    for relative in RULE_FILES:
        path = WHEEL_BUNDLE / relative
        if path.is_file():
            manifest[relative] = _sha256(path)
    manifest_path = WHEEL_BUNDLE / "rules.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def cmd_check(*, product_only: bool = False) -> int:
    errors: list[str] = []
    if not product_only:
        ok, msg = _compare_hooks_json(LIVE_CURSOR / "hooks.json", TEMPLATE / "hooks.json", "live vs template")
        if not ok:
            errors.append(msg)
        for live, dest in _template_file_pairs():
            if not live.is_file():
                errors.append(f"missing live file: {live.relative_to(ROOT)}")
                continue
            if not dest.is_file():
                errors.append(f"missing template file: {dest.relative_to(ROOT)}")
                continue
            if _sha256(live) != _sha256(dest):
                errors.append(f"drift: {live.relative_to(ROOT)} != {dest.relative_to(ROOT)}")
    if not TEMPLATE.is_dir():
        errors.append(f"missing template bundle: {TEMPLATE.relative_to(ROOT)}")
    if not WHEEL_BUNDLE.is_dir():
        errors.append(f"missing wheel bundle: {WHEEL_BUNDLE.relative_to(ROOT)}")
    else:
        ok, msg = _compare_hooks_json(TEMPLATE / "hooks.json", WHEEL_BUNDLE / "hooks.json", "template vs wheel")
        if not ok:
            errors.append(msg)
        for relative in HOOK_FILES:
            src = TEMPLATE / relative
            dest = WHEEL_BUNDLE / relative
            if not dest.is_file():
                errors.append(f"missing wheel file: {dest.relative_to(ROOT)}")
            elif src.is_file() and _sha256(src) != _sha256(dest):
                errors.append(f"wheel drift: {relative}")
        for rule in sorted((TEMPLATE / "rules").glob(RULE_GLOB)):
            dest = WHEEL_BUNDLE / "rules" / rule.name
            if not dest.is_file():
                errors.append(f"missing wheel rule: {rule.name}")
            elif _sha256(rule) != _sha256(dest):
                errors.append(f"wheel rule drift: {rule.name}")
    if errors:
        print("Ordia Cursor bundle drift detected:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("Run: python tools/sync_cursor_bundle.py --sync", file=sys.stderr)
        return 1
    label = "template, wheel" if product_only else "live, template, wheel"
    print(f"Ordia Cursor bundle: in sync ({label})")
    return 0


def cmd_sync(*, product_only: bool = False) -> int:
    if product_only:
        _mirror_template_to_wheel()
        write_hooks_manifest()
        write_rules_manifest()
        print("Ordia Cursor bundle synced: template -> ordia/cursor_bundle/")
        return cmd_check(product_only=True)
    TEMPLATE.mkdir(parents=True, exist_ok=True)
    (TEMPLATE / "hooks" / "lib").mkdir(parents=True, exist_ok=True)
    (TEMPLATE / "rules").mkdir(parents=True, exist_ok=True)
    for live, dest in _template_file_pairs():
        if not live.is_file():
            print(f"WARNING: skip missing {live.relative_to(ROOT)}", file=sys.stderr)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(live, dest)
    live_hooks = LIVE_CURSOR / "hooks.json"
    template_hooks = TEMPLATE / "hooks.json"
    if live_hooks.is_file():
        text = _normalize_hooks_live(live_hooks.read_text(encoding="utf-8")).replace(
            "python .cursor/hooks/", "{PYTHON} .cursor/hooks/"
        )
        template_hooks.write_text(text, encoding="utf-8")
    _mirror_template_to_wheel()
    write_hooks_manifest()
    write_rules_manifest()
    print("Ordia Cursor bundle synced to packages/ordia-cursor/templates/ and ordia/cursor_bundle/")
    return cmd_check(product_only=product_only)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync or verify Ordia Cursor template bundle")
    parser.add_argument("--sync", action="store_true", help="Copy live .cursor/ into template + wheel bundle")
    parser.add_argument("--check", action="store_true", help="Verify bundle matches live (default)")
    parser.add_argument(
        "--product-only",
        action="store_true",
        help="Compare template vs wheel only (ordia-package repo; no live .cursor/)",
    )
    args = parser.parse_args()
    if args.sync:
        return cmd_sync(product_only=args.product_only)
    return cmd_check(product_only=args.product_only)


if __name__ == "__main__":
    raise SystemExit(main())
