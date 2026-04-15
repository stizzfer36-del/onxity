from __future__ import annotations

SCOPE_FS_READ = "fs:read"
SCOPE_FS_WRITE = "fs:write"
SCOPE_EXECUTE = "execute"
SCOPE_NETWORK = "network"
SCOPE_HARDWARE = "hardware"
SCOPE_SPAWN = "spawn"
SCOPE_GIT = "git"


def evaluate_scopes(required: list[str], config_permissions: dict) -> tuple[str, list[str]]:
    if not required:
        return "allow", []
    denied, prompted = [], []
    for scope in required:
        decision = config_permissions.get(scope, "deny")
        if decision == "deny":
            denied.append(scope)
        elif decision == "prompt":
            prompted.append(scope)
    if denied:
        return "deny", denied
    if prompted:
        return "prompt", prompted
    return "allow", []
