from __future__ import annotations

import sqlite3

import pytest

from fieldops.data.builder import build_database


EXPECTED_TABLES = {
    "fields",
    "crop_stats",
    "weather_daily",
    "missions",
    "weed_detections",
    "spray_events",
    "equipment_alerts",
}


@pytest.mark.asyncio
async def test_build_database_creates_expected_tables(tmp_path):
    db_path = tmp_path / "fieldops.db"

    await build_database(db_path, mode="offline")

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }

    assert tables == EXPECTED_TABLES


@pytest.mark.asyncio
async def test_build_database_seeds_representative_fieldops_records(tmp_path):
    db_path = tmp_path / "fieldops.db"

    await build_database(db_path, mode="offline")

    with sqlite3.connect(db_path) as conn:
        field_count = conn.execute("SELECT COUNT(*) FROM fields").fetchone()[0]
        high_weed_fields = conn.execute(
            """
            SELECT COUNT(DISTINCT field_id)
            FROM weed_detections
            WHERE severity_score >= 7.5
            """
        ).fetchone()[0]
        windy_spray_events = conn.execute(
            """
            SELECT COUNT(*)
            FROM spray_events
            WHERE wind_speed_m_s > 6.0
            """
        ).fetchone()[0]

    assert field_count == 4
    assert high_weed_fields >= 2
    assert windy_spray_events >= 2

