from __future__ import annotations

import pytest

from fieldops.data.builder import build_database
from fieldops.mcp_servers.metadata_server import (
    describe_table,
    get_database_summary,
    get_source_lineage,
    list_tables,
)


@pytest.mark.asyncio
async def test_metadata_server_tools_return_structured_metadata(tmp_path, monkeypatch):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")
    monkeypatch.setenv("FIELDOPS_DB_PATH", str(db_path))

    tables = await list_tables()
    missions = await describe_table("missions")
    summary = await get_database_summary()
    lineage = await get_source_lineage()

    assert tables["database"] == str(db_path)
    assert "missions" in tables["tables"]
    assert missions["table"] == "missions"
    assert summary["tables"]["fields"] == 4
    assert lineage["crop_stats"][0]["source_name"] == "USDA NASS QuickStats fixture"
