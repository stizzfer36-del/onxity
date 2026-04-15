from __future__ import annotations

import subprocess
import tempfile


def setrlimits(cpu_seconds: int, max_open_files: int):
    def _inner():
        try:
            import resource

            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
            resource.setrlimit(resource.RLIMIT_NOFILE, (max_open_files, max_open_files))
        except Exception:
            return

    return _inner


def run_with_timeout(argv: list[str], timeout: int, cpu_seconds: int, max_open_files: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="onxity_exec_") as wd:
        try:
            cp = subprocess.run(
                argv,
                shell=False,
                timeout=timeout,
                cwd=wd,
                capture_output=True,
                text=True,
                preexec_fn=setrlimits(cpu_seconds, max_open_files),
            )
            return {"exit_code": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr, "timed_out": False, "cwd": wd}
        except subprocess.TimeoutExpired:
            return {"exit_code": None, "stdout": "", "stderr": "", "timed_out": True, "error": "timeout", "cwd": wd}

# TODO Windows: use Job Objects/STARTUPINFO to enforce resource limits and process-tree kill.
