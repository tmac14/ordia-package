"""Lightweight tests for model routing helpers."""

from __future__ import annotations

from ordia.model_routing.rate_limits import (
    CODEX_RATE_LIMIT_NOTE,
    CURSOR_RATE_LIMIT_NOTE,
    is_cursor_auto_model,
    rate_limit_guidance,
)
from ordia.model_routing.tiers import max_tier, normalize_tier, tier_at_least


def test_is_cursor_auto_model() -> None:
    assert is_cursor_auto_model(None) is True
    assert is_cursor_auto_model("auto") is True
    assert is_cursor_auto_model("gpt-4") is False


def test_rate_limit_guidance_by_runtime() -> None:
    assert CODEX_RATE_LIMIT_NOTE in rate_limit_guidance("ONLY_CODEX")
    assert CURSOR_RATE_LIMIT_NOTE in rate_limit_guidance("ONLY_CURSOR")
    assert CURSOR_RATE_LIMIT_NOTE in rate_limit_guidance(None)


def test_normalize_tier_and_ordering() -> None:
    assert normalize_tier("t2") == "T2"
    assert normalize_tier("invalid") is None
    assert tier_at_least("T3", "T2") is True
    assert tier_at_least("T1", "T3") is False
    assert max_tier("T1", "T3", "T0") == "T3"
