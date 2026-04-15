from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from pathlib import Path

SENSITIVE = {"password", "secret", "api_key", "key", "token"}


def redact(payload: dict, hash_sensitive: bool = False) -> dict:
    out = {}
    for k, v in payload.items():
        if isinstance(v, dict):
            out[k] = redact(v, hash_sensitive)
        elif k.lower() in SENSITIVE:
            out[k] = "[REDACTED]"
            if hash_sensitive and isinstance(v, str):
                out[f"{k}_sha256"] = hashlib.sha256(v.encode()).hexdigest()
        else:
            out[k] = v
    return out


class AuditWriter:
    def __init__(self, config: dict):
        self.path = Path(config["audit_path"]).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.hash_sensitive = bool(config.get("audit_hash_sensitive", False))

    def append(self, entry_type: str, payload: dict) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "type": entry_type,
            "ts": time.time(),
            "payload": redact(payload, self.hash_sensitive),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return entry
