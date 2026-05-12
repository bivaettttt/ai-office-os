from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.orchestrator import (
    orchestrator,
)

from app.core.world import world
from app.core.factory import create_task as create_world_task
from app.core.orchestration.task_status import TaskStatus
from app.models.task import TaskRuntimePhase
from app.core.agent_runtime.capabilities import (
    infer_required_capabilities,
    normalize_capabilities,
)
from app.core.agent_runtime.control import (
    cancel_task as cancel_runtime_task,
    pause_task as pause_runtime_task,
    resume_task as resume_runtime_task,
    retry_failed_step as retry_runtime_step,
)
from app.orchestration.event_bus import event_bus


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


def get_task_or_404(task_id: str):
    task = world.tasks.get(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return task


def task_detail(task):
    assigned_agent = (
        world.agents.get(task.assigned_to)
        if task.assigned_to
        else None
    )
    assigned_manager = (
        world.agents.get(task.assigned_by_manager_id)
        if task.assigned_by_manager_id
        else None
    )

    return {
        "task": task.model_dump(mode="json"),
        "assigned_agent": (
            assigned_agent.model_dump(mode="json")
            if assigned_agent
            else None
        ),
        "assigned_manager": (
            assigned_manager.model_dump(mode="json")
            if assigned_manager
            else None
        ),
        "activity_log": [
            entry
            for entry in world.activity_log
            if entry.get("task_id") == task.id
        ],
    }


class CreateTaskRequest(BaseModel):
    message: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    priority: str = "normal"
    required_capabilities: list[str] = Field(
        default_factory=list
    )


def route_department(
    text: str,
    requested_department: Optional[str],
) -> str:
    allowed = {
        "development",
        "analytics",
        "assistant",
        "content",
        "operations",
    }

    if requested_department in allowed:
        return requested_department

    lower = text.lower()

    if any(
        token in lower
        for token in [
            "code",
            "api",
            "frontend",
            "backend",
            "bug",
            "site",
            "app",
        ]
    ):
        return "development"

    if any(
        token in lower
        for token in [
            "research",
            "analytics",
            "market",
            "report",
            "metric",
            "analyze",
        ]
    ):
        return "analytics"

    if any(
        token in lower
        for token in [
            "content",
            "article",
            "seo",
            "post",
        ]
    ):
        return "content"

    if any(
        token in lower
        for token in [
            "project",
            "ops",
            "operations",
            "coordinate",
            "quality",
        ]
    ):
        return "operations"

    return "assistant"


# =====================================================
# CREATE TASK
# =====================================================

@router.post("")
async def create_task(
    req: CreateTaskRequest,
):

    if req.message and not req.title:
        return await orchestrator.process_user_request(
            req.message
        )

    title = (
        req.title
        or req.message
        or "Untitled task"
    ).strip()
    description = (
        req.description
        or req.message
        or title
    ).strip()
    department = route_department(
        f"{title} {description}",
        req.department,
    )
    required_capabilities = normalize_capabilities(
        req.required_capabilities
        or infer_required_capabilities(
            f"{title} {description}",
            department,
        )
    )

    task = create_world_task(
        title=title,
        description=description,
        department=department,
        priority=req.priority,
        required_capabilities=required_capabilities,
    )
    task.status = TaskStatus.QUEUED
    task.runtime_phase = TaskRuntimePhase.QUEUED

    await event_bus.emit(
        "task.created",
        {
            "task_id": task.id,
            "title": task.title,
            "department": task.department,
            "priority": task.priority,
            "required_capabilities": (
                task.required_capabilities
            ),
        },
    )

    return {
        "status": "queued",
        "department": department,
        "task_id": task.id,
        "task": task.model_dump(mode="json"),
    }


# =====================================================
# LIST TASKS
# =====================================================

@router.get("")
def get_tasks():

    return list(
        world.serialize()["tasks"].values()
    )


@router.get("/{task_id}")
def get_task_detail(task_id: str):
    return task_detail(get_task_or_404(task_id))


@router.post("/{task_id}/pause")
async def pause_task(task_id: str):
    task = pause_runtime_task(
        world,
        get_task_or_404(task_id),
    )
    await event_bus.emit(
        "task.paused",
        {
            "task_id": task.id,
            "task_title": task.title,
        },
    )
    return task_detail(task)


@router.post("/{task_id}/resume")
async def resume_task(task_id: str):
    task = resume_runtime_task(
        world,
        get_task_or_404(task_id),
    )
    await event_bus.emit(
        "task.resumed",
        {
            "task_id": task.id,
            "task_title": task.title,
        },
    )
    return task_detail(task)


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    task = cancel_runtime_task(
        world,
        get_task_or_404(task_id),
    )
    await event_bus.emit(
        "task.cancelled",
        {
            "task_id": task.id,
            "task_title": task.title,
        },
    )
    return task_detail(task)


@router.post("/{task_id}/retry-step")
async def retry_step(task_id: str):
    task = get_task_or_404(task_id)
    step = retry_runtime_step(world, task)

    if not step:
        raise HTTPException(
            status_code=409,
            detail="No failed step to retry",
        )

    await event_bus.emit(
        "task.retry_started",
        {
            "task_id": task.id,
            "task_title": task.title,
            "step_id": step.id,
            "step_title": step.title,
        },
    )
    return task_detail(task)
