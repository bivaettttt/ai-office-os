from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.llm.types import LLMRequest, LLMResponse


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def availability_reason(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def default_model(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def complete(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        raise NotImplementedError
