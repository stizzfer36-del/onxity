from __future__ import annotations

from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class _Collector(FileSystemEventHandler):
    def __init__(self):
        self.events: list[dict] = []

    def on_any_event(self, event):
        self.events.append({"event_type": event.event_type, "src_path": event.src_path, "is_directory": event.is_directory})


def watch_once(path: str, seconds: float = 1.0) -> dict:
    root = Path(path).expanduser().resolve()
    handler = _Collector()
    observer = Observer()
    observer.schedule(handler, str(root), recursive=True)
    observer.start()
    try:
        import time

        time.sleep(seconds)
    finally:
        observer.stop()
        observer.join(timeout=2)
    return {"path": str(root), "events": handler.events}
