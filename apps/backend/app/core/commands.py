from __future__ import annotations

import time

from pydantic import BaseModel

from app.core.agent_runtime.capabilities import (
    infer_required_capabilities,
)


class CommandRouteResult(BaseModel):
    department: str
    priority: str
    required_capabilities: list[str]
    title: str
    description: str
    explanation: str
    matched_keywords: list[str]


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


def route_user_command(
    text: str,
    requested_department: str | None = None,
    requested_priority: str | None = None,
) -> CommandRouteResult:
    normalized = normalize_command_text(text)
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
