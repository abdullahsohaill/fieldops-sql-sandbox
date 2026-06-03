from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from fieldops.agents.provider import FakeProvider, GeminiProvider, ModelResponse
from fieldops.config import load_env_file
from fieldops.tools.protocol import InternalToolSpec, ToolCatalog


@pytest.mark.asyncio
async def test_fake_provider_returns_configured_responses():
    provider = FakeProvider([ModelResponse(text="plan"), ModelResponse(text="summary")])

    first = await provider.generate("question")
    second = await provider.generate("result")

    assert first.text == "plan"
    assert second.text == "summary"
    assert provider.prompts == ["question", "result"]


def test_load_env_file_sets_missing_environment_variables(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=test-key\nFIELDOPS_MODEL=test-model\n")

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("FIELDOPS_MODEL", raising=False)

    load_env_file(env_file)

    assert os.environ["GEMINI_API_KEY"] == "test-key"
    assert os.environ["FIELDOPS_MODEL"] == "test-model"


@pytest.mark.asyncio
async def test_gemini_provider_normalizes_function_calls(monkeypatch):
    async def fake_generate_content(*, model, contents, config=None):
        return SimpleNamespace(
            text=None,
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[
                            SimpleNamespace(
                                function_call=SimpleNamespace(
                                    id="call-1",
                                    name="execute_read_only_sql",
                                    args={"query": "SELECT * FROM fields"},
                                )
                            )
                        ]
                    )
                )
            ],
        )

    provider = GeminiProvider(api_key="test-key", model="test-model")
    monkeypatch.setattr(provider.client.aio.models, "generate_content", fake_generate_content)

    catalog = ToolCatalog(
        (
            InternalToolSpec(
                name="execute_read_only_sql",
                description="Execute SQL",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                server_name="sql_sandbox",
            ),
        )
    )

    response = await provider.generate("question", tools=catalog)

    assert response.tool_call is not None
    assert response.tool_call.call_id == "call-1"
    assert response.tool_call.server_name == "sql_sandbox"
    assert response.tool_call.arguments == {"query": "SELECT * FROM fields"}
