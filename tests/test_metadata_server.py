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
async def test_metadata_server_tools_return_structured_metadata(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    tables = await list_tables(str(db_path))
    missions = await describe_table("missions", str(db_path))
    summary = await get_database_summary(str(db_path))
    lineage = await get_source_lineage(str(db_path))

    assert tables["database"] == str(db_path)
    assert "missions" in tables["tables"]
    assert missions["table"] == "missions"
    assert summary["tables"]["fields"] == 4
    assert lineage["crop_stats"][0]["source_name"] == "USDA NASS QuickStats fixture"

