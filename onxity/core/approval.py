from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from onxity.memory.sqlite_store import add_audit_db, get_session
from onxity.security.audit import AuditWriter


class ApprovalModule:
    def __init__(self, config: dict):
        self.config = config
        self.audit = AuditWriter(config)
        self.path = Path(config["runtime_state_path"]).expanduser().with_name("approvals.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._tokens = self._load_tokens()

    def _load_tokens(self) -> dict[str, dict]:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {}

    def _save_tokens(self):
        self.path.write_text(json.dumps(self._tokens, indent=2), encoding="utf-8")

    def create_approval_request(self, requester: str, scopes: list[str], reason: str, expires_in: int) -> str:
        token = f"appr-{uuid.uuid4().hex[:8]}"
        now = time.time()
        self._tokens[token] = {
            "token": token,
            "requester": requester,
            "scopes": scopes,
            "reason": reason,
            "created_ts": now,
            "expires_at": now + expires_in,
            "status": "pending",
        }
        self._save_tokens()
        payload = self._tokens[token].copy()
        self.audit.append("approval_request", payload)
        try:
            add_audit_db(get_session(), "approval_request", payload)
        except Exception:
            pass
        return token

    def approve_token(self, token: str, operator: str, attestation_text: str) -> dict:
        rec = self._tokens.get(token)
        if not rec:
            raise ValueError("unknown token")
        if time.time() > rec["expires_at"]:
            rec["status"] = "expired"
            self._save_tokens()
            raise ValueError("expired token")
        rec["status"] = "approved"
        rec["operator"] = operator
        rec["attestation_text"] = attestation_text
        rec["approved_ts"] = time.time()
        self._save_tokens()
        self.audit.append("approval_granted", rec)
        try:
            add_audit_db(get_session(), "approval_granted", rec)
        except Exception:
            pass
        return rec

    def revoke_token(self, token: str) -> None:
        if token in self._tokens:
            self._tokens[token]["status"] = "revoked"
            self._save_tokens()
            self.audit.append("approval_revoked", self._tokens[token])

    def is_approved(self, token: str) -> bool:
        rec = self._tokens.get(token)
        return bool(rec and rec.get("status") == "approved" and time.time() <= rec["expires_at"])
