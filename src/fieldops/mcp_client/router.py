from __future__ import annotations

import json
import time
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any, AsyncIterator, Protocol

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult, TextContent

from fieldops.mcp_client.config import McpServerConfig, McpServerRegistry, default_mcp_registry
from fieldops.tools.protocol import InternalToolCall, InternalToolResult


class McpSession(Protocol):
    async def initialize(self) -> Any: ...

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        read_timeout_seconds: timedelta | None = None,
    ) -> CallToolResult: ...


class AsyncMcpRouter:
    def __init__(
        self,
        registry: McpServerRegistry | None = None,
    ) -> None:
        self.registry = registry or default_mcp_registry()

    async def dispatch(self, call: InternalToolCall, timeout_seconds: float = 8.0) -> InternalToolResult:
        started = time.perf_counter()
        try:
            server = self.registry.resolve(call.server_name)
            async with self._session(server) as session:
                await session.initialize()
                result = await session.call_tool(
                    call.name,
                    call.arguments,
                    read_timeout_seconds=timedelta(seconds=timeout_seconds),
                )
        except Exception as exc:
            return InternalToolResult.failure(
                call_id=call.call_id,
                code="mcp_dispatch_error",
                message=str(exc),
                duration_ms=_duration_ms(started),
            )

        return self._to_internal_result(call.call_id, result, started)

    @asynccontextmanager
    async def _session(self, server: McpServerConfig) -> AsyncIterator[McpSession]:
        params = StdioServerParameters(
            command=server.command,
            args=list(server.args),
            env=server.env,
            cwd=server.cwd,
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                yield session

    def _to_internal_result(
        self,
        call_id: str,
        result: CallToolResult,
        started: float,
    ) -> InternalToolResult:
        payload = _decode_tool_result(result)
        if result.isError:
            return InternalToolResult.failure(
                call_id=call_id,
                code="mcp_tool_error",
                message=json.dumps(payload),
                duration_ms=_duration_ms(started),
            )
        if isinstance(payload, dict) and payload.get("ok") is False:
            error = payload.get("error") or {}
            return InternalToolResult.failure(
                call_id=call_id,
                code=str(error.get("code", "tool_rejected")),
                message=str(error.get("message", "Tool returned ok=false.")),
                duration_ms=_duration_ms(started),
            )
        return InternalToolResult.success(
            call_id=call_id,
            result=payload if isinstance(payload, dict) else {"content": payload},
            duration_ms=_duration_ms(started),
        )


def _decode_tool_result(result: CallToolResult) -> Any:
    if not result.content:
        return {}
    if len(result.content) == 1 and isinstance(result.content[0], TextContent):
        text = result.content[0].text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}
    return {"content": [content.model_dump(mode="json") for content in result.content]}


def _duration_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)

