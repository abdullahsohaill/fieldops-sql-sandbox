from __future__ import annotations

import pytest

from fieldops.mcp_client.config import default_mcp_registry


def test_default_mcp_registry_resolves_known_servers():
    registry = default_mcp_registry()

    assert registry.resolve("metadata").command == "fieldops-metadata-mcp"
    assert registry.resolve("sql_sandbox").command == "fieldops-sql-mcp"


def test_mcp_registry_rejects_unknown_servers():
    registry = default_mcp_registry()

    with pytest.raises(KeyError, match="Unknown MCP server"):
        registry.resolve("missing")

