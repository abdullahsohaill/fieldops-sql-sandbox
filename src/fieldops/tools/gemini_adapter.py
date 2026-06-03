from __future__ import annotations

from typing import Any

from google.genai import types

from fieldops.tools.protocol import (
    InternalToolCall,
    InternalToolResult,
    InternalToolSpec,
    ToolCatalog,
)


class GeminiToolAdapter:
    provider = "gemini"

    def __init__(self, catalog: ToolCatalog) -> None:
        self.catalog = catalog

    def to_provider_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                functionDeclarations=[
                    types.FunctionDeclaration(
                        name=tool.name,
                        description=tool.description,
                        parametersJsonSchema=tool.input_schema,
                    )
                    for tool in self.catalog.tools
                ]
            )
        ]

    def normalize_call(self, function_call: dict[str, Any] | types.FunctionCall) -> InternalToolCall:
        if isinstance(function_call, dict):
            name = function_call["name"]
            call_id = function_call.get("id")
            args = dict(function_call.get("args") or {})
        else:
            name = function_call.name or ""
            call_id = function_call.id
            args = dict(function_call.args or {})
        spec = self.catalog.resolve(name)
        return InternalToolCall(
            call_id=call_id or f"gemini-{name}",
            provider=self.provider,
            name=name,
            arguments=args,
            server_name=spec.server_name,
        )

    def result_to_provider_response(self, result: InternalToolResult, tool_name: str) -> types.Part:
        return types.Part.from_function_response(
            name=tool_name,
            response=result.payload(),
        )


def gemini_tool_spec(
    name: str,
    description: str,
    input_schema: dict[str, Any],
    server_name: str,
) -> InternalToolSpec:
    return InternalToolSpec(
        name=name,
        description=description,
        input_schema=input_schema,
        server_name=server_name,
    )
