"""
onxity.providers.anthropic
==========================
Anthropic Claude provider stub.

TODO Implementation Notes
--------------------------
Inputs:
  messages: list[dict] with keys 'role' ('user'|'assistant'|'system') and 'content' (str).
  tools: list[dict] in Anthropic tool_use schema format.

Outputs:
  ProviderResponse with .content = JSON string of the CEO plan.

Errors:
  NotConfiguredError  — ANTHROPIC_API_KEY not set.
  ProviderTimeoutError — httpx/requests read timeout.

Real implementation steps:
  1. pip install anthropic
  2. client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
  3. response = client.messages.create(
         model="claude-opus-4-5",
         max_tokens=4096,
         system=SYSTEM_PROMPT,
         messages=messages,
         tools=tools,
     )
  4. Extract response.content[0].text as plan JSON.
  5. Handle anthropic.APITimeoutError -> raise ProviderTimeoutError.

Streaming (future):
  def stream(self, messages, tools):
      with client.messages.stream(...) as s:
          for text in s.text_stream:
              yield text

Test fixture:
  @pytest.fixture
  def anthropic_provider(monkeypatch):
      monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
      return AnthropicProvider({})
"""

import os

from onxity.providers.base import BaseProvider, ProviderResponse, NotConfiguredError, ProviderTimeoutError


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider. Raises NotConfiguredError if API key missing."""

    def __init__(self, config: dict):
        self.config = config
        self.api_key = os.environ.get("ANTHROPIC_API_KEY") or config.get("anthropic_api_key", "")
        if not self.api_key:
            raise NotConfiguredError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Export it or set anthropic_api_key in config.yaml."
            )

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> ProviderResponse:
        """
        TODO: Implement real Anthropic API call.
        See module docstring for steps.
        """
        # TODO: import anthropic; call client.messages.create(); return ProviderResponse
        raise NotImplementedError("AnthropicProvider.complete not yet implemented. See module docstring.")
