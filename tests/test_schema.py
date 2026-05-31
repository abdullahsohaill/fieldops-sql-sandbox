from __future__ import annotations

import sqlite3
from importlib.resources import files


EXPECTED_TABLES = {
    "fields",
    "crop_stats",
    "weather_daily",
    "missions",
    "weed_detections",
    "spray_events",
    "equipment_alerts",
}

EXPECTED_INDEXES = {
    "idx_weather_field_date",
    "idx_missions_field_date",
    "idx_weed_field_severity",
    "idx_spray_field_date",
    "idx_alerts_equipment",
}


def test_schema_creates_expected_tables_and_indexes():
    schema = files("fieldops.data").joinpath("schema.sql").read_text()

    with sqlite3.connect(":memory:") as conn:
        conn.executescript(schema)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
            )
        }

    assert tables == EXPECTED_TABLES
    assert EXPECTED_INDEXES.issubset(indexes)


def test_schema_enforces_representative_check_constraints():
    schema = files("fieldops.data").joinpath("schema.sql").read_text()

    with sqlite3.connect(":memory:") as conn:
        conn.executescript(schema)
        try:
            conn.execute(
                """
                INSERT INTO fields (
                  field_id, name, state, county, latitude, longitude, crop,
                  area_acres, soil_type, irrigation_type
                )
                VALUES (
                  'fld-bad', 'Bad Field', 'ILLINOIS', 'MCLEAN', 40.0, -88.0,
                  'CORN', -1, 'loam', 'rainfed'
                )
                """
            )
        except sqlite3.IntegrityError as exc:
            assert "CHECK constraint failed" in str(exc)
        else:
            raise AssertionError("negative acreage should violate schema constraints")

