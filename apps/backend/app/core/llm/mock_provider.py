from __future__ import annotations

from app.core.llm.providers import LLMProvider
from app.core.llm.types import LLMRequest, LLMResponse


class MockProvider(LLMProvider):
    name = "mock"

    def is_available(self) -> bool:
        return True

    def availability_reason(self) -> str | None:
        return None

    def default_model(self) -> str:
        return "mock-safe-model"

    def complete(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        user_text = next(
            (
                message.content
                for message in reversed(request.messages)
                if message.role == "user"
            ),
            "",
        )
        model = request.model or self.default_model()

        return LLMResponse(
            content=(
                f"[mock:{model}] Safe deterministic response for "
                f"{request.purpose}: {user_text[:160]}"
            ),
            provider=self.name,
            model=model,
            usage={
                "prompt_chars": sum(
                    len(message.content)
                    for message in request.messages
                ),
                "completion_chars": min(len(user_text), 160),
            },
            finish_reason="stop",
        )
