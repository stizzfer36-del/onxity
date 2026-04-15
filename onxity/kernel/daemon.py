from __future__ import annotations

import json
import os
import signal
import threading
import time
from pathlib import Path

from onxity.kernel.events import EventBus
from onxity.kernel.identity import IdentityStore
from onxity.kernel.state import RuntimeState
from onxity.security.audit import AuditWriter


class OnxityDaemon:
    """Minimal persistent daemon heartbeat + runtime state marker."""

    def __init__(self, config: dict):
        self.config = config
        self.bus = EventBus()
        self.audit = AuditWriter(config)
        self.identity = IdentityStore(config).load_or_create()
        self.state = RuntimeState(config)
        self.pid_file = Path(config["daemon_pid_path"]).expanduser()
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self._stop = threading.Event()

    def _loop(self):
        while not self._stop.is_set():
            evt = self.bus.publish("daemon_heartbeat", {"pid": os.getpid(), "operator_id": self.identity["operator_id"]})
            self.audit.append("event", evt)
            time.sleep(float(self.config.get("daemon", {}).get("heartbeat_seconds", 2)))

    def run_foreground(self):
        self.pid_file.write_text(str(os.getpid()), encoding="utf-8")
        self.state.set_daemon(True, os.getpid())
        self.audit.append("daemon_start", {"pid": os.getpid(), "identity": self.identity})

        def _sigterm(_signo, _frame):
            self.stop()

        signal.signal(signal.SIGTERM, _sigterm)
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
        while not self._stop.is_set():
            time.sleep(0.2)
        t.join(timeout=2)

    def stop(self):
        self._stop.set()
        self.state.set_daemon(False, None)
        self.audit.append("daemon_stop", {"pid": os.getpid()})
        if self.pid_file.exists():
            self.pid_file.unlink()

    @staticmethod
    def read_status(config: dict) -> dict:
        state = RuntimeState(config).state
        pid_file = Path(config["daemon_pid_path"]).expanduser()
        pid = None
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip())
            except ValueError:
                pid = None
        return {"state": state.get("daemon", {}), "pid": pid, "pid_file": str(pid_file)}

    @staticmethod
    def stop_existing(config: dict) -> dict:
        pid_file = Path(config["daemon_pid_path"]).expanduser()
        if not pid_file.exists():
            RuntimeState(config).set_daemon(False, None)
            return {"status": "not_running"}
        pid = int(pid_file.read_text(encoding="utf-8").strip())
        os.kill(pid, signal.SIGTERM)
        return {"status": "signaled", "pid": pid}
