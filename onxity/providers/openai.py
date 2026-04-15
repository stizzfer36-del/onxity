from __future__ import annotations

import os

from onxity.providers.base import BaseProvider, NotConfiguredError


class OpenAIProvider(BaseProvider):
    def __init__(self, cfg: dict):
        self.cfg = cfg

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        if not os.getenv("OPENAI_API_KEY"):
            raise NotConfiguredError("OPENAI_API_KEY missing")
        # TODO: wire OpenAI responses API with strict JSON schema enforcement.
        return {"content": '{"steps": []}'}
