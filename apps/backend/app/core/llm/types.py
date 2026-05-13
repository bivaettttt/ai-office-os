from __future__ import annotations

import time
import uuid

from enum import StrEnum
from typing import Any, Literal, Optional

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
    INVALID_JSON_FALLBACK = "invalid_json_fallback"
    FORBIDDEN_PURPOSE_BLOCKED = "forbidden_purpose_blocked"
    SCHEMA_VALIDATION_FAILED = "schema_validation_failed"
    RATE_LIMITED = "rate_limited"


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


class CommandPreviewEnhancement(BaseModel):
    improved_title: str
    improved_description: str
    plan_notes: list[str] = Field(default_factory=list)
    confidence_note: str | None = None


class TaskPlanDraft(BaseModel):
    suggested_steps: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ManagerReviewDraft(BaseModel):
    review_text: str
    quality_notes: list[str] = Field(default_factory=list)
    approval_recommendation: Literal[
        "approve",
        "needs_revision",
        "fail",
    ]


class TaskSummaryResult(BaseModel):
    summary: str
    current_state: str
    next_best_action: str | None = None


class TimelineSummaryResult(BaseModel):
    summary: str
    key_events: list[str] = Field(default_factory=list)
    risks_or_blockers: list[str] = Field(default_factory=list)


class LLMReasoningDiagnostics(BaseModel):
    reasoning_enabled: bool
    allowed_purposes: list[str]
    blocked_purposes: list[str]
    cache_size: int
    rate_limit_settings: dict[str, int]
    recent_rate_limited_count: int
    recent_schema_failures_count: int
    recent_fallbacks_count: int
