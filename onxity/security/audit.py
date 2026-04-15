"""
onxity.security.audit
=====================
Append-only audit log writer.

All writes are atomic: file opened in append mode, entry written as a
single JSON line, flushed and fsync'd if available.

Redaction policy
----------------
The following keys in the payload are automatically replaced with
"[REDACTED]" before writing. If redact_hash=True in config, the
sha256 hex digest of the original value is stored alongside:

  Sensitive keys: password, secret, api_key, key, token, credential,
                  auth, authorization, private_key, access_token

Example audit entry (redacted):
  {"type":"tool_call","ts":1713178800.0,"uuid":"...",
   "payload":{"tool":"filesystem.read","args":{"path":"/etc/issue"},
              "api_key":"[REDACTED]","api_key_hash":"abc123..."}}
"""

import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

SENSITIVE_KEYS = {
    "password", "secret", "api_key", "key", "token",
    "credential", "auth", "authorization", "private_key", "access_token",
}


def _redact(payload: dict, store_hash: bool = False) -> dict:
    """
    Return a copy of payload with sensitive keys redacted.

    Parameters
    ----------
    payload:
        Arbitrary dict (will be deep-copied).
    store_hash:
        If True, add a companion key '<key>_hash' with the sha256 digest.
    """
    result = {}
    for k, v in payload.items():
        if k.lower() in SENSITIVE_KEYS:
            if store_hash and isinstance(v, str):
                result[f"{k}_hash"] = hashlib.sha256(v.encode()).hexdigest()
            result[k] = "[REDACTED]"
        elif isinstance(v, dict):
            result[k] = _redact(v, store_hash=store_hash)
        else:
            result[k] = v
    return result


class AuditWriter:
    """
    Append-only audit log writer.

    Parameters
    ----------
    config:
        onxity config dict. Uses 'audit_path' and optional 'redact_hash'.
    """

    def __init__(self, config: dict):
        self.audit_path = Path(config.get("audit_path", Path.home() / ".onxity" / "audit.jsonl"))
        self.redact_hash = config.get("redact_hash", False)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry_type: str, payload: dict) -> dict:
        """
        Write a single audit entry as a JSON line.

        Returns the entry dict that was written (for testing).
        """
        clean_payload = _redact(payload, store_hash=self.redact_hash)
        entry = {
            "type": entry_type,
            "ts": time.time(),
            "uuid": str(uuid.uuid4()),
            "payload": clean_payload,
        }
        line = json.dumps(entry, default=str) + "\n"
        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            try:
                os.fsync(f.fileno())
            except (AttributeError, OSError):
                pass  # Windows / non-seekable streams
        return entry
