from __future__ import annotations

import pytest

from app.providers.fake_llm import FakeLLMProvider


@pytest.mark.asyncio
async def test_fake_llm_provider_generate_returns_traceable_markdown_answer() -> None:
    provider = FakeLLMProvider()

    result = await provider.generate(
        messages=[
            {"role": "user", "content": "Who approves leave requests?"},
        ],
        options={"model": "fake-llm"},
    )

    assert result.content == "Fake answer: Who approves leave requests?\n\n[S1] Generated for P0 tests."
    assert result.model_name == "fake-llm"
    assert result.usage == {"input_tokens": 4, "output_tokens": 10}
    assert result.raw_metadata == {"provider": "fake"}


@pytest.mark.asyncio
async def test_fake_llm_provider_stream_returns_normalized_delta_events() -> None:
    provider = FakeLLMProvider(delta_size=12)

    events = [
        event
        async for event in provider.stream(
            messages=[{"role": "user", "content": "Explain citation flow."}],
            options={},
        )
    ]

    assert {event.type for event in events} == {"delta"}
    assert "".join(event.text for event in events) == (
        "Fake answer: Explain citation flow.\n\n[S1] Generated for P0 tests."
    )
    assert events[-1].finish_reason == "stop"
    assert events[-1].usage == {"input_tokens": 3, "output_tokens": 10}


@pytest.mark.asyncio
async def test_fake_llm_provider_health_check_is_ready() -> None:
    provider = FakeLLMProvider()

    result = await provider.health_check()

    assert result == {"status": "ok", "provider": "fake", "model_name": "fake-llm"}
