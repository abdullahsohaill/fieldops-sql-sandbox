from __future__ import annotations

from fieldops.security.sql_validator import validate_read_only_sql


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
