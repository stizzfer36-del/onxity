from __future__ import annotations

from onxity.tools.code.executor import execute
from onxity.tools.registry import tool


@tool(name="terminal.exec", description="Execute command in sandbox", required_scopes=["execute"])
def terminal_exec(argv: list[str], timeout: int = 5) -> dict:
    if not argv:
        raise ValueError("argv required")
    return execute(argv=argv, timeout=timeout)
