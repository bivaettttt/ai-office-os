from __future__ import annotations

from app.config.settings import settings
from app.core.llm.providers import LLMProvider
from app.core.llm.types import LLMRequest, LLMResponse


class OllamaProvider(LLMProvider):
    name = "ollama"

    def is_available(self) -> bool:
        return bool(
            settings.LLM_REAL_CALLS_ENABLED
            and settings.OLLAMA_BASE_URL
            and settings.OLLAMA_MODEL
        )

    def availability_reason(self) -> str | None:
        if not settings.LLM_REAL_CALLS_ENABLED:
            return "Real LLM calls are disabled."
        if not settings.OLLAMA_BASE_URL:
            return "OLLAMA_BASE_URL is not configured."
        if not settings.OLLAMA_MODEL:
            return "OLLAMA_MODEL is not configured."
        return None

    def default_model(self) -> str:
        return settings.OLLAMA_MODEL

    def complete(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        return LLMResponse(
            content=(
                "Ollama provider is configured as a safe stub. "
                "No local model call was performed."
            ),
            provider=self.name,
            model=request.model or self.default_model(),
            finish_reason="stub",
        )
