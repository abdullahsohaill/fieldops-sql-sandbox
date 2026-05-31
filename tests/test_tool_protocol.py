from __future__ import annotations

import pytest

from fieldops.tools.protocol import InternalToolResult, InternalToolSpec, ToolCatalog


def test_tool_catalog_resolves_specs_by_name():
    spec = InternalToolSpec(
        name="execute_read_only_sql",
        description="Execute safe SQL",
        input_schema={"type": "object", "properties": {}},
        server_name="sql_sandbox",
    )
    catalog = ToolCatalog((spec,))

    assert catalog.resolve("execute_read_only_sql") == spec


def test_tool_catalog_rejects_unknown_tools():
    catalog = ToolCatalog(())

    with pytest.raises(KeyError, match="Unknown tool"):
        catalog.resolve("missing")


def test_tool_result_payload_is_provider_neutral():
    result = InternalToolResult.success(
        call_id="call-1",
        result={"rows": [{"field_id": "fld-001"}]},
        duration_ms=12.5,
    )

    assert result.payload() == {
        "ok": True,
        "result": {"rows": [{"field_id": "fld-001"}]},
        "error": None,
        "duration_ms": 12.5,
    }

