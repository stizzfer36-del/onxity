from __future__ import annotations

import time

from onxity.kernel.events import EventBus
from onxity.kernel.policy import classify_risk, compute_budget
from onxity.providers.base import ProviderTimeoutError
from onxity.security.audit import AuditWriter


class _Metrics:
    onxity_plan_steps_total = 0
    onxity_tool_calls_total = 0
    onxity_approvals_total = 0
    onxity_subagent_spawns_total = 0
    onxity_errors_total = 0


class Orchestrator:
    def __init__(self, agent, registry, config: dict, event_bus: EventBus | None = None):
        self.agent = agent
        self.registry = registry
        self.config = config
        self.audit = AuditWriter(config)
        self.metrics = _Metrics()
        self.event_bus = event_bus or EventBus()

    def execute_plan(self, agent_id: str, plan: dict) -> dict:
        out = []
        retries = int(self.config.get("max_retries", 3))
        base = float(self.config.get("retry_backoff_base", 1.5))

        all_scopes = [scope for step in plan.get("steps", []) for scope in step.get("requires", [])]
        risk = classify_risk(all_scopes)
        budget = compute_budget(self.config, risk)
        if len(plan.get("steps", [])) > budget["max_steps"]:
            return {"status": "denied", "reason": "budget_exceeded", "budget": budget}

        plan_start = time.time()
        for step in plan.get("steps", []):
            if time.time() - plan_start > budget["timeout_seconds"]:
                return {"status": "error", "error": "plan_timeout", "tool_results": out}

            self.metrics.onxity_plan_steps_total += 1
            self.event_bus.publish("plan_step_start", {"agent_id": agent_id, "step": step})
            attempt = 0
            while True:
                try:
                    resp = self.registry.dispatch(agent_id, step["tool"], step.get("args", {}), step.get("requires", []))
                    self.metrics.onxity_tool_calls_total += 1
                    if resp.get("status") == "pending_approval":
                        self.metrics.onxity_approvals_total += 1
                        self.event_bus.publish("plan_pending_approval", {"agent_id": agent_id, "step": step, "response": resp})
                        return {"status": "pending_approval", "approval_token": resp["approval_token"], "tool_results": out}
                    out.append({"step_id": step["id"], "response": resp})
                    self.event_bus.publish("plan_step_complete", {"agent_id": agent_id, "step": step, "response": resp})
                    break
                except ProviderTimeoutError as exc:
                    attempt += 1
                    if attempt > retries:
                        self.metrics.onxity_errors_total += 1
                        self.audit.append("error", {"error": str(exc), "step": step})
                        return {"status": "error", "error": str(exc), "tool_results": out}
                    time.sleep(base**attempt)
                except Exception as exc:
                    self.metrics.onxity_errors_total += 1
                    out.append({"step_id": step["id"], "response": {"status": "error", "error": str(exc)}})
                    self.event_bus.publish("plan_step_error", {"agent_id": agent_id, "step": step, "error": str(exc)})
                    break
        return {"status": "ok", "tool_results": out, "budget": budget, "risk": risk}
