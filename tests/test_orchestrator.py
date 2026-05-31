from __future__ import annotations

import os
import sys

import pytest

from fieldops.agents.orchestrator import FieldOpsOrchestrator
from fieldops.agents.provider import FakeProvider, ModelResponse
from fieldops.data.builder import build_database
from fieldops.mcp_client.config import McpServerConfig, McpServerRegistry
from fieldops.mcp_client.router import AsyncMcpRouter
from fieldops.tools.protocol import InternalToolCall


def _router(db_path: str) -> AsyncMcpRouter:
    env = {**os.environ, "FIELDOPS_DB_PATH": db_path}
    registry = McpServerRegistry(
        (
            McpServerConfig(
                name="metadata",
                command=sys.executable,
                args=("-m", "fieldops.mcp_servers.metadata_server"),
                env=env,
            ),
            McpServerConfig(
                name="sql_sandbox",
                command=sys.executable,
                args=("-m", "fieldops.mcp_servers.sql_sandbox_server"),
                env=env,
            ),
        )
    )
    return AsyncMcpRouter(registry)


@pytest.mark.asyncio
async def test_orchestrator_runs_full_fake_provider_flow(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")
    provider = FakeProvider(
        [
            ModelResponse(text="Find high weed fields and compare spray mission completion."),
            ModelResponse(
                tool_call=InternalToolCall(
                    call_id="sql-call",
                    provider="gemini",
                    name="execute_read_only_sql",
                    arguments={
                        "query": """
                        SELECT fields.name, MAX(weed_detections.severity_score) AS max_severity
                        FROM fields
                        JOIN weed_detections ON weed_detections.field_id = fields.field_id
                        GROUP BY fields.field_id
                        ORDER BY max_severity DESC
                        """,
                        "max_rows": 5,
                    },
                    server_name="sql_sandbox",
                )
            ),
            ModelResponse(text="North Ridge and Story West have the highest weed pressure."),
        ]
    )

    result = await FieldOpsOrchestrator(provider, _router(str(db_path))).answer(
        "Which fields had the highest weed pressure?"
    )

    assert result.plan == "Find high weed fields and compare spray mission completion."
    assert result.tool_result.ok is True
    assert result.tool_result.result is not None
    assert result.tool_result.result["result"]["row_count"] >= 2
    assert "North Ridge" in result.answer


@pytest.mark.asyncio
async def test_orchestrator_surfaces_sql_sandbox_rejections(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")
    provider = FakeProvider(
        [
            ModelResponse(text="Attempt unsafe operation."),
            ModelResponse(
                tool_call=InternalToolCall(
                    call_id="unsafe-call",
                    provider="gemini",
                    name="execute_read_only_sql",
                    arguments={"query": "DROP TABLE fields"},
                    server_name="sql_sandbox",
                )
            ),
            ModelResponse(text="The SQL sandbox rejected the request."),
        ]
    )

    result = await FieldOpsOrchestrator(provider, _router(str(db_path))).answer("Drop the fields table")

    assert result.tool_result.ok is False
    assert result.tool_result.error == {
        "code": "blocked_keyword",
        "message": "Blocked SQL keyword(s): drop.",
    }
    assert "rejected" in result.answer

