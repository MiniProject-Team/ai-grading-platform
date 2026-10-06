"""Bounded, thread-safe progress snapshots for this API process."""

from collections import OrderedDict
from datetime import datetime, timezone
from threading import Lock
import time


class ProgressStore:
    def __init__(self, capacity: int = 1000, ttl_seconds: float = 3600) -> None:
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self._lock = Lock()
        self._entries: OrderedDict[str, tuple[float, dict]] = OrderedDict()

    def update(self, evaluation_id: str, stage: str, message: str, status: str = "processing") -> None:
        with self._lock:
            self._prune()
            previous = self._entries.get(evaluation_id)
            events = previous[1]["events"] if previous else []
            event = {"stage": stage, "message": message, "timestamp": datetime.now(timezone.utc).isoformat()}
            snapshot = {"evaluation_id": evaluation_id, "status": status, **event, "events": [*events, event][-100:]}
            self._entries[evaluation_id] = (time.monotonic(), snapshot)
            self._entries.move_to_end(evaluation_id)
            while len(self._entries) > self.capacity:
                self._entries.popitem(last=False)

    def get(self, evaluation_id: str) -> dict | None:
        with self._lock:
            self._prune()
            entry = self._entries.get(evaluation_id)
            return entry[1] if entry else None

    def _prune(self) -> None:
        cutoff = time.monotonic() - self.ttl_seconds
        while self._entries and next(iter(self._entries.values()))[0] < cutoff:
            self._entries.popitem(last=False)
