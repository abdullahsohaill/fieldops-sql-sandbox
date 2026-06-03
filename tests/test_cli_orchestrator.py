from __future__ import annotations

from typer.testing import CliRunner

from fieldops.cli import app
import fieldops.config as fieldops_config
from fieldops.agents.provider import ModelProviderError


runner = CliRunner()


def test_demo_command_runs_end_to_end(tmp_path):
    db_path = tmp_path / "fieldops.db"

    result = runner.invoke(app, ["demo", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "North Ridge" in result.output
    assert db_path.exists()


def test_ask_requires_gemini_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setattr(fieldops_config, "ENV_FILE", tmp_path / "missing.env")

    result = runner.invoke(app, ["ask", "Which fields had high weed pressure?"])

    assert result.exit_code != 0
    assert "GEMINI_API_KEY must be set" in result.output


def test_ask_surfaces_provider_failures_cleanly(tmp_path, monkeypatch):
    class FailingGeminiProvider:
        def __init__(self, api_key: str, model: str) -> None:
            self.api_key = api_key
            self.model = model

        async def generate(self, *args, **kwargs):
            raise ModelProviderError("Gemini request failed for model `test-model`: 503 UNAVAILABLE")

    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=test-key\nFIELDOPS_MODEL=test-model\n")

    monkeypatch.setattr(fieldops_config, "ENV_FILE", env_file)
    monkeypatch.setattr("fieldops.cli.GeminiProvider", FailingGeminiProvider)

    result = runner.invoke(app, ["ask", "Which fields had high weed pressure?"])

    assert result.exit_code != 0
    output = result.output.replace("\n", "")
    assert "Gemini request failed" in output
    assert "503 UNAVAILABLE" in output
    assert "Retry shortly or set FIELDOPS_MODEL" in output
