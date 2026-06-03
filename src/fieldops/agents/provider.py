from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from google import genai
from google.genai import types

from fieldops.tools.gemini_adapter import GeminiToolAdapter
from fieldops.tools.protocol import InternalToolCall, InternalToolResult, ToolCatalog


@dataclass(frozen=True)
class ModelResponse:
    text: str = ""
    tool_call: InternalToolCall | None = None


class ModelProvider(Protocol):
    async def generate(
        self,
        prompt: str,
        *,
        tools: ToolCatalog | None = None,
        tool_result: InternalToolResult | None = None,
    ) -> ModelResponse: ...


class ModelProviderError(RuntimeError):
    """Raised when a provider call fails in a user-facing way."""


class GeminiProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        *,
        tools: ToolCatalog | None = None,
        tool_result: InternalToolResult | None = None,
    ) -> ModelResponse:
        contents: list[Any] = [prompt]
        config: types.GenerateContentConfig | None = None

        adapter = GeminiToolAdapter(tools) if tools is not None else None
        if tool_result is not None:
            contents.append(f"Tool result: {tool_result.payload()}")
        if adapter is not None:
            config = types.GenerateContentConfig(
                tools=adapter.to_provider_tools(),
                toolConfig=types.ToolConfig(
                    functionCallingConfig=types.FunctionCallingConfig(mode="ANY")
                ),
            )
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            raise ModelProviderError(
                f"Gemini request failed for model `{self.model}`: {exc}"
            ) from exc
        function_call = _extract_function_call(response)
        if function_call is not None and adapter is not None:
            return ModelResponse(tool_call=adapter.normalize_call(function_call))
        return ModelResponse(text=response.text or "")


class FakeProvider:
    def __init__(self, responses: list[ModelResponse] | None = None) -> None:
        self.responses = responses or []
        self.prompts: list[str] = []

    async def generate(
        self,
        prompt: str,
        *,
        tools: ToolCatalog | None = None,
        tool_result: InternalToolResult | None = None,
    ) -> ModelResponse:
        self.prompts.append(prompt)
        if self.responses:
            return self.responses.pop(0)
        return ModelResponse(text="No fake response configured.")


def _extract_function_call(response: Any) -> types.FunctionCall | None:
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            function_call = getattr(part, "function_call", None)
            if function_call is not None:
                return function_call
    return None
