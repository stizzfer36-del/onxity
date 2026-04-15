from __future__ import annotations

import importlib.util
import os
import platform
import site
import sys
from pathlib import Path

from onxity.config import default_config, load_config


def _writable(path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8"):
            pass
        return True
    except Exception:
        return False


def collect_diagnostics() -> dict:
    cfg = load_config() if Path(default_config()["config_path"]).expanduser().exists() else default_config()
    repo_root = Path(__file__).resolve().parent.parent
    py = sys.version.split()[0]
    onxity_importable = importlib.util.find_spec("onxity") is not None
    return {
        "os": platform.platform(),
        "python": py,
        "python_executable": sys.executable,
        "pip_hint": f"{sys.executable} -m pip --version",
        "site_packages": site.getsitepackages() if hasattr(site, "getsitepackages") else [],
        "repo_root": str(repo_root),
        "cwd": os.getcwd(),
        "config_path": cfg["config_path"],
        "db_path": cfg["db_path"],
        "audit_path": cfg["audit_path"],
        "identity_path": cfg["identity_path"],
        "runtime_state_path": cfg["runtime_state_path"],
        "daemon_pid_path": cfg["daemon_pid_path"],
        "plugins_dir": cfg["onxity_plugin_dir"],
        "pack_registry_path": cfg["pack_registry_path"],
        "onxity_importable": onxity_importable,
        "paths_writable": {
            "config_path": _writable(Path(cfg["config_path"]).expanduser()),
            "db_path": _writable(Path(cfg["db_path"]).expanduser()),
            "audit_path": _writable(Path(cfg["audit_path"]).expanduser()),
            "runtime_state_path": _writable(Path(cfg["runtime_state_path"]).expanduser()),
            "plugins_dir": Path(cfg["onxity_plugin_dir"]).expanduser().exists() or _writable(Path(cfg["onxity_plugin_dir"]).expanduser() / ".touch"),
        },
    }
