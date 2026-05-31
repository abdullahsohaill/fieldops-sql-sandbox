from __future__ import annotations

import pytest

from fieldops.data.builder import build_database
from fieldops.mcp_servers.sql_sandbox_server import (
    execute_read_only_sql,
    validate_read_only_sql,
)


@pytest.mark.asyncio
async def test_validate_read_only_sql_tool_returns_safe_query(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    response = await validate_read_only_sql("SELECT name FROM fields", db_path=str(db_path))

    assert response["ok"] is True
    assert response["validation"]["referenced_tables"] == ["fields"]
    assert "LIMIT 100" in response["validation"]["safe_query"]


@pytest.mark.asyncio
async def test_validate_read_only_sql_tool_returns_structured_rejection(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    response = await validate_read_only_sql("DROP TABLE fields", db_path=str(db_path))

    assert response["ok"] is False
    assert response["error"]["code"] == "blocked_keyword"


@pytest.mark.asyncio
async def test_execute_read_only_sql_tool_returns_rows(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    response = await execute_read_only_sql(
        "SELECT field_id, name FROM fields ORDER BY field_id",
        max_rows=2,
        db_path=str(db_path),
    )

    assert response["ok"] is True
    assert response["result"]["row_count"] == 2
    assert response["result"]["rows"][0]["field_id"] == "fld-001"
    assert response["result"]["referenced_tables"] == ["fields"]


@pytest.mark.asyncio
async def test_execute_read_only_sql_tool_blocks_writes_before_execution(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    response = await execute_read_only_sql(
        "UPDATE fields SET crop = 'CORN'",
        db_path=str(db_path),
    )

    assert response["ok"] is False
    assert response["error"]["code"] == "blocked_keyword"

