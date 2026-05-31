from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class McpServerConfig:
    name: str
    command: str
    args: tuple[str, ...] = field(default_factory=tuple)
    cwd: Path | None = None
    env: dict[str, str] | None = None


@dataclass(frozen=True)
class McpServerRegistry:
    servers: tuple[McpServerConfig, ...]

    def by_name(self) -> dict[str, McpServerConfig]:
        return {server.name: server for server in self.servers}

    def resolve(self, name: str) -> McpServerConfig:
        try:
            return self.by_name()[name]
        except KeyError as exc:
            raise KeyError(f"Unknown MCP server: {name}") from exc


def default_mcp_registry() -> McpServerRegistry:
    return McpServerRegistry(
        servers=(
            McpServerConfig(
                name="metadata",
                command="fieldops-metadata-mcp",
            ),
            McpServerConfig(
                name="sql_sandbox",
                command="fieldops-sql-mcp",
            ),
        )
    )

