from __future__ import annotations

from enum import StrEnum


class Capability(StrEnum):
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    WEB_RESEARCH = "web_research"
    REPORT_WRITING = "report_writing"
    SCHEDULING = "scheduling"
    COMMUNICATION = "communication"
    CONTENT_WRITING = "content_writing"
    DATA_ANALYSIS = "data_analysis"
    TASK_PLANNING = "task_planning"
    QUALITY_REVIEW = "quality_review"
    PROJECT_MANAGEMENT = "project_management"


ALL_CAPABILITIES = {capability.value for capability in Capability}

DEPARTMENT_DEFAULT_CAPABILITIES: dict[str, list[str]] = {
    "development": [
        Capability.CODE_GENERATION,
        Capability.CODE_REVIEW,
        Capability.DEBUGGING,
        Capability.QUALITY_REVIEW,
    ],
    "analytics": [
        Capability.WEB_RESEARCH,
        Capability.REPORT_WRITING,
        Capability.DATA_ANALYSIS,
        Capability.QUALITY_REVIEW,
    ],
    "assistant": [
        Capability.SCHEDULING,
        Capability.COMMUNICATION,
        Capability.TASK_PLANNING,
    ],
    "content": [
        Capability.CONTENT_WRITING,
        Capability.REPORT_WRITING,
        Capability.COMMUNICATION,
        Capability.QUALITY_REVIEW,
    ],
    "operations": [
        Capability.PROJECT_MANAGEMENT,
        Capability.TASK_PLANNING,
        Capability.COMMUNICATION,
        Capability.QUALITY_REVIEW,
    ],
}


def normalize_capability(value: str | Capability) -> str:
    capability = value.value if isinstance(value, Capability) else value
    capability = capability.strip().lower()

    if capability not in ALL_CAPABILITIES:
        raise ValueError(f"unknown capability: {value}")

    return capability


def normalize_capabilities(
    values: list[str | Capability] | None,
) -> list[str]:
    if not values:
        return []

    normalized: list[str] = []

    for value in values:
        capability = normalize_capability(value)
        if capability not in normalized:
            normalized.append(capability)

    return normalized


def default_capabilities_for_department(
    department: str,
) -> list[str]:
    return [
        capability.value
        if isinstance(capability, Capability)
        else capability
        for capability in DEPARTMENT_DEFAULT_CAPABILITIES.get(
            department,
            [],
        )
    ]


def infer_required_capabilities(
    text: str,
    department: str | None = None,
) -> list[str]:
    lower = text.lower()
    inferred: list[Capability] = []

    def add(*capabilities: Capability) -> None:
        for capability in capabilities:
            if capability not in inferred:
                inferred.append(capability)

    if any(token in lower for token in ["bug", "debug", "error", "traceback"]):
        add(Capability.DEBUGGING)

    if any(token in lower for token in ["frontend", "ui", "react", "api", "backend", "code"]):
        add(Capability.CODE_GENERATION)

    if any(token in lower for token in ["review", "qa", "quality"]):
        add(Capability.CODE_REVIEW, Capability.QUALITY_REVIEW)

    if any(token in lower for token in ["research", "market", "analyze", "analytics", "metric"]):
        add(Capability.WEB_RESEARCH, Capability.DATA_ANALYSIS)

    if any(token in lower for token in ["report", "summary", "brief"]):
        add(Capability.REPORT_WRITING)

    if any(token in lower for token in ["schedule", "calendar", "reminder"]):
        add(Capability.SCHEDULING)

    if any(token in lower for token in ["post", "article", "content", "seo"]):
        add(Capability.CONTENT_WRITING)

    if any(token in lower for token in ["plan", "project", "coordinate"]):
        add(Capability.TASK_PLANNING, Capability.PROJECT_MANAGEMENT)

    if not inferred and department:
        return default_capabilities_for_department(department)[:2]

    return [capability.value for capability in inferred]
