from __future__ import annotations

import json

import httpx
import pytest

from app.providers.base import LLMProviderError
from app.providers.qwen import QwenLLMProvider


@pytest.mark.asyncio
async def test_qwen_provider_generate_uses_openai_compatible_chat_completion() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["authorization"]
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "qwen-plus",
                "choices": [{"message": {"content": "Real answer [S1]"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 4},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = QwenLLMProvider(
            api_key="test-key",
            base_url="https://dashscope.test/compatible-mode/v1",
            model_name="qwen-plus",
            client=client,
        )

        result = await provider.generate(
            messages=[{"role": "user", "content": "Who approves access?"}],
            options={},
        )

    assert captured["url"] == "https://dashscope.test/compatible-mode/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-key"
    assert captured["payload"] == {
        "messages": [{"role": "user", "content": "Who approves access?"}],
        "model": "qwen-plus",
        "stream": False,
    }
    assert result.content == "Real answer [S1]"
    assert result.model_name == "qwen-plus"
    assert result.usage == {"input_tokens": 9, "output_tokens": 4}
    assert result.raw_metadata == {"provider": "qwen", "finish_reason": "stop"}


@pytest.mark.asyncio
async def test_qwen_provider_stream_parses_sse_delta_lines() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["stream"] is True
        body = "\n\n".join(
            [
                'data: {"choices":[{"delta":{"content":"Hello "}}]}',
                'data: {"choices":[{"delta":{"content":"world"},"finish_reason":"stop"}]}',
                "data: [DONE]",
            ],
        )
        return httpx.Response(200, text=body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = QwenLLMProvider(api_key="test-key", client=client)

        events = [
            event
            async for event in provider.stream(
                messages=[{"role": "user", "content": "Say hello"}],
                options={},
            )
        ]

    assert [event.text for event in events] == ["Hello ", "world"]
    assert events[-1].finish_reason == "stop"


@pytest.mark.asyncio
async def test_qwen_provider_raises_sanitized_provider_errors() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"message": "Invalid API key."}},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = QwenLLMProvider(api_key="test-key", client=client)

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.generate(messages=[{"role": "user", "content": "ping"}], options={})

    assert str(exc_info.value) == "Invalid API key."
    assert exc_info.value.status_code == 401
