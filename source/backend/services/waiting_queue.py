"""The check-in waiting queue (ITEC 104: a min-heap / priority queue).

Patients leave the queue in the order they checked in. A heap gives O(log n) insertion and
O(log n) removal of the earliest arrival, instead of re-sorting the whole list each time.
"""

from __future__ import annotations

import heapq
from datetime import datetime
from typing import Any


class WaitingQueue:
    """Min-heap of checked-in appointments ordered by (checked_in_at, id)."""

    def __init__(self) -> None:
        self._heap: list[tuple[datetime, int, dict[str, Any]]] = []

    def push(self, appointment: dict[str, Any]) -> None:
        """Add a checked-in appointment. Missing check-in times sort last."""
        heapq.heappush(self._heap, (appointment.get("checked_in_at") or datetime.max, appointment["id"], appointment))

    def pop(self) -> dict[str, Any]:
        """Remove and return the patient who has waited longest."""
        return heapq.heappop(self._heap)[2]

    def peek(self) -> dict[str, Any] | None:
        """The next patient without removing them."""
        return self._heap[0][2] if self._heap else None

    def __len__(self) -> int:
        return len(self._heap)

    def ordered(self) -> list[dict[str, Any]]:
        """Everyone in service order, each tagged with a 1-based `queue_position` (the queue is emptied)."""
        result: list[dict[str, Any]] = []
        while self._heap:
            item = self.pop()
            item["queue_position"] = len(result) + 1
            result.append(item)
        return result