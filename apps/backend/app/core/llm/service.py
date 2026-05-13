from __future__ import annotations

from app.config.settings import settings
from app.core.llm.guardrails import (
    LLMGuardrailError,
    validate_request,
)
from app.core.llm.mock_provider import MockProvider
from app.core.llm.ollama_provider import OllamaProvider
from app.core.llm.prompt_log import create_prompt_log_entry
from app.core.llm.providers import LLMProvider
from app.core.llm.types import (
    LLMMessage,
    LLMMessageRole,
    LLMProviderName,
    LLMProviderStatus,
    LLMRequest,
    LLMResponse,
    LLMStatusResponse,
    LLMSafetyFlag,
)
from app.core.world import World


class LLMService:
    def __init__(
        self,
        world: World,
        provider_override: str | None = None,
    ):
        self.world = world
        self.providers: dict[str, LLMProvider] = {
            LLMProviderName.MOCK.value: MockProvider(),
            LLMProviderName.OLLAMA.value: OllamaProvider(),
        }
        self.selected_provider = (
            provider_override or settings.LLM_PROVIDER
        )

    def complete(
        self,
        request: LLMRequest,
    ) -> tuple[LLMResponse, str | None]:
        provider = self._select_provider()
        fallback_used = (
            provider.name != self.selected_provider
        )
        safety_flags: list[LLMSafetyFlag] = []

        self.world.add_event(
            "llm_request_started",
            {
                "provider": provider.name,
                "selected_provider": self.selected_provider,
                "purpose": request.purpose,
                "task_id": request.task_id,
                "agent_id": request.agent_id,
                "command_id": request.command_id,
            },
        )

        try:
            safety_flags.extend(validate_request(request))
            if not settings.LLM_REAL_CALLS_ENABLED:
                safety_flags.append(
                    LLMSafetyFlag.REAL_CALLS_DISABLED
                )
            if fallback_used:
                safety_flags.append(
                    LLMSafetyFlag.PROVIDER_FALLBACK_USED
                )
                self.world.add_event(
                    "llm_provider_fallback_used",
                    {
                        "selected_provider": self.selected_provider,
                        "active_provider": provider.name,
                    },
                )

            response = provider.complete(request)
            response.safety_flags = sorted(
                set(
                    [
                        *response.safety_flags,
                        *safety_flags,
                    ]
                )
            )

            log_entry_id = self._log(
                request=request,
                response=response,
                provider=provider.name,
                model=response.model,
                safety_flags=response.safety_flags,
                status="completed",
            )
            self.world.add_event(
                "llm_request_completed",
                {
                    "provider": provider.name,
                    "model": response.model,
                    "purpose": request.purpose,
                    "log_entry_id": log_entry_id,
                },
            )
            return response, log_entry_id
        except LLMGuardrailError as exc:
            self.world.add_event(
                "llm_guardrail_blocked",
                {
                    "provider": provider.name,
                    "purpose": request.purpose,
                    "error": str(exc),
                    "safety_flags": [
                        flag.value
                        for flag in exc.flags
                    ],
                },
            )
            log_entry_id = self._log(
                request=request,
                response=None,
                provider=provider.name,
                model=request.model or provider.default_model(),
                safety_flags=exc.flags,
                status="blocked",
                error=str(exc),
            )
            raise LLMGuardrailError(
                f"{str(exc)} log_entry_id={log_entry_id}",
                exc.flags,
            ) from exc
        except Exception as exc:
            self.world.add_event(
                "llm_request_failed",
                {
                    "provider": provider.name,
                    "purpose": request.purpose,
                    "error": str(exc),
                },
            )
            self._log(
                request=request,
                response=None,
                provider=provider.name,
                model=request.model or provider.default_model(),
                safety_flags=safety_flags,
                status="failed",
                error=str(exc),
            )
            raise

    def status(self) -> LLMStatusResponse:
        active = self._select_provider()
        return LLMStatusResponse(
            selected_provider=self.selected_provider,
            active_provider=active.name,
            real_calls_enabled=settings.LLM_REAL_CALLS_ENABLED,
            providers=[
                LLMProviderStatus(
                    name=provider.name,
                    available=provider.is_available(),
                    model=provider.default_model(),
                    reason=provider.availability_reason(),
                )
                for provider in self.providers.values()
            ],
            model_configuration={
                "llm_provider": settings.LLM_PROVIDER,
                "llm_timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
                "llm_max_prompt_chars": settings.LLM_MAX_PROMPT_CHARS,
                "ollama_base_url": settings.OLLAMA_BASE_URL,
                "ollama_model": settings.OLLAMA_MODEL,
            },
            prompt_log_enabled=settings.LLM_PROMPT_LOG_ENABLED,
        )

    def test_prompt(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> tuple[LLMResponse, str | None]:
        service = (
            LLMService(self.world, provider)
            if provider
            else self
        )
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role=LLMMessageRole.USER,
                    content=prompt,
                )
            ],
            model=model,
            purpose="llm_test",
        )
        return service.complete(request)

    def _select_provider(self) -> LLMProvider:
        selected = self.providers.get(
            self.selected_provider,
            self.providers[LLMProviderName.MOCK.value],
        )
        if selected.is_available():
            return selected
        return self.providers[LLMProviderName.MOCK.value]

    def _log(
        self,
        request: LLMRequest,
        response: LLMResponse | None,
        provider: str,
        model: str,
        safety_flags: list[LLMSafetyFlag],
        status: str,
        error: str | None = None,
    ) -> str | None:
        if not settings.LLM_PROMPT_LOG_ENABLED:
            return None
        entry = create_prompt_log_entry(
            self.world,
            request=request,
            response=response,
            provider=provider,
            model=model,
            safety_flags=safety_flags,
            status=status,
            error=error,
        )
        return entry.id
