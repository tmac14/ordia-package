#!/usr/bin/env python3
"""Generate a minimal post-init greenfield snapshot for examples/greenfield/."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages" / "ordia-core"
DEFAULT_OUT = ROOT / "examples" / "greenfield" / "snapshot"

KEEP = (
    "ordia.yaml",
    "AGENTS.md",
    "docs/control/ORCHESTRATION_STATE.md",
    "docs/control/TASK_REGISTRY.yaml",
    "docs/control/AGENT_REGISTRY.yaml",
    "docs/control/commands.catalog.json",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold greenfield snapshot")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory")
    parser.add_argument("--profile", default="greenfield-example")
    args = parser.parse_args()

    out_dir: Path = args.out
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        cmd = [
            sys.executable,
            "-m",
            "ordia.cli",
            "init",
            "--directory",
            str(target),
            "--profile",
            args.profile,
        ]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            print(proc.stderr or proc.stdout, file=sys.stderr)
            return proc.returncode

        for rel in KEEP:
            src = target / rel
            if not src.is_file():
                print(f"WARNING: missing expected file {rel}", file=sys.stderr)
                continue
            dest = out_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    print(f"Greenfield snapshot written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
