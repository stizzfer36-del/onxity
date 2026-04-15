from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import yaml

ONXITY_HOME = Path.home() / ".onxity"
CONFIG_PATH = ONXITY_HOME / "config.yaml"
_ENV = re.compile(r"\$\{([^}]+)\}")


def default_config() -> dict:
    return {
        "config_path": str(CONFIG_PATH),
        "provider": os.getenv("ONXITY_PROVIDER", "mock"),
        "permissions": {
            "fs:read": "allow",
            "fs:write": "deny",
            "execute": "prompt",
            "network": "prompt",
            "hardware": "deny",
            "spawn": "prompt",
            "git": "prompt",
        },
        "memory": {"max_items": 50, "max_bytes": 262144, "compress_threshold": 40},
        "sandbox": {"timeout": 5, "ulimit_nofile": 64, "cpu_seconds": 2},
        "approval": {"token_expiry_seconds": 86400},
        "agency": {"max_depth": 2, "max_workers": 4, "allowed_tools": []},
        "daemon": {"heartbeat_seconds": 2},
        "budgets": {
            "low": {"max_steps": 10, "timeout_seconds": 20},
            "high": {"max_steps": 6, "timeout_seconds": 15},
            "severe": {"max_steps": 3, "timeout_seconds": 10},
        },
        "db_path": str(ONXITY_HOME / "onxity.db"),
        "audit_path": str(ONXITY_HOME / "audit.jsonl"),
        "identity_path": str(ONXITY_HOME / "identity.json"),
        "runtime_state_path": str(ONXITY_HOME / "runtime_state.json"),
        "daemon_pid_path": str(ONXITY_HOME / "daemon.pid"),
        "pack_registry_path": str(ONXITY_HOME / "packs.json"),
        "pack_signing_secret": os.getenv("ONXITY_PACK_SIGNING_SECRET", "dev-secret"),
        "onxity_plugin_dir": str(ONXITY_HOME / "plugins"),
        "allowed_roots": [str(Path.home())],
        "auto_approve": False,
    }


def _interp(v):
    if isinstance(v, str):
        return _ENV.sub(lambda m: os.getenv(m.group(1), m.group(0)), v)
    if isinstance(v, dict):
        return {k: _interp(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_interp(i) for i in v]
    return v


def load_config(path: Optional[str] = None) -> dict:
    cfg = default_config()
    p = Path(path) if path else CONFIG_PATH
    if p.exists():
        with p.open("r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
        for k, v in loaded.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    cfg = _interp(cfg)
    cfg["config_path"] = str(p)
    return cfg


def save_config(cfg: dict, path: Optional[str] = None) -> None:
    p = Path(path) if path else CONFIG_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    body = {k: v for k, v in cfg.items() if k != "config_path"}
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(body, f, sort_keys=False)
