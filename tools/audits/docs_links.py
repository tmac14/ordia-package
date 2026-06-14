#!/usr/bin/env python3
"""Audit relative markdown links in Ordia documentation trees."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PORTABLE_DOC_NAMES = frozenset({
    "README.md",
    "DAILY_USAGE.md",
    "SPEC_v0.2.md",
    "SPEC_v0.6.md",
    "SPEC_v0.7.md",
    "SPEC_v0.8.md",
})

SCAN_ROOTS = (
    ROOT / "docs" / "ordia",
    ROOT / "packages" / "ordia-core" / "docs",
    ROOT / "packages" / "ordia-core" / "ordia" / "product_docs",
)

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#]+)(?:#[^)]*)?\)")


def _collect_markdown_files() -> list[Path]:
    files: list[Path] = []
    for scan_root in SCAN_ROOTS:
        if not scan_root.is_dir():
            continue
        portable_only = scan_root.name in {"ordia", "product_docs"} or (
            scan_root.parent.name == "ordia" and scan_root.name == "ordia"
        )
        for path in sorted(scan_root.rglob("*.md")):
            if not path.is_file():
                continue
            if portable_only and path.name not in PORTABLE_DOC_NAMES:
                continue
            files.append(path)
    return files


def _resolve_link(source: Path, href: str) -> Path:
    href = href.strip().replace("\\", "/")
    if href.startswith("/"):
        return (ROOT / href.lstrip("/")).resolve()
    return (source.parent / href).resolve()


def _target_exists(target: Path) -> bool:
    if target.is_file() or target.is_dir():
        return True
    if target.suffix:
        return False
    for candidate in (target.with_suffix(".md"), target / "README.md"):
        if candidate.is_file():
            return True
    return False


def audit_links() -> list[tuple[str, str, str]]:
    broken: list[tuple[str, str, str]] = []
    for source in _collect_markdown_files():
        try:
            text = source.read_text(encoding="utf-8")
        except OSError as exc:
            broken.append((source.relative_to(ROOT).as_posix(), "", str(exc)))
            continue
        for match in LINK_RE.finditer(text):
            href = match.group(1).strip()
            if not href or href.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = _resolve_link(source, href)
            if not _target_exists(target):
                broken.append((source.relative_to(ROOT).as_posix(), href, str(target.relative_to(ROOT))))
    return broken


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit relative links in Ordia markdown docs")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any broken relative link is found",
    )
    args = parser.parse_args()

    broken = audit_links()
    print("Documentation link audit")
    print(f"- markdown files scanned: {len(_collect_markdown_files())}")
    print(f"- broken relative links: {len(broken)}")

    if broken:
        for source, href, target in broken:
            print(f"BROKEN: {source} -> {href} (resolved: {target})", file=sys.stderr)
        return 1 if args.strict else 0

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
