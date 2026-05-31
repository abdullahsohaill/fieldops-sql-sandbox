from __future__ import annotations

from typer.testing import CliRunner

from fieldops.cli import app


runner = CliRunner()


def test_demo_command_runs_end_to_end(tmp_path):
    db_path = tmp_path / "fieldops.db"

    result = runner.invoke(app, ["demo", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "North Ridge" in result.output
    assert db_path.exists()


def test_ask_requires_gemini_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = runner.invoke(app, ["ask", "Which fields had high weed pressure?"])

    assert result.exit_code != 0
    assert "GEMINI_API_KEY must be set" in result.output

