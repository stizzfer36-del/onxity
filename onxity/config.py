"""
onxity.config
=============
Load, save, and provide defaults for ~/.onxity/config.yaml.

Env interpolation: ${ENV_VAR} in values is replaced at load time.
If the variable is not set, the literal default is preserved.
"""

import os
import re
from pathlib import Path
from typing import Optional

import yaml

ONXITY_DIR = Path.home() / ".onxity"
CONFIG_PATH = ONXITY_DIR / "config.yaml"

_ENV_RE = re.compile(r"\$\{([^}]+)\}")


def _interpolate(value: str) -> str:
    """Replace ${ENV_VAR} tokens with environment variable values."""
    def replacer(m):
        return os.environ.get(m.group(1), m.group(0))
    return _ENV_RE.sub(replacer, value)


def _interpolate_dict(d: dict) -> dict:
    """Recursively interpolate env vars in a config dict."""
    result = {}
    for k, v in d.items():
        if isinstance(v, str):
            result[k] = _interpolate(v)
        elif isinstance(v, dict):
            result[k] = _interpolate_dict(v)
        else:
            result[k] = v
    return result


def default_config() -> dict:
    """Return a safe default configuration."""
    onxity_dir = str(ONXITY_DIR)
    return {
        "config_path": str(CONFIG_PATH),
        "provider": os.environ.get("ONXITY_PROVIDER", "mock"),
        "db_path": str(ONXITY_DIR / "onxity.db"),
        "audit_path": str(ONXITY_DIR / "audit.jsonl"),
        "plugin_dir": str(ONXITY_DIR / "plugins"),
        "permissions": {
            "fs:read": "allow",
            "fs:write": "prompt",
            "execute": "prompt",
            "network": "prompt",
            "hardware": "deny",
            "spawn": "prompt",
            "git": "allow",
        },
        "memory": {
            "max_items": 50,
            "max_bytes": 102400,  # 100 KB
            "compress_threshold": 40,
        },
        "sandbox": {
            "timeout": 10,  # seconds
            "max_cpu_seconds": 5,
            "max_open_files": 64,
        },
        "approval": {
            "token_expiry_seconds": 86400,  # 24 hours
        },
        "allowed_roots": [str(Path.home())],
        "max_subagent_depth": 2,
        "max_retries": 3,
        "retry_backoff_base": 1.5,
        "telemetry": False,
    }


def load_config(path: Optional[str] = None) -> dict:
    """
    Load config from path (default ~/.onxity/config.yaml).
    Falls back to defaults for missing keys.
    Applies env interpolation on all string values.
    """
    cfg_path = Path(path) if path else CONFIG_PATH
    cfg = default_config()

    if cfg_path.exists():
        with open(cfg_path, "r") as f:
            loaded = yaml.safe_load(f) or {}
        cfg.update(loaded)

    cfg = _interpolate_dict(cfg)
    cfg["config_path"] = str(cfg_path)
    return cfg


def save_config(cfg: dict, path: Optional[str] = None) -> None:
    """
    Save config dict to path (default ~/.onxity/config.yaml).
    Creates ~/.onxity/ directory if missing.
    """
    cfg_path = Path(path) if path else CONFIG_PATH
    cfg_path.parent.mkdir(parents=True, exist_ok=True)

    # Don't persist runtime-only keys
    to_save = {k: v for k, v in cfg.items() if k != "config_path"}
    with open(cfg_path, "w") as f:
        yaml.dump(to_save, f, default_flow_style=False, sort_keys=True)
