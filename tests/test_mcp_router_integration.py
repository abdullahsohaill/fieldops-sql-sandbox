from __future__ import annotations

import os
import sys

import pytest

from fieldops.data.builder import build_database
from fieldops.mcp_client.config import McpServerConfig, McpServerRegistry
from fieldops.mcp_client.router import AsyncMcpRouter
from fieldops.tools.protocol import InternalToolCall


def _registry_with_db(db_path: str) -> McpServerRegistry:
    env = {**os.environ, "FIELDOPS_DB_PATH": db_path}
    return McpServerRegistry(
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


@pytest.mark.asyncio
async def test_router_dispatches_to_real_metadata_mcp_server(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")
    router = AsyncMcpRouter(_registry_with_db(str(db_path)))

    result = await router.dispatch(
        InternalToolCall(
            call_id="metadata-call",
            provider="gemini",
            name="list_tables",
            arguments={},
            server_name="metadata",
        )
    )

    assert result.ok is True
    assert result.result is not None
    assert "fields" in result.result["tables"]


@pytest.mark.asyncio
async def test_router_dispatches_to_real_sql_sandbox_mcp_server(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")
    router = AsyncMcpRouter(_registry_with_db(str(db_path)))

    result = await router.dispatch(
        InternalToolCall(
            call_id="sql-call",
            provider="gemini",
            name="execute_read_only_sql",
            arguments={"query": "SELECT field_id FROM fields ORDER BY field_id", "max_rows": 2},
            server_name="sql_sandbox",
        )
    )

    assert result.ok is True
    assert result.result is not None
    assert result.result["result"]["row_count"] == 2


@pytest.mark.asyncio
async def test_router_returns_failure_from_real_sql_sandbox_mcp_server(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")
    router = AsyncMcpRouter(_registry_with_db(str(db_path)))

    result = await router.dispatch(
        InternalToolCall(
            call_id="unsafe-sql-call",
            provider="gemini",
            name="execute_read_only_sql",
            arguments={"query": "DROP TABLE fields"},
            server_name="sql_sandbox",
        )
    )

    assert result.ok is False
    assert result.error == {
        "code": "blocked_keyword",
        "message": "Blocked SQL keyword(s): drop.",
    }

