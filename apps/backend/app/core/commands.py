from __future__ import annotations

import time

from pydantic import BaseModel, Field

from app.core.agent_runtime.capabilities import (
    default_capabilities_for_department,
    infer_required_capabilities,
)
from app.core.agent_runtime.planning import (
    generate_task_steps,
)


class CommandRouteResult(BaseModel):
    department: str
    priority: str
    required_capabilities: list[str]
    title: str
    description: str
    explanation: str
    matched_keywords: list[str]


class CommandValidationWarning(BaseModel):
    code: str
    message: str


class CommandPreview(BaseModel):
    normalized_text: str
    inferred_department: str
    inferred_priority: str
    inferred_capabilities: list[str]
    routing_explanation: str
    proposed_title: str
    proposed_description: str
    proposed_steps: list[dict]
    warnings: list[CommandValidationWarning]
    confidence_score: float
    valid: bool = True
    ai_explanation: str | None = None
    ai_improved_title: str | None = None
    ai_improved_description: str | None = None
    ai_plan_notes: str | None = None
    llm_provider_used: str | None = None
    llm_fallback_used: bool = False
    llm_safety_flags: list[str] = Field(default_factory=list)


DEPARTMENT_KEYWORDS: dict[str, list[str]] = {
    "development": [
        "code",
        "app",
        "website",
        "frontend",
        "backend",
        "bug",
        "project",
        "landing",
        "api",
        "component",
        "лендинг",
        "сайт",
        "приложение",
    ],
    "analytics": [
        "analyze",
        "research",
        "market",
        "competitors",
        "report",
        "trends",
        "metrics",
        "проанализируй",
        "рынок",
        "конкуренты",
        "отчет",
    ],
    "assistant": [
        "remind",
        "schedule",
        "calendar",
        "personal",
        "message",
        "plan my day",
        "todo",
        "напомни",
        "запланируй",
        "календарь",
        "задачи",
    ],
    "content": [
        "post",
        "article",
        "copy",
        "text",
        "telegram",
        "script",
        "content",
        "seo",
        "пост",
        "статья",
        "текст",
        "телеграм",
        "контент",
    ],
    "operations": [
        "status",
        "system",
        "health",
        "queue",
        "workload",
        "agents",
        "статус",
        "система",
        "очередь",
        "нагрузка",
        "агенты",
    ],
}

HIGH_PRIORITY = ["urgent", "high", "срочно", "важно"]
LOW_PRIORITY = [
    "later",
    "низкий",
    "когда будет время",
]

SUPPORTED_PRIORITIES = {"low", "normal", "high"}


def normalize_command_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def infer_priority(
    text: str,
    requested_priority: str | None = None,
) -> str:
    if requested_priority in ["low", "normal", "high"]:
        return requested_priority

    normalized = normalize_command_text(text)

    if any(token in normalized for token in HIGH_PRIORITY):
        return "high"

    if any(token in normalized for token in LOW_PRIORITY):
        return "low"

    return "normal"


def validate_command_request(
    text: str,
    requested_department: str | None = None,
    requested_priority: str | None = None,
) -> list[CommandValidationWarning]:
    warnings: list[CommandValidationWarning] = []
    normalized = normalize_command_text(text)

    if not normalized:
        raise ValueError("Command text is required")

    if len(normalized) < 4:
        warnings.append(
            CommandValidationWarning(
                code="too_short",
                message="Command is very short; routing may be ambiguous.",
            )
        )

    if (
        requested_department is not None
        and requested_department not in DEPARTMENT_KEYWORDS
    ):
        raise ValueError(
            f"Unsupported department: {requested_department}"
        )

    if (
        requested_priority is not None
        and requested_priority not in SUPPORTED_PRIORITIES
    ):
        raise ValueError(
            f"Unsupported priority: {requested_priority}"
        )

    return warnings


