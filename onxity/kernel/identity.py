from __future__ import annotations

import json
import os
import secrets
import socket
import time
from pathlib import Path


class IdentityStore:
    """Durable operator identity persisted across restarts."""

    def __init__(self, config: dict):
        self.path = Path(config["identity_path"]).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_or_create(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        identity = {
            "operator_id": f"op-{secrets.token_hex(6)}",
            "created_ts": time.time(),
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
        }
        self.path.write_text(json.dumps(identity, indent=2), encoding="utf-8")
        return identity
