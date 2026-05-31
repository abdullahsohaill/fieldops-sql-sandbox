from __future__ import annotations

import json
from typing import Any

from fieldops.tools.protocol import (
    InternalToolCall,
    InternalToolResult,
    ToolCatalog,
)


class OpenAIToolAdapter:
    provider = "openai"

    def __init__(self, catalog: ToolCatalog) -> None:
        self.catalog = catalog

    def to_provider_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in self.catalog.tools
        ]

    def normalize_call(self, tool_call: dict[str, Any]) -> InternalToolCall:
        function = tool_call["function"]
        name = function["name"]
        spec = self.catalog.resolve(name)
        arguments = function.get("arguments") or "{}"
        return InternalToolCall(
            call_id=tool_call["id"],
            provider=self.provider,
            name=name,
            arguments=json.loads(arguments) if isinstance(arguments, str) else dict(arguments),
            server_name=spec.server_name,
        )

    def result_to_provider_response(self, result: InternalToolResult) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": result.call_id,
            "content": json.dumps(result.payload()),
        }

