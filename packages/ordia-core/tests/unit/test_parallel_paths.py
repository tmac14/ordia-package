"""Unit tests for parallel path overlap helpers."""

from __future__ import annotations

import unittest

from ordia.validator.parallel import collect_write_paths, normalize_path, paths_overlap


class ParallelPathTests(unittest.TestCase):
    def test_normalize_strips_relative_prefix(self) -> None:
        self.assertEqual(normalize_path("./src/api/"), "src/api")

    def test_paths_overlap_prefix_and_glob(self) -> None:
        self.assertTrue(paths_overlap("src/api/", "src/api/handler.py"))
        self.assertTrue(paths_overlap("src/*", "src/ui"))
        self.assertFalse(paths_overlap("src/api/", "apps/web/"))

    def test_collect_write_paths_merges_fields(self) -> None:
        task = {
            "planned_write_paths": ["src/a"],
            "blocked_paths": ["src/b"],
        }
        self.assertEqual(collect_write_paths(task), ["src/a", "src/b"])


if __name__ == "__main__":
    unittest.main()
