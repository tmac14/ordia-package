"""Tests for workflow intents including UI/UX."""

from __future__ import annotations

import unittest
from pathlib import Path

from ordia.workflows.registry import load_intent


class WorkflowIntentUiTests(unittest.TestCase):
    def test_ui_intents_exist(self) -> None:
        for intent_id in ("implement_ui", "implement_ux", "modify_feature", "orchestrate_parallel"):
            intent = load_intent(Path("."), intent_id)
            self.assertIsNotNone(intent, intent_id)
            assert intent is not None
            self.assertTrue(intent.requires_task or intent_id == "orchestrate_parallel")


if __name__ == "__main__":
    unittest.main()
