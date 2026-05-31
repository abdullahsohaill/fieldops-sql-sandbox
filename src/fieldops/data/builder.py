from __future__ import annotations

import json
import os
import sqlite3
from importlib.resources import files
from pathlib import Path
from typing import Any

import httpx

from fieldops.config import PROJECT_ROOT


FIELDS: list[dict[str, Any]] = [
    {
        "field_id": "fld-001",
        "name": "North Ridge",
        "state": "ILLINOIS",
        "county": "MCLEAN",
        "latitude": 40.5142,
        "longitude": -88.9906,
        "crop": "CORN",
        "area_acres": 142.5,
        "soil_type": "silty clay loam",
        "irrigation_type": "rainfed",
    },
    {
        "field_id": "fld-002",
        "name": "Prairie East",
        "state": "ILLINOIS",
        "county": "MCLEAN",
        "latitude": 40.4481,
        "longitude": -88.8419,
        "crop": "SOYBEANS",
        "area_acres": 96.0,
        "soil_type": "loam",
        "irrigation_type": "pivot",
    },
    {
        "field_id": "fld-003",
        "name": "Story West",
        "state": "IOWA",
        "county": "STORY",
        "latitude": 42.0347,
        "longitude": -93.6408,
        "crop": "CORN",
        "area_acres": 188.2,
        "soil_type": "clay loam",
        "irrigation_type": "rainfed",
    },
    {
        "field_id": "fld-004",
        "name": "Skunk River South",
        "state": "IOWA",
        "county": "STORY",
        "latitude": 41.9966,
        "longitude": -93.5021,
        "crop": "SOYBEANS",
        "area_acres": 121.7,
        "soil_type": "sandy loam",
        "irrigation_type": "pivot",
    },
]


MISSIONS: list[dict[str, Any]] = [
    {
        "mission_id": "msn-001",
        "field_id": "fld-001",
        "mission_date": "2026-05-02",
        "mission_type": "scouting",
        "status": "completed",
        "coverage_pct": 94.2,
        "operator_name": "Avery Singh",
        "equipment_id": "drone-alpha",
    },
    {
        "mission_id": "msn-002",
        "field_id": "fld-001",
        "mission_date": "2026-05-03",
        "mission_type": "spray",
        "status": "aborted",
        "coverage_pct": 41.5,
        "operator_name": "Avery Singh",
        "equipment_id": "sprayer-17",
    },
    {
        "mission_id": "msn-003",
        "field_id": "fld-002",
        "mission_date": "2026-05-02",
        "mission_type": "spray",
        "status": "completed",
        "coverage_pct": 91.8,
        "operator_name": "Maya Chen",
        "equipment_id": "sprayer-21",
    },
    {
        "mission_id": "msn-004",
        "field_id": "fld-003",
        "mission_date": "2026-05-02",
        "mission_type": "scouting",
        "status": "completed",
        "coverage_pct": 86.4,
        "operator_name": "Noah Patel",
        "equipment_id": "drone-beta",
    },
    {
        "mission_id": "msn-005",
        "field_id": "fld-004",
        "mission_date": "2026-05-02",
        "mission_type": "spray",
        "status": "completed",
        "coverage_pct": 88.7,
        "operator_name": "Maya Chen",
        "equipment_id": "sprayer-17",
    },
]


WEED_DETECTIONS: list[dict[str, Any]] = [
    {
        "detection_id": "det-001",
        "mission_id": "msn-001",
        "field_id": "fld-001",
        "detected_at": "2026-05-02T10:21:00",
        "weed_species": "waterhemp",
        "severity_score": 8.6,
        "density_per_m2": 14.2,
        "confidence": 0.91,
    },
    {
        "detection_id": "det-002",
        "mission_id": "msn-001",
        "field_id": "fld-001",
        "detected_at": "2026-05-02T10:36:00",
        "weed_species": "giant ragweed",
        "severity_score": 6.1,
        "density_per_m2": 6.4,
        "confidence": 0.86,
    },
    {
        "detection_id": "det-003",
        "mission_id": "msn-004",
        "field_id": "fld-003",
        "detected_at": "2026-05-02T13:12:00",
        "weed_species": "foxtail",
        "severity_score": 7.8,
        "density_per_m2": 11.8,
        "confidence": 0.89,
    },
    {
        "detection_id": "det-004",
        "mission_id": "msn-005",
        "field_id": "fld-004",
        "detected_at": "2026-05-02T15:17:00",
        "weed_species": "velvetleaf",
        "severity_score": 4.2,
        "density_per_m2": 3.1,
        "confidence": 0.82,
    },
]


SPRAY_EVENTS: list[dict[str, Any]] = [
    {
        "spray_id": "spr-001",
        "field_id": "fld-001",
        "mission_id": "msn-002",
        "spray_date": "2026-05-03",
        "chemical_name": "glyphosate",
        "application_rate_l_per_acre": 0.72,
        "total_liters": 43.0,
        "wind_speed_m_s": 6.8,
        "status": "aborted",
    },
    {
        "spray_id": "spr-002",
        "field_id": "fld-002",
        "mission_id": "msn-003",
        "spray_date": "2026-05-02",
        "chemical_name": "clethodim",
        "application_rate_l_per_acre": 0.33,
        "total_liters": 31.7,
        "wind_speed_m_s": 6.9,
        "status": "completed",
    },
    {
        "spray_id": "spr-003",
        "field_id": "fld-004",
        "mission_id": "msn-005",
        "spray_date": "2026-05-02",
        "chemical_name": "dicamba",
        "application_rate_l_per_acre": 0.45,
        "total_liters": 54.8,
        "wind_speed_m_s": 7.6,
        "status": "completed",
    },
]


