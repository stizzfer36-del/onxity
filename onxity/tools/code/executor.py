from __future__ import annotations

from onxity.security.sandbox import run_with_timeout


def execute(argv: list[str], timeout: int = 5, cpu_seconds: int = 2, max_open_files: int = 64) -> dict:
    return run_with_timeout(argv, timeout=timeout, cpu_seconds=cpu_seconds, max_open_files=max_open_files)

# TODO implement per-call working directory policy injection.
