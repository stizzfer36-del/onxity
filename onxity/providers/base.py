"""
onxity.providers.base
=====================
BaseProvider abstraction and MockProvider for unit tests.

MockProvider behavior:
  - Input starting with "show " → returns a filesystem.read plan (Example 1).
  - Input containing "fetch cve" → returns a network.fetch plan requiring network scope (Example 2).
  - All other inputs → generic single-step echo plan.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any


class ProviderTimeoutError(Exception):
    """Raised when provider call exceeds timeout."""


class NotConfiguredError(Exception):
    """Raised when a required API key or config is missing."""


class PlanValidationError(Exception):
    """Raised when CEO plan JSON fails schema validation."""


@dataclass
class ProviderResponse:
    """Structured response from a provider."""
    content: str
    model: str = "mock"
    usage: dict = field(default_factory=dict)
    raw: Any = None


class BaseProvider:
    """
    Abstract provider. All real providers must subclass this.

    Methods
    -------
    complete(messages, tools) -> ProviderResponse
        Synchronous completion. Returns ProviderResponse or raises
        ProviderTimeoutError / NotConfiguredError.

    TODO (streaming):
        def stream(self, messages, tools) -> Iterator[str]:
            Yield text tokens as they arrive from the provider.
            Implement in subclasses for streaming UX.
    """

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> ProviderResponse:
        raise NotImplementedError


class MockProvider(BaseProvider):
    """
    Deterministic mock provider for unit tests and CI.

    Returns valid JSON plan strings based on input content.
    """

    model = "mock-v1"

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> ProviderResponse:
        """
        Inspect the last user message and return a matching plan JSON.

        Examples
        --------
        >>> p = MockProvider()
        >>> r = p.complete([{"role": "user", "content": "show /etc/issue"}])
        >>> plan = json.loads(r.content)
        >>> plan["steps"][0]["tool"]
        'filesystem.read'

        >>> r2 = p.complete([{"role": "user", "content": "fetch cve data"}])
        >>> plan2 = json.loads(r2.content)
        >>> plan2["steps"][0]["requires"]
        ['network']
        """
        user_text = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_text = m.get("content", "")
                break

        plan = self._build_plan(user_text)
        return ProviderResponse(content=json.dumps(plan), model=self.model)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_plan(self, user_text: str) -> dict:
        lower = user_text.lower()

        # Example 1: simple safe read
        if lower.startswith("show "):
            path = user_text[5:].strip() or "/etc/issue"
            return {
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

        # Example 2: network fetch requiring approval
        if "fetch cve" in lower or "cve" in lower:
            return {
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

        # Generic fallback plan
        return {
            "steps": [
                {
                    "id": f"s-{uuid.uuid4().hex[:6]}",
                    "action": "echo",
                    "tool": "system.echo",
                    "args": {"message": user_text},
                    "requires": [],
                    "proof_required": False,
                    "proof": [],
                }
            ]
        }
