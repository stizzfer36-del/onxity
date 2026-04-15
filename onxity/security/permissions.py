"""
onxity.security.permissions
============================
Permission scope constants and evaluation logic.

Scope evaluation matrix
-----------------------
Config value | evaluate_scopes return
  'allow'    | ('allow', [])
  'prompt'   | ('prompt', [missing scope])
  'deny'     | ('deny',  [missing scope])
  missing    | ('deny',  [missing scope])  <- safe default

Examples
--------
>>> cfg = {"permissions": {"fs:read": "allow", "network": "prompt", "hardware": "deny"}}
>>> evaluate_scopes(["fs:read"], cfg["permissions"])
('allow', [])
>>> evaluate_scopes(["network"], cfg["permissions"])
('prompt', ['network'])
>>> evaluate_scopes(["hardware"], cfg["permissions"])
('deny', ['hardware'])
>>> evaluate_scopes(["fs:read", "network"], cfg["permissions"])
('prompt', ['network'])
>>> evaluate_scopes(["unknown_scope"], cfg["permissions"])
('deny', ['unknown_scope'])
"""

from typing import Literal

# Scope constants
SCOPE_FS_READ = "fs:read"
SCOPE_FS_WRITE = "fs:write"
SCOPE_EXECUTE = "execute"
SCOPE_NETWORK = "network"
SCOPE_HARDWARE = "hardware"
SCOPE_SPAWN = "spawn"
SCOPE_GIT = "git"

ALL_SCOPES = [
    SCOPE_FS_READ,
    SCOPE_FS_WRITE,
    SCOPE_EXECUTE,
    SCOPE_NETWORK,
    SCOPE_HARDWARE,
    SCOPE_SPAWN,
    SCOPE_GIT,
]

HIGH_RISK_SCOPES = [SCOPE_EXECUTE, SCOPE_NETWORK, SCOPE_HARDWARE, SCOPE_SPAWN]

Decision = Literal["allow", "deny", "prompt"]


def evaluate_scopes(
    required: list[str],
    config_permissions: dict,
) -> tuple[Decision, list[str]]:
    """
    Evaluate whether a set of required scopes is allowed given config.

    Returns the most restrictive decision and a list of scopes driving that decision.
    Priority: deny > prompt > allow.

    Parameters
    ----------
    required:
        List of scope strings that a tool requires.
    config_permissions:
        Dict mapping scope -> 'allow' | 'deny' | 'prompt'.

    Returns
    -------
    (decision, missing_scopes)
        decision:      'allow' | 'deny' | 'prompt'
        missing_scopes: scopes that triggered prompt or deny.
    """
    if not required:
        return "allow", []

    denied = []
    prompted = []

    for scope in required:
        setting = config_permissions.get(scope, "deny")  # safe default
        if setting == "deny":
            denied.append(scope)
        elif setting == "prompt":
            prompted.append(scope)
        # 'allow' — no action needed

    if denied:
        return "deny", denied
    if prompted:
        return "prompt", prompted
    return "allow", []
