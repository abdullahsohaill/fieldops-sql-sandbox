from __future__ import annotations

import pytest

from fieldops.agents.provider import FakeProvider, ModelResponse


@pytest.mark.asyncio
async def test_fake_provider_returns_configured_responses():
    provider = FakeProvider([ModelResponse(text="plan"), ModelResponse(text="summary")])

    first = await provider.generate("question")
    second = await provider.generate("result")

    assert first.text == "plan"
    assert second.text == "summary"
    assert provider.prompts == ["question", "result"]

