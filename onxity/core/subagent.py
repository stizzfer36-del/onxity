from __future__ import annotations

import queue
import threading

from onxity.security.audit import AuditWriter


class SubAgent:
    def __init__(self, id: str, allowed_tool_names: list[str], max_depth: int, parent_id: str, task_queue: queue.Queue, config: dict, depth: int = 0):
        self.id = id
        self.allowed_tool_names = set(allowed_tool_names)
        self.max_depth = max_depth
        self.parent_id = parent_id
        self.queue = task_queue
        self.depth = depth
        self.audit = AuditWriter(config)
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop.set()

    def spawn_allowed(self) -> bool:
        ok = self.depth < self.max_depth
        self.audit.append("subagent_spawn", {"parent_id": self.parent_id, "agent_id": self.id, "depth": self.depth, "outcome": "ok" if ok else "denied_max_depth"})
        return ok

    def run(self):
        while not self._stop.is_set():
            try:
                self.queue.get(timeout=0.1)
            except queue.Empty:
                continue
