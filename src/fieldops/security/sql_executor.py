from __future__ import annotations

import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fieldops.metadata import connect_readonly, list_tables
from fieldops.security.sql_validator import DEFAULT_MAX_ROWS, validate_read_only_sql


DEFAULT_QUERY_TIMEOUT_SECONDS = 5.0
SQLITE_PROGRESS_CHECK_OPS = 1_000


@dataclass(frozen=True)
class SqlExecutionResult:
    original_query: str
    safe_query: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    row_count: int
    referenced_tables: tuple[str, ...]
    max_rows: int
    limit_added: bool
    duration_ms: float

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["columns"] = list(self.columns)
        data["rows"] = list(self.rows)
        data["referenced_tables"] = list(self.referenced_tables)
        return data


def execute_read_only_query(
    db_path: Path,
    query: str,
    max_rows: int = DEFAULT_MAX_ROWS,
    timeout_seconds: float = DEFAULT_QUERY_TIMEOUT_SECONDS,
) -> SqlExecutionResult:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0.")

    allowed_tables = list_tables(db_path)
    validation = validate_read_only_sql(query, allowed_tables=allowed_tables, max_rows=max_rows)

    started = time.perf_counter()
    with connect_readonly(db_path) as conn:
        conn.execute("PRAGMA query_only = ON")
        _install_timeout(conn, started=started, timeout_seconds=timeout_seconds)
        try:
            cursor = conn.execute(validation.safe_query)
            rows = tuple(dict(row) for row in cursor.fetchall())
        except sqlite3.OperationalError as exc:
            if "interrupted" in str(exc).lower():
                raise TimeoutError(f"SQL query exceeded {timeout_seconds:.2f}s timeout.") from exc
            raise
        finally:
            conn.set_progress_handler(None, 0)

    duration_ms = (time.perf_counter() - started) * 1000
    columns = tuple(rows[0].keys()) if rows else _columns_for_empty_result(db_path, validation.safe_query)
    return SqlExecutionResult(
        original_query=validation.original_query,
        safe_query=validation.safe_query,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        referenced_tables=validation.referenced_tables,
        max_rows=validation.max_rows,
        limit_added=validation.limit_added,
        duration_ms=round(duration_ms, 3),
    )


def _install_timeout(
    conn: sqlite3.Connection,
    started: float,
    timeout_seconds: float,
) -> None:
    def check_timeout() -> int:
        return int((time.perf_counter() - started) > timeout_seconds)

    conn.set_progress_handler(check_timeout, SQLITE_PROGRESS_CHECK_OPS)


def _columns_for_empty_result(db_path: Path, query: str) -> tuple[str, ...]:
    with connect_readonly(db_path) as conn:
        conn.execute("PRAGMA query_only = ON")
        cursor = conn.execute(query)
        return tuple(description[0] for description in cursor.description or ())

