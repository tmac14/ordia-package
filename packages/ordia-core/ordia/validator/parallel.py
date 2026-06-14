"""Parallel-safety path helpers for validator and hooks."""

from __future__ import annotations


def normalize_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/") or normalized


def paths_overlap(left: str, right: str) -> bool:
    """Return True when two declared paths may touch the same files."""
    a = normalize_path(left)
    b = normalize_path(right)
    if not a or not b:
        return False
    if "*" in a or "*" in b:
        prefix_a = a.split("*", 1)[0]
        prefix_b = b.split("*", 1)[0]
        return prefix_a.startswith(prefix_b) or prefix_b.startswith(prefix_a)
    if a.endswith("/") or b.endswith("/"):
        base = a if a.endswith("/") else a + "/"
        other = b if b.endswith("/") else b + "/"
        return base.startswith(other) or other.startswith(base)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def collect_write_paths(task: dict) -> list[str]:
    paths: list[str] = []
    for key in ("planned_write_paths", "blocked_paths"):
        values = task.get(key, [])
        if isinstance(values, list):
            paths.extend(str(item) for item in values if item)
    return paths
