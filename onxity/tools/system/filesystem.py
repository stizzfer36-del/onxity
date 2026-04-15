from __future__ import annotations

from pathlib import Path

from onxity.tools.registry import tool

_ALLOWED_ROOTS = [Path.home()]


def configure_allowed_roots(roots: list[str]):
    global _ALLOWED_ROOTS
    _ALLOWED_ROOTS = [Path(p).expanduser().resolve() for p in roots]


def _assert_allowed(path: str):
    roots = _ALLOWED_ROOTS
    rp = Path(path).expanduser().resolve()
    if not any(str(rp).startswith(str(root)) for root in roots):
        raise PermissionError(f"Path outside allowed roots: {rp}")


@tool(
    name="filesystem.read",
    description="Read a file",
    required_scopes=["fs:read"],
)
def filesystem_read(path: str) -> dict:
    _assert_allowed(path)
    p = Path(path)
    content = p.read_text(encoding="utf-8", errors="ignore")
    return {"content": content, "size": len(content)}


@tool(
    name="filesystem.write",
    description="Write a file",
    required_scopes=["fs:write"],
)
def filesystem_write(path: str, content: str) -> dict:
    _assert_allowed(path)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"written": True}


@tool(
    name="filesystem.find",
    description="Find files by pattern",
    required_scopes=["fs:read"],
)
def filesystem_find(root: str, pattern: str) -> dict:
    _assert_allowed(root)
    rp = Path(root)
    matches = [str(p) for p in rp.rglob(pattern)]
    return {"matches": matches}


# TODO hardening: move to strict path whitelist/chroot-like jail and
# deny symlink escapes.
