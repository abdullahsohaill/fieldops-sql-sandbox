from __future__ import annotations

import json

from fieldops.tools.openai_adapter import OpenAIToolAdapter
from fieldops.tools.protocol import InternalToolResult, InternalToolSpec, ToolCatalog


def _catalog() -> ToolCatalog:
    return ToolCatalog(
        (
            InternalToolSpec(
                name="validate_read_only_sql",
                description="Validate generated SQL",
                input_schema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                    "additionalProperties": False,
                },
                server_name="sql_sandbox",
            ),
        )
    )


def test_openai_adapter_converts_internal_specs_to_tool_schema():
    adapter = OpenAIToolAdapter(_catalog())

    tools = adapter.to_provider_tools()

    assert tools == [
        {
            "type": "function",
            "function": {
                "name": "validate_read_only_sql",
                "description": "Validate generated SQL",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        }
    ]


def test_openai_adapter_normalizes_tool_calls():
    adapter = OpenAIToolAdapter(_catalog())

    call = adapter.normalize_call(
        {
            "id": "call-openai-1",
            "type": "function",
            "function": {
                "name": "validate_read_only_sql",
                "arguments": json.dumps({"query": "SELECT * FROM fields"}),
            },
        }
    )

    assert call.call_id == "call-openai-1"
    assert call.provider == "openai"
    assert call.server_name == "sql_sandbox"
    assert call.arguments == {"query": "SELECT * FROM fields"}


def test_openai_adapter_maps_results_to_tool_message():
    adapter = OpenAIToolAdapter(_catalog())
    result = InternalToolResult.failure("call-openai-1", "blocked_keyword", "Blocked keyword")

    response = adapter.result_to_provider_response(result)

    assert response["role"] == "tool"
    assert response["tool_call_id"] == "call-openai-1"
    assert json.loads(response["content"])["error"]["code"] == "blocked_keyword"

