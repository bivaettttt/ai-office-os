from __future__ import annotations

from app.core.llm.types import (
    LLMMessage,
    LLMMessageRole,
    LLMRequest,
)


SAFETY_SYSTEM_PROMPT = (
    "You are a local reasoning assistant for AI Office OS. "
    "Do not execute actions. Do not call tools. Do not request secrets. "
    "Do not suggest shell, file, browser, or network actions. "
    "Return only the requested text or JSON shape."
)


def command_explanation_request(
    *,
    text: str,
    department: str,
    priority: str,
    capabilities: list[str],
    routing_explanation: str,
) -> LLMRequest:
    return LLMRequest(
        purpose="command_explanation",
        messages=[
            LLMMessage(
                role=LLMMessageRole.SYSTEM,
                content=SAFETY_SYSTEM_PROMPT,
            ),
            LLMMessage(
                role=LLMMessageRole.USER,
                content=(
                    "Explain this routed command in 1-2 short sentences.\n"
                    f"Command: {text}\n"
                    f"Department: {department}\n"
                    f"Priority: {priority}\n"
                    f"Capabilities: {', '.join(capabilities)}\n"
                    f"Routing explanation: {routing_explanation}"
                ),
            ),
        ],
        metadata={
            "reasoning_template": "command_explanation",
            "department": department,
            "priority": priority,
            "capabilities": capabilities,
        },
    )


def command_preview_enhancement_request(
    *,
    text: str,
    current_title: str,
    current_description: str,
    current_plan: list[str],
) -> LLMRequest:
    return LLMRequest(
        purpose="command_preview_enhancement",
        messages=[
            LLMMessage(
                role=LLMMessageRole.SYSTEM,
                content=SAFETY_SYSTEM_PROMPT,
            ),
            LLMMessage(
                role=LLMMessageRole.USER,
                content=(
                    "Improve this command preview. Return JSON only with keys: "
                    "improved_title, improved_description, plan_notes, confidence_note. "
                    "plan_notes must be an array of short strings.\n"
                    f"Command: {text}\n"
                    f"Current title: {current_title}\n"
                    f"Current description: {current_description}\n"
                    f"Current plan: {', '.join(current_plan)}"
                ),
            ),
        ],
        metadata={
            "reasoning_template": "command_preview_enhancement",
        },
    )


def task_plan_draft_request(
    *,
    title: str,
    department: str,
    capabilities: list[str],
    current_plan: list[str],
) -> LLMRequest:
    return LLMRequest(
        purpose="task_plan_draft",
        messages=[
            LLMMessage(
                role=LLMMessageRole.SYSTEM,
                content=SAFETY_SYSTEM_PROMPT,
            ),
            LLMMessage(
                role=LLMMessageRole.USER,
                content=(
                    "Suggest a refined plan. Return JSON only with key "
                    "suggested_steps, risks, assumptions. "
                    "Each value must be an array of short strings.\n"
                    f"Task title: {title}\n"
                    f"Department: {department}\n"
                    f"Capabilities: {', '.join(capabilities)}\n"
                    f"Current plan: {', '.join(current_plan)}"
                ),
            ),
        ],
        metadata={
            "reasoning_template": "task_plan_draft",
        },
    )


def manager_review_draft_request(
    *,
    task_title: str,
    steps: list[str],
    agent_name: str,
    result_summary: str,
) -> LLMRequest:
    return LLMRequest(
        purpose="manager_review_draft",
        messages=[
            LLMMessage(
                role=LLMMessageRole.SYSTEM,
                content=SAFETY_SYSTEM_PROMPT,
            ),
            LLMMessage(
                role=LLMMessageRole.USER,
                content=(
                    "Write a short manager review draft. Return JSON only with keys: "
                    "review_text, quality_notes, approval_recommendation. "
                    "approval_recommendation must be approve, needs_revision, or fail.\n"
                    f"Task: {task_title}\n"
                    f"Agent: {agent_name}\n"
                    f"Steps: {', '.join(steps)}\n"
                    f"Current summary: {result_summary}"
                ),
            ),
        ],
        metadata={
            "reasoning_template": "manager_review_draft",
        },
    )


def task_summary_request(
    *,
    task_title: str,
    status: str,
    steps: list[str],
    timeline_highlights: list[str],
    task_id: str | None = None,
) -> LLMRequest:
    return LLMRequest(
        purpose="task_summary",
        task_id=task_id,
        messages=[
            LLMMessage(
                role=LLMMessageRole.SYSTEM,
                content=SAFETY_SYSTEM_PROMPT,
            ),
            LLMMessage(
                role=LLMMessageRole.USER,
                content=(
                    "Summarize this task. Return JSON only with keys: "
                    "summary, current_state, next_best_action.\n"
                    f"Task: {task_title}\n"
                    f"Status: {status}\n"
                    f"Steps: {', '.join(steps)}\n"
                    f"Timeline highlights: {' | '.join(timeline_highlights[:6])}"
                ),
            ),
        ],
        metadata={
            "reasoning_template": "task_summary",
        },
    )


def timeline_summary_request(
    *,
    entries: list[str],
) -> LLMRequest:
    return LLMRequest(
        purpose="timeline_summary",
        messages=[
            LLMMessage(
                role=LLMMessageRole.SYSTEM,
                content=SAFETY_SYSTEM_PROMPT,
            ),
            LLMMessage(
                role=LLMMessageRole.USER,
                content=(
                    "Summarize what happened in this timeline. Return JSON only with keys: "
                    "summary, key_events, risks_or_blockers. key_events and risks_or_blockers "
                    "must be arrays of short strings.\n"
                    + "\n".join(entries[:12])
                ),
            ),
        ],
        metadata={
            "reasoning_template": "timeline_summary",
        },
    )
