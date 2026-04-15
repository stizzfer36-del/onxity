from __future__ import annotations

import uuid
from dataclasses import dataclass

from onxity.core.approval import ApprovalModule
from onxity.security.audit import AuditWriter
from onxity.security.permissions import evaluate_scopes


@dataclass
class ToolMeta:
    name: str
    description: str
    required_scopes: list[str]


def tool(name: str, description: str, required_scopes: list[str]):
    def deco(func):
        func._tool_meta = ToolMeta(name=name, description=description, required_scopes=required_scopes)
        return func

    return deco


class ToolRegistry:
    def __init__(self, config: dict):
        self.config = config
        self.audit = AuditWriter(config)
        self.approvals = ApprovalModule(config)
        self._tools: dict[str, callable] = {}
        try:
            from onxity.tools.system.filesystem import configure_allowed_roots
            configure_allowed_roots(config.get("allowed_roots", []))
        except Exception:
            pass

    def register(self, func):
        meta = getattr(func, "_tool_meta", None)
        if not meta:
            raise ValueError("tool missing @tool decorator")
        self._tools[meta.name] = func

    def get_tool(self, name: str):
        return self._tools.get(name)

    def dispatch(self, agent_id: str, tool_name: str, args: dict, actor_scopes: list[str] | None = None) -> dict:
        trace_id = str(uuid.uuid4())
        fn = self.get_tool(tool_name)
        if not fn:
            return {"status": "error", "error": f"unknown tool {tool_name}"}
        meta = fn._tool_meta
        decision, missing = evaluate_scopes(meta.required_scopes, self.config.get("permissions", {}))
        if decision == "deny":
            payload = {"agent_id": agent_id, "tool": tool_name, "args_redacted": args, "required_scopes": meta.required_scopes,
                      "outcome": "denied", "reason": "permission_denied", "trace_id": trace_id}
            self.audit.append("tool_call", payload)
            return {"status": "denied", "reason": "permission_denied", "missing": missing}
        if decision == "prompt":
            if self.config.get("auto_approve"):
                pass
            else:
                token = self.approvals.create_approval_request(agent_id, missing, f"tool={tool_name}", self.config["approval"]["token_expiry_seconds"])
                self.audit.append("tool_call", {"agent_id": agent_id, "tool": tool_name, "args_redacted": args, "required_scopes": meta.required_scopes,
                                                "approval_token": token, "outcome": "pending_approval", "trace_id": trace_id})
                return {"status": "pending_approval", "approval_token": token}
        try:
            result = fn(**args)
            self.audit.append("tool_call", {"agent_id": agent_id, "tool": tool_name, "args_redacted": args, "required_scopes": meta.required_scopes,
                                            "outcome": "ok", "trace_id": trace_id})
            return {"status": "ok", "result": result}
        except Exception as exc:
            self.audit.append("tool_call", {"agent_id": agent_id, "tool": tool_name, "args_redacted": args, "required_scopes": meta.required_scopes,
                                            "outcome": "error", "error": str(exc), "trace_id": trace_id})
            return {"status": "error", "error": str(exc)}
