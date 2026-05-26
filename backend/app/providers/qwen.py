from __future__ import annotations

from collections.abc import AsyncIterator
import json
from typing import Any

import httpx

from app.providers.base import LLMProviderError, LLMResult, LLMStreamEvent


class QwenLLMProvider:
    provider_name = "qwen"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_name: str = "qwen-plus",
        timeout_seconds: float = 60.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise LLMProviderError("Qwen API key is not configured.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self._client = client

    async def generate(
        self,
        *,
        messages: list[dict[str, str]],
        options: dict[str, Any],
    ) -> LLMResult:
        payload = self._payload(messages=messages, options=options, stream=False)
        response = await self._post_json(payload)
        choice = (response.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = str(message.get("content") or "")
        return LLMResult(
            content=content,
            model_name=str(response.get("model") or payload["model"]),
            usage=self._usage(response.get("usage")),
            raw_metadata={"provider": self.provider_name, "finish_reason": choice.get("finish_reason")},
        )

    async def stream(
        self,
        *,
        messages: list[dict[str, str]],
        options: dict[str, Any],
    ) -> AsyncIterator[LLMStreamEvent]:
        payload = self._payload(messages=messages, options=options, stream=True)
        async with self._stream_response(payload) as response:
            self._raise_for_status(response)
            async for line in response.aiter_lines():
                event = self._parse_stream_line(line)
                if event is None:
                    continue
                yield event

    async def health_check(self) -> dict[str, Any]:
        result = await self.generate(
            messages=[{"role": "user", "content": "ping"}],
            options={"max_tokens": 1},
        )
        return {
            "status": "ok",
            "provider": self.provider_name,
            "model_name": result.model_name,
        }

    def _payload(
        self,
        *,
        messages: list[dict[str, str]],
        options: dict[str, Any],
        stream: bool,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "messages": messages,
            "model": str(options.get("model") or self.model_name),
            "stream": stream,
        }
        if "temperature" in options:
            payload["temperature"] = options["temperature"]
        if "max_tokens" in options:
            payload["max_tokens"] = options["max_tokens"]
        return payload

    async def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._client is not None:
            response = await self._client.post(self._endpoint, headers=self._headers, json=payload)
            self._raise_for_status(response)
            return response.json()

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(self._endpoint, headers=self._headers, json=payload)
            self._raise_for_status(response)
            return response.json()

    def _stream_response(self, payload: dict[str, Any]):
        if self._client is not None:
            return self._client.stream("POST", self._endpoint, headers=self._headers, json=payload)

        client = httpx.AsyncClient(timeout=self.timeout_seconds)
        return _OwnedStream(client, self._endpoint, self._headers, payload)

    def _parse_stream_line(self, line: str) -> LLMStreamEvent | None:
        if not line.startswith("data: "):
            return None
        data = line.removeprefix("data: ").strip()
        if not data or data == "[DONE]":
            return None
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("Qwen returned malformed stream data.") from exc

        choice = (payload.get("choices") or [{}])[0]
        delta = choice.get("delta") or {}
        text = delta.get("content")
        if not text:
            return None
        return LLMStreamEvent(
            type="delta",
            text=str(text),
            finish_reason=choice.get("finish_reason"),
            usage=self._usage(payload.get("usage")) if payload.get("usage") else None,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        message = "Qwen provider request failed."
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict) and error.get("message"):
            message = str(error["message"])
        raise LLMProviderError(message, status_code=response.status_code)

    def _usage(self, raw_usage: Any) -> dict[str, int]:
        if not isinstance(raw_usage, dict):
            return {}
        return {
            "input_tokens": int(raw_usage.get("prompt_tokens") or raw_usage.get("input_tokens") or 0),
            "output_tokens": int(raw_usage.get("completion_tokens") or raw_usage.get("output_tokens") or 0),
        }

    @property
    def _endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json",
        }


class _OwnedStream:
    def __init__(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> None:
        self.client = client
        self.endpoint = endpoint
        self.headers = headers
        self.payload = payload
        self.response_context = None

    async def __aenter__(self) -> httpx.Response:
        self.response_context = self.client.stream(
            "POST",
            self.endpoint,
            headers=self.headers,
            json=self.payload,
        )
        return await self.response_context.__aenter__()

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        if self.response_context is not None:
            await self.response_context.__aexit__(exc_type, exc, traceback)
        await self.client.aclose()
