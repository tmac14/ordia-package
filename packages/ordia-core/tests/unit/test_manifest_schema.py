"""Tests for ordia.yaml JSON Schema validation."""

from __future__ import annotations

import unittest

from ordia.validator.common import Validation
from ordia.validator.manifest_schema import validate_manifest_schema


class ManifestSchemaTests(unittest.TestCase):
    def test_valid_manifest_passes(self) -> None:
        raw = {
            "version": "0.3",
            "profile": "test",
            "control": {"root": "docs/control"},
            "enforcement": {"productRoots": ["src/"]},
        }
        result = Validation()
        validate_manifest_schema(raw, result)
        self.assertEqual(result.errors, [])

    def test_missing_profile_fails(self) -> None:
        raw = {
            "version": "0.3",
            "control": {"root": "docs/control"},
            "enforcement": {"productRoots": ["src/"]},
        }
        result = Validation()
        validate_manifest_schema(raw, result)
        self.assertTrue(any("profile" in err.lower() for err in result.errors))


if __name__ == "__main__":
    unittest.main()
