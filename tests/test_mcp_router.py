from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any, AsyncIterator

import pytest
from mcp.types import CallToolResult, TextContent

from fieldops.mcp_client.config import McpServerConfig, McpServerRegistry
from fieldops.mcp_client.router import AsyncMcpRouter
from fieldops.tools.protocol import InternalToolCall


class FakeSession:
    def __init__(self, result: CallToolResult) -> None:
        self.result = result
        self.initialized = False
        self.calls: list[tuple[str, dict[str, Any] | None, timedelta | None]] = []

    async def initialize(self) -> None:
        self.initialized = True

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        read_timeout_seconds: timedelta | None = None,
    ) -> CallToolResult:
        self.calls.append((name, arguments, read_timeout_seconds))
        return self.result


class FakeRouter(AsyncMcpRouter):
    def __init__(self, session: FakeSession) -> None:
        super().__init__(
            McpServerRegistry(
                (
                    McpServerConfig(
                        name="sql_sandbox",
                        command="fake-sql-mcp",
                    ),
                )
            )
        )
        self.session = session

    @asynccontextmanager
    async def _session(self, server: McpServerConfig) -> AsyncIterator[FakeSession]:
        yield self.session


def _text_result(payload: dict[str, Any], is_error: bool = False) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload))],
        isError=is_error,
    )


@pytest.mark.asyncio
async def test_router_dispatches_internal_calls_to_mcp_sessions():
    session = FakeSession(_text_result({"ok": True, "result": {"row_count": 2}}))
    router = FakeRouter(session)

    result = await router.dispatch(
        InternalToolCall(
            call_id="call-1",
            provider="gemini",
            name="execute_read_only_sql",
            arguments={"query": "SELECT * FROM fields"},
            server_name="sql_sandbox",
        )
    )

    assert session.initialized is True
    assert session.calls[0][0] == "execute_read_only_sql"
    assert session.calls[0][1] == {"query": "SELECT * FROM fields"}
    assert result.ok is True
    assert result.result == {"ok": True, "result": {"row_count": 2}}


@pytest.mark.asyncio
async def test_router_maps_tool_rejections_to_internal_failures():
    session = FakeSession(
        _text_result(
            {
                "ok": False,
                "error": {"code": "blocked_keyword", "message": "Blocked SQL keyword."},
            }
        )
    )
    router = FakeRouter(session)

    result = await router.dispatch(
        InternalToolCall(
            call_id="call-2",
            provider="gemini",
            name="execute_read_only_sql",
            arguments={"query": "DROP TABLE fields"},
            server_name="sql_sandbox",
        )
    )

    assert result.ok is False
    assert result.error == {"code": "blocked_keyword", "message": "Blocked SQL keyword."}


@pytest.mark.asyncio
async def test_router_handles_unknown_servers():
    session = FakeSession(_text_result({"ok": True}))
    router = FakeRouter(session)

    result = await router.dispatch(
        InternalToolCall(
            call_id="call-3",
            provider="gemini",
            name="list_tables",
            arguments={},
            server_name="missing",
        )
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error["code"] == "mcp_dispatch_error"

