"""
onxity.providers.openai
=======================
OpenAI provider stub.

TODO Implementation Notes
--------------------------
Inputs:
  messages: list[dict] with keys 'role' and 'content'.
  tools: list[dict] in OpenAI function-calling schema format.

Outputs:
  ProviderResponse with .content = JSON string of the CEO plan.

Errors:
  NotConfiguredError  — OPENAI_API_KEY not set.
  ProviderTimeoutError — openai.APITimeoutError.

Real implementation steps:
  1. pip install openai
  2. client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
  3. response = client.chat.completions.create(
         model="gpt-4o",
         messages=messages,
         tools=tools,
         response_format={"type": "json_object"},
     )
  4. Extract response.choices[0].message.content as plan JSON.
  5. Handle openai.APITimeoutError -> raise ProviderTimeoutError.

Streaming (future):
  def stream(self, messages, tools):
      for chunk in client.chat.completions.create(stream=True, ...):
          yield chunk.choices[0].delta.content or ""

Test fixture:
  @pytest.fixture
  def openai_provider(monkeypatch):
      monkeypatch.setenv("OPENAI_API_KEY", "test-key")
      return OpenAIProvider({})
"""

import os

from onxity.providers.base import BaseProvider, ProviderResponse, NotConfiguredError, ProviderTimeoutError


class OpenAIProvider(BaseProvider):
    """OpenAI GPT provider. Raises NotConfiguredError if API key missing."""

    def __init__(self, config: dict):
        self.config = config
        self.api_key = os.environ.get("OPENAI_API_KEY") or config.get("openai_api_key", "")
        if not self.api_key:
            raise NotConfiguredError(
                "OPENAI_API_KEY environment variable not set. "
                "Export it or set openai_api_key in config.yaml."
            )

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> ProviderResponse:
        """
        TODO: Implement real OpenAI API call.
        See module docstring for steps.
        """
        # TODO: import openai; call client.chat.completions.create(); return ProviderResponse
        raise NotImplementedError("OpenAIProvider.complete not yet implemented. See module docstring.")
