from __future__ import annotations

import time

from app.core.agent_runtime.execution import (
    initialize_task_execution,
)
from app.core.world import World
from app.models.agent import Agent
from app.models.task import (
    Task,
    TaskRuntimePhase,
    TaskStep,
    TaskStepStatus,
)
from app.schemas.protocol import TaskStatus


def assigned_agent(
    world: World,
    task: Task,
) -> Agent | None:
    if not task.assigned_to:
        return None

    return world.agents.get(task.assigned_to)


def pause_task(
    world: World,
    task: Task,
) -> Task:
    task.runtime_phase = TaskRuntimePhase.PAUSED
    task.updated_at = time.time()

    agent = assigned_agent(world, task)
    if agent:
        agent.status = "idle"
        agent.current_action = f"Paused: {task.title}"
        agent.task_progress = task.progress
        agent.last_active_at = time.time()

    world.add_activity(
        task.assigned_to,
        task.id,
        "task_paused",
        f"Task paused: {task.title}",
    )
    return task


def resume_task(
    world: World,
    task: Task,
) -> Task:
    task.status = TaskStatus.IN_PROGRESS
    task.runtime_phase = TaskRuntimePhase.EXECUTING
    task.updated_at = time.time()

    agent = assigned_agent(world, task)
    if agent:
        if agent.current_task_id != task.id:
            agent.workload += 1
        agent.status = "working"
        agent.current_task_id = task.id
        agent.current_action = f"Working on: {task.title}"
        agent.last_active_at = time.time()

    if task.steps:
        step = task.steps[task.active_step_index]
        if step.status == TaskStepStatus.PENDING:
            initialize_task_execution(
                task,
                task.assigned_to or "",
            )

    world.add_activity(
        task.assigned_to,
        task.id,
        "task_resumed",
        f"Task resumed: {task.title}",
    )
    return task


def cancel_task(
    world: World,
    task: Task,
) -> Task:
    agent = assigned_agent(world, task)
    task.status = TaskStatus.CANCELLED
    task.runtime_phase = TaskRuntimePhase.CANCELLED
    task.updated_at = time.time()
    task.failure_reason = "Task cancelled"

    if agent:
        agent.status = "idle"
        agent.current_task_id = None
        agent.task_progress = 0
        agent.current_action = "Ожидает задачу"
        agent.workload = max(0, agent.workload - 1)
        agent.last_active_at = time.time()

    world.add_activity(
        task.assigned_to,
        task.id,
        "task_cancelled",
        f"Task cancelled: {task.title}",
    )
    return task


def retry_failed_step(
    world: World,
    task: Task,
) -> TaskStep | None:
    world.add_activity(
        task.assigned_to,
        task.id,
        "task_retry_requested",
        f"Retry requested: {task.title}",
    )

    if not task.steps:
        return None

    step = task.steps[task.active_step_index]
    if step.status != TaskStepStatus.FAILED:
        failed_index = next(
            (
                index
                for index, item in enumerate(task.steps)
                if item.status == TaskStepStatus.FAILED
            ),
            None,
        )
        if failed_index is None:
            return None

        task.active_step_index = failed_index
        step = task.steps[failed_index]

    step.status = TaskStepStatus.IN_PROGRESS
    step.completed_at = None
    step.started_at = step.started_at or time.time()
    step.assigned_agent_id = task.assigned_to

    task.status = TaskStatus.IN_PROGRESS
    task.runtime_phase = TaskRuntimePhase.EXECUTING
    task.failure_reason = None
    task.updated_at = time.time()

    agent = assigned_agent(world, task)
    if agent:
        agent.status = "working"
        agent.current_task_id = task.id
        agent.current_action = f"Retrying: {step.title}"
        agent.task_progress = task.progress
        agent.last_active_at = time.time()

    world.add_activity(
        task.assigned_to,
        task.id,
        "task_retry_started",
        f"Retry started: {step.title}",
    )
    return step
