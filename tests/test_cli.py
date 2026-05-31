from __future__ import annotations

from typer.testing import CliRunner

from fieldops.cli import app


runner = CliRunner()


def test_build_db_command_creates_database(tmp_path):
    db_path = tmp_path / "fieldops.db"

    result = runner.invoke(app, ["build-db", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert db_path.exists()
    assert "Built FieldOps database" in result.output


def test_db_summary_command_shows_table_counts(tmp_path):
    db_path = tmp_path / "fieldops.db"
    build_result = runner.invoke(app, ["build-db", "--db-path", str(db_path)])

    result = runner.invoke(app, ["db-summary", "--db-path", str(db_path)])

    assert build_result.exit_code == 0
    assert result.exit_code == 0
    assert "fields" in result.output
    assert "missions" in result.output
    assert "weed_detections" in result.output

