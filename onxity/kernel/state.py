from __future__ import annotations

import json
import time
import uuid
from pathlib import Path


class RuntimeState:
    """Restart-safe runtime/session state."""

    def __init__(self, config: dict):
        self.path = Path(config["runtime_state_path"]).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"active_session_id": None, "sessions": {}, "daemon": {"running": False}}

    def save(self):
        self.path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def start_session(self, agent_id: str, meta: dict | None = None) -> dict:
        sid = f"sess-{uuid.uuid4().hex[:10]}"
        rec = {"id": sid, "agent_id": agent_id, "created_ts": time.time(), "ended_ts": None, "meta": meta or {}}
        self.state["sessions"][sid] = rec
        self.state["active_session_id"] = sid
        self.save()
        return rec

    def end_session(self, sid: str):
        rec = self.state["sessions"].get(sid)
        if rec and rec["ended_ts"] is None:
            rec["ended_ts"] = time.time()
        if self.state.get("active_session_id") == sid:
            self.state["active_session_id"] = None
        self.save()

    def set_daemon(self, running: bool, pid: int | None = None):
        self.state["daemon"] = {"running": running, "pid": pid, "updated_ts": time.time()}
        self.save()
