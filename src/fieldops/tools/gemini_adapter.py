from __future__ import annotations

from typing import Any

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

    def to_provider_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "function_declarations": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": _gemini_schema(tool.input_schema),
                    }
                    for tool in self.catalog.tools
                ]
            }
        ]

    def normalize_call(self, function_call: dict[str, Any]) -> InternalToolCall:
        name = function_call["name"]
        spec = self.catalog.resolve(name)
        return InternalToolCall(
            call_id=function_call.get("id") or f"gemini-{name}",
            provider=self.provider,
            name=name,
            arguments=dict(function_call.get("args") or {}),
            server_name=spec.server_name,
        )

    def result_to_provider_response(self, result: InternalToolResult) -> dict[str, Any]:
        return {
            "function_response": {
                "name": result.call_id,
                "response": result.payload(),
            }
        }


def _gemini_schema(schema: dict[str, Any]) -> dict[str, Any]:
    converted = dict(schema)
    if "additionalProperties" in converted:
        converted.pop("additionalProperties")
    if converted.get("type") == "object":
        converted["type"] = "OBJECT"
    for property_schema in converted.get("properties", {}).values():
        if isinstance(property_schema, dict) and "type" in property_schema:
            property_schema["type"] = str(property_schema["type"]).upper()
    return converted


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

