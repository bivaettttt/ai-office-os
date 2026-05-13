from __future__ import annotations

import time

from app.config.settings import settings
from app.models.task import (
    Task,
    TaskRuntimePhase,
    TaskStep,
    TaskStepStatus,
)
from app.schemas.protocol import TaskStatus


def initialize_task_execution(
    task: Task,
    agent_id: str,
) -> TaskStep | None:
    if not task.steps:
        return None

    task.started_at = task.started_at or time.time()
    task.runtime_phase = TaskRuntimePhase.EXECUTING
    task.active_step_index = 0
    step = task.steps[0]
    step.status = TaskStepStatus.IN_PROGRESS
    step.started_at = step.started_at or time.time()
    step.assigned_agent_id = agent_id
    task.progress = calculate_task_progress(task)
    return step


def calculate_task_progress(task: Task) -> int:
    if not task.steps:
        return task.progress

    total = sum(step.progress for step in task.steps)
    return round(total / len(task.steps))


def advance_task_steps(
    task: Task,
    agent_id: str,
    amount: int,
) -> list[dict]:
    events: list[dict] = []

    if task.runtime_phase == TaskRuntimePhase.PAUSED:
        return events

    if not task.steps:
        task.progress = min(100, task.progress + amount)
        return events

    active_step = task.steps[task.active_step_index]

    if active_step.status != TaskStepStatus.IN_PROGRESS:
        active_step.status = TaskStepStatus.IN_PROGRESS
        task.runtime_phase = TaskRuntimePhase.EXECUTING
        active_step.started_at = active_step.started_at or time.time()
        active_step.assigned_agent_id = agent_id
        events.append(
            {
                "type": "step_started",
                "step": active_step,
            }
        )

    active_step.progress = min(
        100,
        active_step.progress + amount,
    )

    if active_step.progress >= 100:
        active_step.status = TaskStepStatus.COMPLETED
        active_step.completed_at = time.time()
        events.append(
            {
                "type": "step_completed",
                "step": active_step,
            }
        )

        next_index = task.active_step_index + 1

        if next_index < len(task.steps):
            task.active_step_index = next_index
            next_step = task.steps[next_index]
            next_step.status = TaskStepStatus.IN_PROGRESS
            next_step.started_at = time.time()
            next_step.assigned_agent_id = agent_id
            events.append(
                {
                    "type": "step_started",
                    "step": next_step,
                }
            )

    task.progress = calculate_task_progress(task)
    return events


def all_steps_completed(task: Task) -> bool:
    return bool(task.steps) and all(
        step.status == TaskStepStatus.COMPLETED
        for step in task.steps
    )


def review_completed_task(
    task: Task,
    agent_name: str,
) -> str:
    failed_or_skipped = [
        step
        for step in task.steps
        if step.status
        in [
            TaskStepStatus.FAILED,
            TaskStepStatus.SKIPPED,
        ]
    ]

    if failed_or_skipped:
        task.status = TaskStatus.FAILED
        task.runtime_phase = TaskRuntimePhase.FAILED
        task.reviewed_at = time.time()
        task.updated_at = time.time()
        summary = (
            f"Task failed during manager review. "
            f"{len(failed_or_skipped)} step(s) did not complete."
        )
        task.result_summary = summary
        task.failure_reason = summary
        return summary

    task.status = TaskStatus.COMPLETED
    task.runtime_phase = TaskRuntimePhase.COMPLETED
    task.progress = 100
    task.completed_at = time.time()
    task.reviewed_at = time.time()
    task.updated_at = time.time()
    summary = (
        f"Task completed by {agent_name}. "
        f"Plan executed successfully across {len(task.steps)} steps."
    )
    if settings.LLM_REASONING_ENABLED:
        try:
            from app.core.llm.reasoning import (
                LLMReasoningService,
            )
            from app.core.world import world

            draft = LLMReasoningService(world).draft_manager_review(
                task_title=task.title,
                steps=[step.title for step in task.steps],
                agent_name=agent_name,
                result_summary=summary,
            )
            summary = draft["review_text"]
        except Exception:
            pass
    task.result_summary = summary
    task.result = summary
    return summary


def mark_active_step_failed(
    task: Task,
    reason: str,
) -> TaskStep | None:
    if not task.steps:
        task.status = TaskStatus.FAILED
        task.runtime_phase = TaskRuntimePhase.FAILED
        task.failure_reason = reason
        task.updated_at = time.time()
        return None

    step = task.steps[task.active_step_index]
    step.status = TaskStepStatus.FAILED
    step.completed_at = time.time()
    task.status = TaskStatus.FAILED
    task.runtime_phase = TaskRuntimePhase.FAILED
    task.failure_reason = reason
    task.updated_at = time.time()
    return step
