from __future__ import annotations

from app.core.llm.guardrails import joined_prompt, preview
from app.core.llm.types import (
    LLMRequest,
    LLMResponse,
    LLMPromptLogEntry,
    LLMSafetyFlag,
)
from app.core.world import World


def create_prompt_log_entry(
    world: World,
    request: LLMRequest,
    provider: str,
    model: str,
    safety_flags: list[LLMSafetyFlag],
    status: str,
    response: LLMResponse | None = None,
    error: str | None = None,
) -> LLMPromptLogEntry:
    entry = LLMPromptLogEntry(
        provider=provider,
        model=model,
        purpose=request.purpose,
        task_id=request.task_id,
        agent_id=request.agent_id,
        command_id=request.command_id,
        prompt_preview=preview(joined_prompt(request)),
        response_preview=(
            preview(response.content)
            if response
            else ""
        ),
        safety_flags=safety_flags,
        status=status,
        error=error,
    )
    world.add_llm_prompt_log(entry)
    return entry
