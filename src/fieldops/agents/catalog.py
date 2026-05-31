from __future__ import annotations

from fieldops.tools.protocol import InternalToolSpec, ToolCatalog


def orchestration_tool_catalog() -> ToolCatalog:
    return ToolCatalog(
        (
            InternalToolSpec(
                name="list_tables",
                description="List tables in the FieldOps analytics database.",
                input_schema={"type": "object", "properties": {}, "additionalProperties": False},
                server_name="metadata",
            ),
            InternalToolSpec(
                name="get_database_summary",
                description="Return row counts for FieldOps database tables.",
                input_schema={"type": "object", "properties": {}, "additionalProperties": False},
                server_name="metadata",
            ),
            InternalToolSpec(
                name="execute_read_only_sql",
                description="Validate and execute read-only SQL against the FieldOps database.",
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

