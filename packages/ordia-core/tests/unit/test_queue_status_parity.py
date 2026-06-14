"""Parity between QUEUE_STATUS and documented queue tables."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from ordia.validator.common import QUEUE_STATUS

CORE_ROOT = Path(__file__).resolve().parents[2]
TASK_EXECUTION = CORE_ROOT / "ordia" / "protocols" / "TASK_EXECUTION.md"
PROTOCOLS_DOC = CORE_ROOT / "docs" / "PROTOCOLS.md"


def _parse_queue_table(text: str) -> dict[str, set[str]]:
    rows: dict[str, set[str]] = {}
    in_table = False
    for line in text.splitlines():
        if "| Queue |" in line and "Allowed statuses" in line:
            in_table = True
            continue
        if not in_table:
            continue
        if not line.strip().startswith("|"):
            if rows:
                break
            continue
        if re.match(r"^\|\s*-+", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        queue = cells[0].strip("`")
        statuses = {item.strip().strip("`") for item in cells[1].split(",") if item.strip()}
        if queue:
            rows[queue] = statuses
    return rows


class QueueStatusParityTests(unittest.TestCase):
    def test_task_execution_table_matches_queue_status(self) -> None:
        text = TASK_EXECUTION.read_text(encoding="utf-8")
        documented = _parse_queue_table(text)
        self.assertEqual(set(documented), set(QUEUE_STATUS))
        for queue, allowed in QUEUE_STATUS.items():
            self.assertEqual(documented.get(queue), set(allowed), f"drift in queue {queue}")

    def test_protocols_doc_table_matches_queue_status(self) -> None:
        text = PROTOCOLS_DOC.read_text(encoding="utf-8")
        documented = _parse_queue_table(text)
        self.assertEqual(set(documented), set(QUEUE_STATUS))
        for queue, allowed in QUEUE_STATUS.items():
            self.assertEqual(documented.get(queue), set(allowed), f"drift in queue {queue}")


if __name__ == "__main__":
    unittest.main()
