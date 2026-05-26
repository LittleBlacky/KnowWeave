from __future__ import annotations

from app.core.config import Settings
from app.providers.base import LLMProvider
from app.providers.fake_llm import FakeLLMProvider
from app.providers.qwen import QwenLLMProvider


def build_default_llm_provider(settings: Settings) -> LLMProvider:
    if settings.qwen_enabled and settings.qwen_api_key:
        return QwenLLMProvider(
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_base_url,
            model_name=settings.qwen_chat_model,
            timeout_seconds=settings.qwen_timeout_seconds,
        )
    return FakeLLMProvider()
