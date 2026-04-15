from __future__ import annotations


def classify_risk(scopes: list[str]) -> str:
    severe = {"hardware", "spawn"}
    high = {"execute", "network", "git"}
    if any(s in severe for s in scopes):
        return "severe"
    if any(s in high for s in scopes):
        return "high"
    return "low"


def compute_budget(config: dict, risk: str) -> dict:
    budget_cfg = config.get("budgets", {})
    defaults = {
        "low": {"max_steps": 10, "timeout_seconds": 20},
        "high": {"max_steps": 6, "timeout_seconds": 15},
        "severe": {"max_steps": 3, "timeout_seconds": 10},
    }
    out = defaults.get(risk, defaults["low"]).copy()
    out.update(budget_cfg.get(risk, {}))
    return out
