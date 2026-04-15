from __future__ import annotations

from pathlib import Path

from onxity.kernel.daemon import OnxityDaemon
from onxity.kernel.state import RuntimeState


def test_daemon_status_handles_stale_pid(tmp_config):
    pid_path = Path(tmp_config["daemon_pid_path"])
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text("999999", encoding="utf-8")
    RuntimeState(tmp_config).set_daemon(True, 999999)
    out = OnxityDaemon.read_status(tmp_config)
    assert out["state"]["running"] is False
