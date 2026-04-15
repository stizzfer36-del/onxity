from __future__ import annotations

import os
import platform
import socket
import sys
import time
from pathlib import Path

import psutil

from onxity.tools.registry import tool


@tool(name="host.health", description="Host health sweep", required_scopes=["fs:read"])
def host_health() -> dict:
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(str(Path.home()))
    return {
        "ts": time.time(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": mem.percent,
        "disk_percent_home": disk.percent,
        "pid": os.getpid(),
    }


@tool(name="process.list", description="List active processes", required_scopes=["execute"])
def process_list(limit: int = 30) -> dict:
    out = []
    for proc in psutil.process_iter(attrs=["pid", "name", "status", "username"]):
        out.append(proc.info)
        if len(out) >= limit:
            break
    return {"processes": out}
