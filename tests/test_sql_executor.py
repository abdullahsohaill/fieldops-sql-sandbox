from __future__ import annotations

import pytest

from fieldops.data.builder import build_database
from fieldops.security.sql_executor import execute_read_only_query
from fieldops.security.sql_validator import SqlValidationError


@pytest.mark.asyncio
async def test_execute_read_only_query_returns_structured_rows(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    result = execute_read_only_query(
        db_path,
        "SELECT field_id, name, crop FROM fields WHERE crop = 'CORN' ORDER BY field_id",
    )

    assert result.columns == ("field_id", "name", "crop")
    assert result.row_count == 2
    assert result.rows[0]["field_id"] == "fld-001"
    assert result.referenced_tables == ("fields",)
    assert "LIMIT 100" in result.safe_query


@pytest.mark.asyncio
async def test_execute_read_only_query_enforces_max_rows(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    result = execute_read_only_query(
        db_path,
        "SELECT field_id FROM fields ORDER BY field_id",
        max_rows=2,
    )

    assert result.row_count == 2
    assert "LIMIT 2" in result.safe_query


@pytest.mark.asyncio
async def test_execute_read_only_query_rejects_unsafe_sql(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    with pytest.raises(SqlValidationError, match="Blocked SQL keyword"):
        execute_read_only_query(db_path, "DROP TABLE fields")


@pytest.mark.asyncio
async def test_execute_read_only_query_reports_empty_result_columns(tmp_path):
    db_path = await build_database(tmp_path / "fieldops.db", mode="offline")

    result = execute_read_only_query(
        db_path,
        "SELECT field_id, name FROM fields WHERE crop = 'COTTON'",
    )

    assert result.columns == ("field_id", "name")
    assert result.row_count == 0
    assert result.rows == ()

