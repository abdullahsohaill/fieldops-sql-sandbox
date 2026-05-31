from __future__ import annotations

import pytest

from fieldops.data.builder import build_database
from fieldops.metadata import (
    describe_table,
    get_database_summary,
    get_source_lineage,
    list_tables,
)


@pytest.mark.asyncio
async def test_list_tables_returns_fieldops_tables(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    tables = list_tables(db_path)

    assert "fields" in tables
    assert "missions" in tables
    assert "weed_detections" in tables
    assert all(not table.startswith("sqlite_") for table in tables)


@pytest.mark.asyncio
async def test_describe_table_returns_columns_foreign_keys_and_indexes(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    description = describe_table(db_path, "missions")

    assert description["table"] == "missions"
    assert {"name": "mission_id", "type": "TEXT", "nullable": True, "default": None, "primary_key": True} in description["columns"]
    assert any(fk["references_table"] == "fields" for fk in description["foreign_keys"])
    assert any(index["name"] == "idx_missions_field_date" for index in description["indexes"])


@pytest.mark.asyncio
async def test_describe_table_rejects_unknown_tables(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    with pytest.raises(ValueError, match="Unknown table"):
        describe_table(db_path, "not_a_table")


@pytest.mark.asyncio
async def test_database_summary_includes_row_counts(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    summary = get_database_summary(db_path)

    assert summary["table_count"] == 7
    assert summary["tables"]["fields"] == 4
    assert summary["tables"]["weather_daily"] == 12


@pytest.mark.asyncio
async def test_source_lineage_reports_seed_and_fixture_sources(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    lineage = get_source_lineage(db_path)

    assert lineage["fields"]["source"] == "deterministic local seed data"
    assert lineage["crop_stats"][0]["source_name"] == "USDA NASS QuickStats fixture"
    assert lineage["weather_daily"][0]["source_name"] == "NASA POWER Daily API fixture"

