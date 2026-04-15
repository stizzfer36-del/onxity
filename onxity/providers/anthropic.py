from __future__ import annotations

import os

from onxity.providers.base import BaseProvider, NotConfiguredError


class AnthropicProvider(BaseProvider):
    def __init__(self, cfg: dict):
        self.cfg = cfg

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise NotConfiguredError("ANTHROPIC_API_KEY missing")
        # TODO: wire official Anthropic SDK request/response mapping.
        # Input: OpenAI-style messages/tools.
        # Output: {'content': '<JSON plan string>'}.
        return {"content": '{"steps": []}'}
