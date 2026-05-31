from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from fieldops.config import get_settings
from fieldops.data.builder import build_database


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


if __name__ == "__main__":
    app()

