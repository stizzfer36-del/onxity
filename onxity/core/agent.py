from __future__ import annotations

import json
import time

from onxity.providers.base import BaseProvider, PlanValidationError
from onxity.security.audit import AuditWriter

SYSTEM_PROMPT_TEMPLATE = (
    "You are onxity CEO agent. Return ONLY JSON object matching schema {steps:[...]} with requires list and proof-first. "
    "For destructive/network/hardware scopes set proof_required true with proof references."
)


class CeoAgent:
    def __init__(self, id: str, provider: BaseProvider, memory, config: dict):
        self.id = id
        self.provider = provider
        self.memory = memory
        self.config = config
        self.audit = AuditWriter(config)

    def plan(self, user_input: str) -> dict:
        self.audit.append("user_turn", {"agent_id": self.id, "input": user_input})
        msgs = [{"role": "system", "content": SYSTEM_PROMPT_TEMPLATE}, {"role": "user", "content": user_input}]
        resp = self.provider.complete(msgs, [])
        raw = resp["content"] if isinstance(resp, dict) else resp.content
        try:
            plan = json.loads(raw)
        except Exception as exc:
            self.audit.append("plan_error", {"error": str(exc), "raw": raw})
            raise PlanValidationError("invalid JSON")
        self._validate_plan(plan)
        self.audit.append("plan", {"plan_json": plan})
        return plan

    def _validate_plan(self, plan: dict) -> None:
        if not isinstance(plan, dict) or "steps" not in plan or not isinstance(plan["steps"], list):
            raise PlanValidationError("plan must be object with steps list")
        seen = set()
        for step in plan["steps"]:
            for key in ["id", "action", "tool", "args", "requires", "proof_required"]:
                if key not in step:
                    raise PlanValidationError(f"missing {key}")
            if step["id"] in seen:
                raise PlanValidationError("duplicate step id")
            seen.add(step["id"])
            if step["proof_required"] and not step.get("proof"):
                raise PlanValidationError("proof required")

    def synthesize(self, tool_results: list[dict]) -> dict:
        msg = "No actions executed." if not tool_results else "\n".join(str(x) for x in tool_results)
        final = {"final_message": msg, "memory_write": {"ts": time.time(), "tool_results": tool_results}}
        self.memory.append(final["memory_write"])
        self.audit.append("synthesis", final)
        return final
