from __future__ import annotations

import asyncio
import os
import sqlite3
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from fieldops.agents.orchestrator import FieldOpsOrchestrator
from fieldops.agents.provider import FakeProvider, GeminiProvider, ModelResponse
from fieldops.config import get_settings
from fieldops.data.builder import build_database
from fieldops.mcp_client.config import McpServerConfig, McpServerRegistry
from fieldops.mcp_client.router import AsyncMcpRouter
from fieldops.tools.protocol import InternalToolCall


app = typer.Typer(help="FieldOps SQL Sandbox command line interface.")
console = Console()


@app.command("build-db")
def build_db(
    mode: str = typer.Option("offline", help="Use 'offline' fixtures or 'refresh' public data."),
    db_path: Path | None = typer.Option(None, help="SQLite database path."),
) -> None:
    """Build the reproducible local FieldOps SQLite database."""
    settings = get_settings()
    path = db_path or settings.db_path
    built_path = asyncio.run(build_database(path, mode=mode))
    console.print(f"Built FieldOps database at [bold]{built_path}[/bold]")


@app.command("db-summary")
def db_summary(db_path: Path | None = typer.Option(None, help="SQLite database path.")) -> None:
    """Show table row counts for the local FieldOps database."""
    settings = get_settings()
    path = db_path or settings.db_path
    if not path.exists():
        raise typer.BadParameter(f"Database not found at {path}. Run `fieldops build-db` first.")

    table = Table(title="FieldOps database summary")
    table.add_column("Table")
    table.add_column("Rows", justify="right")

    with sqlite3.connect(path) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
        for (table_name,) in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            table.add_row(table_name, str(count))

    console.print(table)


@app.command("demo")
def demo(db_path: Path | None = typer.Option(None, help="SQLite database path.")) -> None:
    """Run a deterministic end-to-end orchestrator demo."""
    settings = get_settings()
    path = db_path or settings.db_path
    if not path.exists():
        asyncio.run(build_database(path, mode="offline"))

    provider = FakeProvider(
        [
            ModelResponse(text="Compare weed severity across fields using read-only SQL."),
            ModelResponse(
                tool_call=InternalToolCall(
                    call_id="demo-sql-call",
                    provider="gemini",
                    name="execute_read_only_sql",
                    arguments={
                        "query": """
                        SELECT fields.name, MAX(weed_detections.severity_score) AS max_severity
                        FROM fields
                        JOIN weed_detections ON weed_detections.field_id = fields.field_id
                        GROUP BY fields.field_id
                        ORDER BY max_severity DESC
                        """,
                        "max_rows": 5,
                    },
                    server_name="sql_sandbox",
                )
            ),
            ModelResponse(text="North Ridge and Story West show the highest weed pressure."),
        ]
    )
    result = asyncio.run(
        FieldOpsOrchestrator(provider, _router_for_db(path)).answer(
            "Which fields had the highest weed pressure?"
        )
    )
    console.print(result.answer)


@app.command("ask")
def ask(
    question: str = typer.Argument(..., help="Natural-language FieldOps question."),
    db_path: Path | None = typer.Option(None, help="SQLite database path."),
) -> None:
    """Ask a live Gemini-backed FieldOps question."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise typer.BadParameter("GEMINI_API_KEY must be set for live `fieldops ask`.")
    path = db_path or settings.db_path
    if not path.exists():
        asyncio.run(build_database(path, mode="offline"))

    provider = GeminiProvider(api_key=settings.gemini_api_key, model=settings.model)
    result = asyncio.run(FieldOpsOrchestrator(provider, _router_for_db(path)).answer(question))
    console.print(result.answer)


def _router_for_db(db_path: Path) -> AsyncMcpRouter:
    env = {**os.environ, "FIELDOPS_DB_PATH": str(db_path)}
    registry = McpServerRegistry(
        (
            McpServerConfig(
                name="metadata",
                command=sys.executable,
                args=("-m", "fieldops.mcp_servers.metadata_server"),
                env=env,
            ),
            McpServerConfig(
                name="sql_sandbox",
                command=sys.executable,
                args=("-m", "fieldops.mcp_servers.sql_sandbox_server"),
                env=env,
            ),
        )
    )
    return AsyncMcpRouter(registry)


if __name__ == "__main__":
    app()
