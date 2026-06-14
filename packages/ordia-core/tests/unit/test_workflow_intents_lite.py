"""Unit tests for pip-safe workflow intent lookup in cursor hooks."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = CORE_ROOT / "ordia" / "cursor_bundle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from lib.workflow_intents_lite import known_intent_ids, parse_intent_from_prompt, validate_intent_in_prompt  # noqa: E402


class WorkflowIntentsLiteTests(unittest.TestCase):
    def test_parse_intent_line(self) -> None:
        self.assertEqual(parse_intent_from_prompt("intent: implement_ui\nDo work"), "implement_ui")

    def test_known_intent_ids_from_wheel(self) -> None:
        root = CORE_ROOT.parents[1]
        ids = known_intent_ids(root)
        self.assertIn("implement_ui", ids)
        self.assertIn("orchestrate_parallel", ids)

    def test_validate_unknown_intent_warns(self) -> None:
        root = CORE_ROOT.parents[1]
        message = validate_intent_in_prompt(root, "intent: not_a_real_intent\n")
        self.assertIsNotNone(message)
        self.assertIn("unknown intent", message or "")


if __name__ == "__main__":
    unittest.main()
