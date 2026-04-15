from __future__ import annotations

import queue
import threading
import time
import uuid


class EventBus:
    """In-process event bus with fan-out subscribers."""

    def __init__(self):
        self._q: queue.Queue[dict] = queue.Queue()
        self._subs: list[queue.Queue] = []
        self._lock = threading.Lock()

    def publish(self, typ: str, payload: dict) -> dict:
        evt = {"event_id": str(uuid.uuid4()), "type": typ, "ts": time.time(), "payload": payload}
        self._q.put(evt)
        with self._lock:
            for sub in self._subs:
                sub.put(evt)
        return evt

    def subscribe(self) -> queue.Queue:
        q: queue.Queue[dict] = queue.Queue()
        with self._lock:
            self._subs.append(q)
        return q

    def read(self, timeout: float = 0.1) -> dict | None:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None
