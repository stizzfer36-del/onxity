from __future__ import annotations

import json
from dataclasses import dataclass, field


class ProviderTimeoutError(Exception):
    pass


class NotConfiguredError(Exception):
    pass


class PlanValidationError(Exception):
    pass


@dataclass
class ProviderResponse:
    content: str
    model: str = "unknown"
    usage: dict = field(default_factory=dict)


class BaseProvider:
    def complete(self, messages: list[dict], tools: list[dict]) -> dict:
        raise NotImplementedError


class MockProvider(BaseProvider):
    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        msg = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
        lower = msg.lower()
        if lower.startswith("show "):
            path = msg.split(" ", 1)[1]
            return {
                "content": json.dumps(
                    {
                        "steps": [
                            {
                                "id": "s1",
                                "action": "read_file",
                                "tool": "filesystem.read",
                                "args": {"path": path},
                                "requires": ["fs:read"],
                                "proof_required": False,
                                "proof": [],
                            }
                        ]
                    }
                )
            }
        if "fetch" in lower and "cve" in lower:
            return {
                "content": json.dumps(
                    {
                        "steps": [
                            {
                                "id": "s2",
                                "action": "http_get",
                                "tool": "network.fetch",
                                "args": {"url": "https://example.com/cves.json"},
                                "requires": ["network"],
                                "proof_required": True,
                                "proof": ["memory_chunk:init"],
                            }
                        ]
                    }
                )
            }
        return {"content": json.dumps({"steps": []})}
