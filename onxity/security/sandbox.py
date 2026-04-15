"""
onxity.security.sandbox
=======================
Subprocess sandbox helper used by onxity/tools/code/executor.py.

Provides:
  - make_preexec_fn(cpu_seconds, max_open_files) -> callable
      Returns a preexec_fn for subprocess.Popen that sets resource limits.
  - run_sandboxed(argv, timeout, cpu_seconds, max_open_files, cwd) -> dict
      Runs a subprocess with limits and captures output.

Windows TODO:
  resource.setrlimit is POSIX-only. On Windows:
  - Use subprocess with a Job Object via ctypes or pywin32.
  - STARTUPINFO can hide console windows.
  - Consider using a Docker container or WSL for sandboxing.
  - Reference: https://docs.microsoft.com/en-us/windows/win32/procthread/job-objects
"""

import subprocess
import sys
import tempfile
from typing import Any


def make_preexec_fn(cpu_seconds: int = 5, max_open_files: int = 64):
    """
    Return a preexec_fn that sets POSIX resource limits.

    Called in the child process before exec, so it does not affect
    the parent onxity process.

    Limits set
    ----------
    RLIMIT_CPU  : cpu_seconds (hard + soft)
    RLIMIT_NOFILE: max_open_files (hard + soft)
    """
    if sys.platform == "win32":
        # TODO: implement Windows Job Object equivalent
        return None

    def _set_limits():
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
            resource.setrlimit(resource.RLIMIT_NOFILE, (max_open_files, max_open_files))
        except Exception:
            pass  # Best-effort; don't crash the child

    return _set_limits


def run_sandboxed(
    argv: list[str],
    timeout: int = 10,
    cpu_seconds: int = 5,
    max_open_files: int = 64,
    cwd: str | None = None,
) -> dict:
    """
    Run a command in a sandboxed subprocess.

    Parameters
    ----------
    argv:
        Command as a list (shell=False). E.g. ['python3', 'script.py'].
    timeout:
        Wall-clock timeout in seconds. Process killed on expiry.
    cpu_seconds:
        POSIX RLIMIT_CPU. Kills child if it uses more CPU than this.
    max_open_files:
        POSIX RLIMIT_NOFILE.
    cwd:
        Working directory. If None, a TemporaryDirectory is created and
        cleaned up after the call.

    Returns
    -------
    dict with keys:
      exit_code  : int | None
      stdout     : str
      stderr     : str
      timed_out  : bool
      cwd        : str
    """
    preexec = make_preexec_fn(cpu_seconds=cpu_seconds, max_open_files=max_open_files)
    _tmp_dir = None

    if cwd is None:
        _tmp_dir = tempfile.TemporaryDirectory(prefix="onxity_sandbox_")
        cwd = _tmp_dir.name

    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            shell=False,
            preexec_fn=preexec,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": False,
            "cwd": cwd,
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "timed_out": True,
            "cwd": cwd,
            "error": "timeout",
        }
    except Exception as exc:
        return {
            "exit_code": None,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
            "cwd": cwd,
            "error": str(exc),
        }
    finally:
        if _tmp_dir:
            _tmp_dir.cleanup()
