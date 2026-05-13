from __future__ import annotations

import re

from app.config.settings import settings
from app.core.llm.types import (
    LLMRequest,
    LLMSafetyFlag,
)

SECRET_PATTERNS = [
    re.compile(r"API_KEY[^\s]*", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9_\-]+"),
    re.compile(r"token=[^\s]+", re.IGNORECASE),
    re.compile(r"password=[^\s]+", re.IGNORECASE),
]


class LLMGuardrailError(Exception):
    def __init__(
        self,
        message: str,
        flags: list[LLMSafetyFlag],
    ):
        super().__init__(message)
        self.flags = flags


def validate_request(
    request: LLMRequest,
) -> list[LLMSafetyFlag]:
    prompt_text = joined_prompt(request)
    flags: list[LLMSafetyFlag] = []

    if request.purpose == "tool_execution":
        raise LLMGuardrailError(
            "LLM tool execution purpose is blocked at this stage.",
            [LLMSafetyFlag.TOOL_EXECUTION_BLOCKED],
        )

    if not prompt_text.strip():
        raise LLMGuardrailError(
            "LLM prompt is empty.",
            [LLMSafetyFlag.EMPTY_PROMPT_BLOCKED],
        )

    if len(prompt_text) > settings.LLM_MAX_PROMPT_CHARS:
        raise LLMGuardrailError(
            "LLM prompt exceeds maximum safe length.",
            [LLMSafetyFlag.PROMPT_TOO_LONG_BLOCKED],
        )

    if contains_secret(prompt_text):
        flags.append(LLMSafetyFlag.SECRET_REDACTED)

    return flags


def joined_prompt(
    request: LLMRequest,
) -> str:
    return "\n".join(
        message.content
        for message in request.messages
    )



def contains_secret(
    value: str,
) -> bool:
    return any(
        pattern.search(value)
        for pattern in SECRET_PATTERNS
    )


def redact_text(
    value: str,
) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def preview(
    value: str,
    limit: int = 240,
) -> str:
    return redact_text(value).replace("\n", " ")[:limit]
