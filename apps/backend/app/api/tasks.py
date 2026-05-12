from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.orchestrator import (
    orchestrator,
)

from app.core.world import world
from app.core.factory import create_task as create_world_task
from app.core.orchestration.task_status import TaskStatus
from app.orchestration.event_bus import event_bus


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


class CreateTaskRequest(BaseModel):
    message: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    priority: str = "normal"


def route_department(
    text: str,
    requested_department: Optional[str],
) -> str:
    allowed = {
        "development",
        "analytics",
        "assistant",
        "content",
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

    task = create_world_task(
        title=title,
        description=description,
        department=department,
        priority=req.priority,
    )
    task.status = TaskStatus.QUEUED

    await event_bus.emit(
        "task.created",
        {
            "task_id": task.id,
            "title": task.title,
            "department": task.department,
            "priority": task.priority,
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