def route_user_command(
    text: str,
    requested_department: str | None = None,
    requested_priority: str | None = None,
) -> CommandRouteResult:
    normalized = normalize_command_text(text)
    validate_command_request(
        text,
        requested_department,
        requested_priority,
    )
    allowed = set(DEPARTMENT_KEYWORDS)
    matched_department = "assistant"
    matched_keywords: list[str] = []

    if requested_department in allowed:
        matched_department = requested_department
    else:
        for department, keywords in DEPARTMENT_KEYWORDS.items():
            matches = [
                keyword
                for keyword in keywords
                if keyword in normalized
            ]
            if matches:
                matched_department = department
                matched_keywords = matches
                break

    priority = infer_priority(
        normalized,
        requested_priority,
    )
    capabilities = infer_required_capabilities(
        normalized,
        matched_department,
    )
    title = text.strip()[:80] or "Untitled command"
    description = text.strip()

    if requested_department in allowed:
        explanation = (
            f"Department was requested explicitly: "
            f"{matched_department}."
        )
    elif matched_keywords:
        explanation = (
            f"Detected {matched_department} intent from "
            f"keywords: {', '.join(matched_keywords)}. "
            f"Assigned capabilities: "
            f"{', '.join(capabilities)}."
        )
    else:
        explanation = (
            "No strong department keywords detected. "
            "Assigned to Assistant with default capabilities."
        )

    if priority != "normal":
        explanation = (
            f"{explanation} Priority inferred as {priority}."
        )

    return CommandRouteResult(
        department=matched_department,
        priority=priority,
        required_capabilities=capabilities,
        title=title,
        description=description,
        explanation=explanation,
        matched_keywords=matched_keywords,
    )


def build_command_preview(
    text: str,
    requested_department: str | None = None,
    requested_priority: str | None = None,
    edited_title: str | None = None,
    edited_description: str | None = None,
) -> CommandPreview:
    warnings = validate_command_request(
        text,
        requested_department,
        requested_priority,
    )
    normalized = normalize_command_text(text)
    route = route_user_command(
        text,
        requested_department,
        requested_priority,
    )

    default_capabilities = (
        default_capabilities_for_department(
            route.department
        )[:2]
    )
    default_capability_only = (
        route.required_capabilities
        == default_capabilities
    )

    if not route.matched_keywords and not requested_department:
        warnings.append(
            CommandValidationWarning(
                code="fallback_department",
                message=(
                    "Department was selected by fallback logic."
                ),
            )
        )

    if default_capability_only:
        warnings.append(
            CommandValidationWarning(
                code="default_capabilities",
                message=(
                    "Capabilities were inferred from department defaults."
                ),
            )
        )

    confidence = 0.0

    if route.matched_keywords:
        confidence += 0.35

    if route.required_capabilities and not default_capability_only:
        confidence += 0.25

    if requested_priority or any(
        token in normalized
        for token in HIGH_PRIORITY + LOW_PRIORITY
    ):
        confidence += 0.10

    if 12 <= len(normalized) <= 240:
        confidence += 0.10

    if requested_department:
        confidence += 0.20

    confidence = min(1.0, round(confidence, 2))

    if confidence < 0.45:
        warnings.append(
            CommandValidationWarning(
                code="low_confidence",
                message=(
                    "Routing confidence is low; please refine the command."
                ),
            )
        )

    title = (
        edited_title.strip()
        if edited_title and edited_title.strip()
        else route.title
    )
    description = (
        edited_description.strip()
        if edited_description and edited_description.strip()
        else route.description
    )

    return CommandPreview(
        normalized_text=normalized,
        inferred_department=route.department,
        inferred_priority=route.priority,
        inferred_capabilities=route.required_capabilities,
        routing_explanation=route.explanation,
        proposed_title=title,
        proposed_description=description,
        proposed_steps=[
            step.model_dump(mode="json")
            for step in generate_task_steps(route.department)
        ],
        warnings=warnings,
        confidence_score=confidence,
    )
