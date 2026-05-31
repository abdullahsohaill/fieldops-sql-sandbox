from __future__ import annotations

from fieldops.tools.gemini_adapter import GeminiToolAdapter
from fieldops.tools.protocol import InternalToolResult, InternalToolSpec, ToolCatalog


def _catalog() -> ToolCatalog:
    return ToolCatalog(
        (
            InternalToolSpec(
                name="execute_read_only_sql",
                description="Execute validated SQL",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_rows": {"type": "integer"},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                server_name="sql_sandbox",
            ),
        )
    )


def test_gemini_adapter_converts_internal_specs_to_function_declarations():
    adapter = GeminiToolAdapter(_catalog())

    tools = adapter.to_provider_tools()

    declaration = tools[0]["function_declarations"][0]
    assert declaration["name"] == "execute_read_only_sql"
    assert declaration["parameters"]["type"] == "OBJECT"
    assert declaration["parameters"]["properties"]["query"]["type"] == "STRING"
    assert "additionalProperties" not in declaration["parameters"]


def test_gemini_adapter_normalizes_function_calls():
    adapter = GeminiToolAdapter(_catalog())

    call = adapter.normalize_call(
        {
            "id": "call-123",
            "name": "execute_read_only_sql",
            "args": {"query": "SELECT * FROM fields"},
        }
    )

    assert call.call_id == "call-123"
    assert call.provider == "gemini"
    assert call.server_name == "sql_sandbox"
    assert call.arguments == {"query": "SELECT * FROM fields"}


def test_gemini_adapter_maps_internal_results_to_function_response():
    adapter = GeminiToolAdapter(_catalog())
    result = InternalToolResult.success("call-123", {"row_count": 2})

    response = adapter.result_to_provider_response(result)

    assert response["function_response"]["name"] == "call-123"
    assert response["function_response"]["response"]["result"] == {"row_count": 2}

