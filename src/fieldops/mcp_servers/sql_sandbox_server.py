from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from fieldops.config import get_settings
from fieldops.metadata import list_tables
from fieldops.security.sql_executor import execute_read_only_query
from fieldops.security.sql_validator import (
    DEFAULT_MAX_ROWS,
    SqlValidationError,
    validate_read_only_sql as validate_sql,
)


mcp = FastMCP("fieldops-sql-sandbox")


def resolve_db_path(db_path: str | None = None) -> Path:
    return Path(db_path) if db_path else get_settings().db_path


@mcp.tool()
async def validate_read_only_sql(
    query: str,
    max_rows: int = DEFAULT_MAX_ROWS,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Validate generated SQL without executing it."""
    path = resolve_db_path(db_path)
    try:
        validation = validate_sql(query, allowed_tables=list_tables(path), max_rows=max_rows)
    except SqlValidationError as exc:
        return _error_response(exc.code, exc.message)
    except Exception as exc:  # pragma: no cover - defensive boundary for MCP clients
        return _error_response("validation_error", str(exc))

    return {
        "ok": True,
        "validation": {
            "original_query": validation.original_query,
            "safe_query": validation.safe_query,
            "referenced_tables": list(validation.referenced_tables),
            "max_rows": validation.max_rows,
            "limit_added": validation.limit_added,
        },
    }


@mcp.tool()
async def execute_read_only_sql(
    query: str,
    max_rows: int = DEFAULT_MAX_ROWS,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Validate and execute read-only SQL against the FieldOps database."""
    path = resolve_db_path(db_path)
    try:
        result = execute_read_only_query(path, query, max_rows=max_rows)
    except SqlValidationError as exc:
        return _error_response(exc.code, exc.message)
    except TimeoutError as exc:
        return _error_response("query_timeout", str(exc))
    except Exception as exc:  # pragma: no cover - defensive boundary for MCP clients
        return _error_response("execution_error", str(exc))

    return {"ok": True, "result": result.to_dict()}


def _error_response(code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

