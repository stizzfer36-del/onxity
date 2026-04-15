from __future__ import annotations

import json
import threading
import time

from onxity.memory.sqlite_store import add_memory_chunk, get_session


class RollingBuffer:
    def __init__(self, config: dict):
        self.config = config
        self.items: list[dict] = []
        self.lock = threading.Lock()
        mem = config.get("memory", {})
        self.max_items = int(mem.get("max_items", 50))
        self.max_bytes = int(mem.get("max_bytes", 262144))

    def append(self, item: dict):
        with self.lock:
            self.items.append(item)

    def snapshot(self) -> list[dict]:
        with self.lock:
            return list(self.items)

    def _size_bytes(self) -> int:
        return len(json.dumps(self.items))

    def check_and_compress(self, compressor_provider) -> dict:
        with self.lock:
            if len(self.items) <= self.max_items and self._size_bytes() <= self.max_bytes:
                return {"compressed": False}
            old = self.items[:-self.max_items]
            if not old:
                return {"compressed": False}
            summary = compressor_provider.complete(
                [{"role": "system", "content": "compress"}, {"role": "user", "content": json.dumps(old)}], []
            )["content"]
            db = get_session()
            chunk_id = add_memory_chunk(db, summary, old[0].get("ts", time.time()), old[-1].get("ts", time.time()), 0.0)
            self.items = self.items[-self.max_items :]
            return {"compressed": True, "chunk_id": chunk_id}

# TODO add semantic compression quality scoring and chunk retrieval relevance tests.