EQUIPMENT_ALERTS: list[dict[str, Any]] = [
    {
        "alert_id": "alt-001",
        "mission_id": "msn-002",
        "equipment_id": "sprayer-17",
        "alert_type": "nozzle_pressure",
        "severity": "high",
        "message": "Nozzle pressure dropped below calibrated threshold.",
        "created_at": "2026-05-03T09:44:00",
        "resolved_at": None,
    },
    {
        "alert_id": "alt-002",
        "mission_id": "msn-005",
        "equipment_id": "sprayer-17",
        "alert_type": "nozzle_pressure",
        "severity": "medium",
        "message": "Nozzle pressure fluctuation detected during west pass.",
        "created_at": "2026-05-02T15:39:00",
        "resolved_at": "2026-05-02T16:05:00",
    },
    {
        "alert_id": "alt-003",
        "mission_id": "msn-004",
        "equipment_id": "drone-beta",
        "alert_type": "coverage_gap",
        "severity": "medium",
        "message": "Coverage below target due to battery swap delay.",
        "created_at": "2026-05-02T13:52:00",
        "resolved_at": "2026-05-02T14:18:00",
    },
]


def load_fixture(name: str) -> list[dict[str, Any]]:
    path = PROJECT_ROOT / "data" / "fixtures" / name
    return json.loads(path.read_text())


def create_schema(conn: sqlite3.Connection) -> None:
    schema = files("fieldops.data").joinpath("schema.sql").read_text()
    conn.executescript(schema)


async def fetch_usda_crop_stats(api_key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    queries = [
        {"state_alpha": "IL", "county_name": "MCLEAN", "commodity_desc": "CORN"},
        {"state_alpha": "IL", "county_name": "MCLEAN", "commodity_desc": "SOYBEANS"},
        {"state_alpha": "IA", "county_name": "STORY", "commodity_desc": "CORN"},
        {"state_alpha": "IA", "county_name": "STORY", "commodity_desc": "SOYBEANS"},
    ]
    async with httpx.AsyncClient(timeout=20) as client:
        for query in queries:
            params = {
                "key": api_key,
                "format": "JSON",
                "year__GE": "2023",
                "statisticcat_desc": "AREA PLANTED",
                "agg_level_desc": "COUNTY",
                **query,
            }
            response = await client.get("https://quickstats.nass.usda.gov/api/api_GET/", params=params)
            response.raise_for_status()
            for item in response.json().get("data", [])[:3]:
                value = str(item.get("Value", "0")).replace(",", "")
                if not value.isnumeric():
                    continue
                rows.append(
                    {
                        "stat_id": (
                            f"cs-{item['state_alpha'].lower()}-"
                            f"{item['county_name'].lower()}-"
                            f"{item['commodity_desc'].lower()}-{item['year']}"
                        ),
                        "state": item["state_name"],
                        "county": item["county_name"],
                        "commodity": item["commodity_desc"],
                        "year": int(item["year"]),
                        "statistic": item["statisticcat_desc"],
                        "unit": item["unit_desc"],
                        "value": float(value),
                        "source_name": "USDA NASS QuickStats",
                        "source_url": "https://quickstats.nass.usda.gov/api",
                    }
                )
    return rows or load_fixture("crop_stats.json")


async def fetch_nasa_weather() -> list[dict[str, Any]]:
    # NASA POWER is intentionally optional for this MVP; fixtures keep local builds reliable.
    return load_fixture("weather_daily.json")


def insert_rows(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    columns = list(rows[0])
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)
    conn.executemany(
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
        [[row[column] for column in columns] for row in rows],
    )


async def build_database(db_path: Path, mode: str = "offline") -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        crop_stats = load_fixture("crop_stats.json")
        weather = load_fixture("weather_daily.json")
        if mode == "refresh":
            api_key = os.getenv("NASS_API_KEY")
            if api_key:
                crop_stats = await fetch_usda_crop_stats(api_key)
            weather = await fetch_nasa_weather()

        weather_rows = [
            {
                "weather_id": f"wx-{row['field_id']}-{row['date']}",
                **row,
                "source_name": "NASA POWER Daily API fixture",
            }
            for row in weather
        ]

        insert_rows(conn, "fields", FIELDS)
        insert_rows(conn, "crop_stats", crop_stats)
        insert_rows(conn, "weather_daily", weather_rows)
        insert_rows(conn, "missions", MISSIONS)
        insert_rows(conn, "weed_detections", WEED_DETECTIONS)
        insert_rows(conn, "spray_events", SPRAY_EVENTS)
        insert_rows(conn, "equipment_alerts", EQUIPMENT_ALERTS)
        conn.commit()
    finally:
        conn.close()

    return db_path
