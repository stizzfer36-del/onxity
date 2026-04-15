from __future__ import annotations

from dataclasses import dataclass, field

from onxity.kernel.policy import classify_risk, compute_budget
from onxity.security.audit import AuditWriter


@dataclass
class WorkerPolicy:
    max_depth: int = 2
    max_workers: int = 4
    allowed_tools: list[str] = field(default_factory=list)


class TeamOrchestrator:
    """Governed worker spawning and execution boundaries."""

    def __init__(self, config: dict):
        self.config = config
        self.audit = AuditWriter(config)
        self.policy = WorkerPolicy(
            max_depth=int(config.get("agency", {}).get("max_depth", 2)),
            max_workers=int(config.get("agency", {}).get("max_workers", 4)),
            allowed_tools=list(config.get("agency", {}).get("allowed_tools", [])),
        )
        self.workers: dict[str, dict] = {}

    def spawn_worker(self, worker_id: str, parent_id: str, depth: int, scopes: list[str]) -> dict:
        if depth > self.policy.max_depth:
            rec = {"status": "denied", "reason": "max_depth"}
            self.audit.append("worker_spawn_denied", {"worker_id": worker_id, "depth": depth})
            return rec
        if len(self.workers) >= self.policy.max_workers:
            rec = {"status": "denied", "reason": "max_workers"}
            self.audit.append("worker_spawn_denied", {"worker_id": worker_id, "count": len(self.workers)})
            return rec
        risk = classify_risk(scopes)
        budget = compute_budget(self.config, risk)
        rec = {"status": "ok", "worker_id": worker_id, "parent_id": parent_id, "depth": depth, "risk": risk, "budget": budget}
        self.workers[worker_id] = rec
        self.audit.append("worker_spawn", rec)
        return rec

    def verify_result(self, worker_id: str, result: dict) -> dict:
        status = "ok" if result.get("status") in {"ok", "pending_approval", "denied"} else "needs_recovery"
        out = {"worker_id": worker_id, "verdict": status, "result": result}
        self.audit.append("worker_verify", out)
        return out

    def recovery_plan(self, worker_id: str, failure: dict) -> dict:
        plan = {
            "worker_id": worker_id,
            "action": "rollback_or_report",
            "reason": failure.get("error", "unknown"),
            "steps": ["capture_snapshot", "stop_worker", "escalate_to_operator"],
        }
        self.audit.append("worker_recovery", plan)
        return plan
