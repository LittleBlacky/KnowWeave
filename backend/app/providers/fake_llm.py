from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.providers.base import LLMResult, LLMStreamEvent


class FakeLLMProvider:
    def __init__(self, *, model_name: str = "fake-llm", delta_size: int = 16) -> None:
        self.model_name = model_name
        self.delta_size = delta_size

    async def generate(
        self,
        *,
        messages: list[dict[str, str]],
        options: dict[str, Any],
    ) -> LLMResult:
        model_name = str(options.get("model") or self.model_name)
        content = self._answer_for(messages)
        return LLMResult(
            content=content,
            model_name=model_name,
            usage=self._usage_for(messages),
            raw_metadata={"provider": "fake"},
        )

    async def stream(
        self,
        *,
        messages: list[dict[str, str]],
        options: dict[str, Any],
    ) -> AsyncIterator[LLMStreamEvent]:
        content = self._answer_for(messages)
        usage = self._usage_for(messages)
        delta_size = int(options.get("delta_size") or self.delta_size)
        chunks = [content[index : index + delta_size] for index in range(0, len(content), delta_size)]

        for index, chunk in enumerate(chunks):
            is_last = index == len(chunks) - 1
            yield LLMStreamEvent(
                type="delta",
                text=chunk,
                finish_reason="stop" if is_last else None,
                usage=usage if is_last else None,
            )

    async def health_check(self) -> dict[str, Any]:
        return {"status": "ok", "provider": "fake", "model_name": self.model_name}

    def _answer_for(self, messages: list[dict[str, str]]) -> str:
        prompt = messages[-1]["content"] if messages else ""
        return f"Fake answer: {prompt}\n\n[S1] Generated for P0 tests."

    def _usage_for(self, messages: list[dict[str, str]]) -> dict[str, int]:
        input_tokens = sum(len(message.get("content", "").split()) for message in messages)
        return {"input_tokens": input_tokens, "output_tokens": 10}
