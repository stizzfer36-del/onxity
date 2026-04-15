from __future__ import annotations

import urllib.request

from onxity.tools.registry import tool


@tool(name="browser.fetch", description="Fetch a URL as text", required_scopes=["network"])
def browser_fetch(url: str, timeout: int = 5, max_chars: int = 5000) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
    return {"url": url, "status": "ok", "content": body[:max_chars], "truncated": len(body) > max_chars}
