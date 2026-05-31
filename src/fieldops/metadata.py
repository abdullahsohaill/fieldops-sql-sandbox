from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


SYSTEM_TABLE_PREFIX = "sqlite_"


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(db_path: Path) -> list[str]:
    with connect_readonly(db_path) as conn:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE ?
            ORDER BY name
            """,
            (f"{SYSTEM_TABLE_PREFIX}%",),
        ).fetchall()
    return [row["name"] for row in rows]


def describe_table(db_path: Path, table_name: str) -> dict[str, Any]:
    tables = set(list_tables(db_path))
    if table_name not in tables:
        raise ValueError(f"Unknown table: {table_name}")

    with connect_readonly(db_path) as conn:
        columns = [
            {
                "name": row["name"],
                "type": row["type"],
                "nullable": not bool(row["notnull"]),
                "default": row["dflt_value"],
                "primary_key": bool(row["pk"]),
            }
            for row in conn.execute(f"PRAGMA table_info({quote_identifier(table_name)})")
        ]
        foreign_keys = [
            {
                "column": row["from"],
                "references_table": row["table"],
                "references_column": row["to"],
            }
            for row in conn.execute(f"PRAGMA foreign_key_list({quote_identifier(table_name)})")
        ]
        indexes = [
            {"name": row["name"], "unique": bool(row["unique"])}
            for row in conn.execute(f"PRAGMA index_list({quote_identifier(table_name)})")
        ]

    return {
        "table": table_name,
        "columns": columns,
        "foreign_keys": foreign_keys,
        "indexes": indexes,
    }


def get_database_summary(db_path: Path) -> dict[str, Any]:
    tables = list_tables(db_path)
    with connect_readonly(db_path) as conn:
        row_counts = {
            table: conn.execute(f"SELECT COUNT(*) AS count FROM {quote_identifier(table)}").fetchone()[
                "count"
            ]
            for table in tables
        }
    return {
        "database": str(db_path),
        "table_count": len(tables),
        "tables": row_counts,
    }


def get_source_lineage(db_path: Path) -> dict[str, Any]:
    tables = set(list_tables(db_path))
    lineage: dict[str, Any] = {
        "fields": {
            "source": "deterministic local seed data",
            "notes": "Represents synthetic field boundaries and operating context.",
        },
        "missions": {
            "source": "deterministic local seed data",
            "notes": "Represents scouting and spray mission records for the local demo.",
        },
        "weed_detections": {
            "source": "deterministic local seed data",
            "notes": "Represents model-produced weed detections linked to missions.",
        },
        "spray_events": {
            "source": "deterministic local seed data",
            "notes": "Represents spray applications linked to fields and missions.",
        },
        "equipment_alerts": {
            "source": "deterministic local seed data",
            "notes": "Represents operational alerts linked to missions.",
        },
    }

    with connect_readonly(db_path) as conn:
        if "crop_stats" in tables:
            rows = conn.execute(
                """
                SELECT source_name, source_url, COUNT(*) AS rows
                FROM crop_stats
                GROUP BY source_name, source_url
                ORDER BY source_name
                """
            ).fetchall()
            lineage["crop_stats"] = [dict(row) for row in rows]
        if "weather_daily" in tables:
            rows = conn.execute(
                """
                SELECT source_name, COUNT(*) AS rows
                FROM weather_daily
                GROUP BY source_name
                ORDER BY source_name
                """
            ).fetchall()
            lineage["weather_daily"] = [dict(row) for row in rows]

    return lineage


def quote_identifier(identifier: str) -> str:
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'

