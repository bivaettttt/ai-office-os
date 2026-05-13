from __future__ import annotations

import time
import uuid

from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, Field


class LLMProviderName(StrEnum):
    MOCK = "mock"
    OLLAMA = "ollama"


class LLMMessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class LLMSafetyFlag(StrEnum):
    EMPTY_PROMPT_BLOCKED = "empty_prompt_blocked"
    PROMPT_TOO_LONG_BLOCKED = "prompt_too_long_blocked"
    SECRET_REDACTED = "secret_redacted"
    TOOL_EXECUTION_BLOCKED = "tool_execution_blocked"
    REAL_CALLS_DISABLED = "real_calls_disabled"
    PROVIDER_FALLBACK_USED = "provider_fallback_used"


class LLMMessage(BaseModel):
    role: LLMMessageRole
    content: str
    name: Optional[str] = None


class LLMRequest(BaseModel):
    messages: list[LLMMessage]
    model: Optional[str] = None
    temperature: float = 0.2
    max_tokens: Optional[int] = None
    purpose: str = "general"
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    command_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    usage: Optional[dict[str, Any]] = None
    finish_reason: Optional[str] = None
    safety_flags: list[LLMSafetyFlag] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class LLMPromptLogEntry(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    timestamp: float = Field(default_factory=time.time)
    provider: str
    model: str
    purpose: str
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    command_id: Optional[str] = None
    prompt_preview: str = ""
    response_preview: str = ""
    safety_flags: list[LLMSafetyFlag] = Field(default_factory=list)
    status: str
    error: Optional[str] = None


class LLMProviderStatus(BaseModel):
    name: str
    available: bool
    model: Optional[str] = None
    reason: Optional[str] = None


class LLMStatusResponse(BaseModel):
    selected_provider: str
    active_provider: str
    real_calls_enabled: bool
    providers: list[LLMProviderStatus]
    model_configuration: dict[str, Any]
    prompt_log_enabled: bool
