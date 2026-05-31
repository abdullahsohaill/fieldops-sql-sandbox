from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from fieldops.config import get_settings
from fieldops import metadata


mcp = FastMCP("fieldops-metadata")


def resolve_db_path(db_path: str | None = None) -> Path:
    return Path(db_path) if db_path else get_settings().db_path


@mcp.tool()
async def list_tables(db_path: str | None = None) -> dict[str, Any]:
    """List user-defined tables in the FieldOps analytics database."""
    path = resolve_db_path(db_path)
    return {"database": str(path), "tables": metadata.list_tables(path)}


@mcp.tool()
async def describe_table(table_name: str, db_path: str | None = None) -> dict[str, Any]:
    """Describe a table's columns, indexes, and foreign keys."""
    return metadata.describe_table(resolve_db_path(db_path), table_name)


@mcp.tool()
async def get_database_summary(db_path: str | None = None) -> dict[str, Any]:
    """Return row counts for the local FieldOps analytics database."""
    return metadata.get_database_summary(resolve_db_path(db_path))


@mcp.tool()
async def get_source_lineage(db_path: str | None = None) -> dict[str, Any]:
    """Return source notes for each table in the FieldOps analytics database."""
    return metadata.get_source_lineage(resolve_db_path(db_path))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

