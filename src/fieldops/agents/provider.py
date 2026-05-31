from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from google import genai

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
        # The orchestrator currently uses direct prompt contracts for planner/schema/summarizer.
        # Native function-call handling is wired through the provider adapter in the SQL agent.
        contents: list[Any] = [prompt]
        if tool_result is not None:
            contents.append(f"Tool result: {tool_result.payload()}")
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
        )
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

