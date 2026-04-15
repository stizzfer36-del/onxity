from __future__ import annotations

import time
import uuid

from onxity.memory.sqlite_store import add_audit_db, get_session
from onxity.security.audit import AuditWriter


class ApprovalModule:
    _tokens: dict[str, dict] = {}

    def __init__(self, config: dict):
        self.config = config
        self.audit = AuditWriter(config)

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
            raise ValueError("expired token")
        rec["status"] = "approved"
        rec["operator"] = operator
        rec["attestation_text"] = attestation_text
        rec["approved_ts"] = time.time()
        self.audit.append("approval_granted", rec)
        try:
            add_audit_db(get_session(), "approval_granted", rec)
        except Exception:
            pass
        return rec

    def revoke_token(self, token: str) -> None:
        if token in self._tokens:
            self._tokens[token]["status"] = "revoked"
            self.audit.append("approval_revoked", self._tokens[token])

    def is_approved(self, token: str) -> bool:
        rec = self._tokens.get(token)
        return bool(rec and rec.get("status") == "approved" and time.time() <= rec["expires_at"])
