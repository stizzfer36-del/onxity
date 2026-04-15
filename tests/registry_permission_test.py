from __future__ import annotations

import json

from onxity.core.approval import ApprovalModule
from onxity.tools.registry import ToolRegistry
from onxity.tools.system.filesystem import filesystem_read, filesystem_write


def test_deny_write_scope(tmp_config, tmp_path):
    cfg = tmp_config
    cfg["permissions"]["fs:write"] = "deny"
    r = ToolRegistry(cfg)
    r.register(filesystem_write)
    resp = r.dispatch("a1", "filesystem.write", {"path": str(tmp_path / "x.txt"), "content": "x"}, [])
    assert resp["status"] == "denied"
    assert "fs:write" in resp["missing"]


def test_prompt_network_approval_flow(tmp_config):
    cfg = tmp_config
    cfg["permissions"]["network"] = "prompt"
    reg = ToolRegistry(cfg)

    from onxity.tools.registry import tool

    @tool("network.fetch", "fetch", ["network"])
    def fetch(url: str):
        return {"url": url}

    reg.register(fetch)
    pending = reg.dispatch("a1", "network.fetch", {"url": "https://example.com"}, [])
    assert pending["status"] == "pending_approval"
    token = pending["approval_token"]
    appr = ApprovalModule(cfg).approve_token(token, "op", "I am authorized")
    assert appr["status"] == "approved"
