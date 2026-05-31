from __future__ import annotations

import pytest

from fieldops.security.sql_validator import SqlValidationError, validate_read_only_sql


ALLOWED_TABLES = {
    "fields",
    "crop_stats",
    "weather_daily",
    "missions",
    "weed_detections",
    "spray_events",
    "equipment_alerts",
}


def test_validator_accepts_simple_select_and_adds_limit():
    result = validate_read_only_sql(
        "SELECT field_id, crop FROM fields WHERE crop = 'CORN'",
        ALLOWED_TABLES,
    )

    assert result.referenced_tables == ("fields",)
    assert result.limit_added is True
    assert "LIMIT 100" in result.safe_query


def test_validator_accepts_read_only_cte_queries():
    result = validate_read_only_sql(
        """
        WITH high_weed AS (
          SELECT field_id
          FROM weed_detections
          WHERE severity_score >= 7.5
        )
        SELECT fields.name
        FROM fields
        JOIN high_weed ON high_weed.field_id = fields.field_id
        """,
        ALLOWED_TABLES,
    )

    assert result.referenced_tables == ("fields", "weed_detections")
    assert "LIMIT 100" in result.safe_query


def test_validator_preserves_existing_safe_limit():
    result = validate_read_only_sql("SELECT * FROM fields LIMIT 25", ALLOWED_TABLES)

    assert result.limit_added is False
    assert "LIMIT 25" in result.safe_query


def test_validator_clamps_existing_large_limit():
    result = validate_read_only_sql("SELECT * FROM fields LIMIT 500", ALLOWED_TABLES)

    assert result.limit_added is False
    assert "LIMIT 100" in result.safe_query


@pytest.mark.parametrize(
    ("query", "code"),
    [
        ("", "empty_query"),
        ("SELECT * FROM fields; SELECT * FROM missions", "multiple_statements"),
        ("UPDATE fields SET crop = 'CORN'", "blocked_keyword"),
        ("DELETE FROM missions", "blocked_keyword"),
        ("DROP TABLE fields", "blocked_keyword"),
        ("PRAGMA table_info(fields)", "blocked_keyword"),
        ("ATTACH DATABASE 'other.db' AS other", "blocked_keyword"),
        ("SELECT * FROM payroll", "unknown_table"),
        ("EXPLAIN SELECT * FROM fields", "not_select"),
    ],
)
def test_validator_rejects_unsafe_or_out_of_scope_sql(query, code):
    with pytest.raises(SqlValidationError) as exc_info:
        validate_read_only_sql(query, ALLOWED_TABLES)

    assert exc_info.value.code == code


def test_validator_does_not_block_keywords_inside_string_literals():
    result = validate_read_only_sql("SELECT 'drop' AS example FROM fields", ALLOWED_TABLES)

    assert result.referenced_tables == ("fields",)
