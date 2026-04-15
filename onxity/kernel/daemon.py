from __future__ import annotations

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

    @staticmethod
    def _pid_exists(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

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
        running = bool(state.get("daemon", {}).get("running", False))
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip())
                running = OnxityDaemon._pid_exists(pid)
            except ValueError:
                pid = None
                running = False
        if not running:
            RuntimeState(config).set_daemon(False, None)
        return {"state": {**state.get("daemon", {}), "running": running}, "pid": pid, "pid_file": str(pid_file)}

    @staticmethod
    def stop_existing(config: dict) -> dict:
        pid_file = Path(config["daemon_pid_path"]).expanduser()
        if not pid_file.exists():
            RuntimeState(config).set_daemon(False, None)
            return {"status": "not_running"}
        pid = int(pid_file.read_text(encoding="utf-8").strip())
        try:
            os.kill(pid, signal.SIGTERM)
            return {"status": "signaled", "pid": pid}
        except ProcessLookupError:
            pid_file.unlink(missing_ok=True)
            RuntimeState(config).set_daemon(False, None)
            return {"status": "not_running", "pid": pid}
