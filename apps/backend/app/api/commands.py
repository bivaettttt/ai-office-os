from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.commands import (
    normalize_command_text,
    route_user_command,
)
from app.core.factory import create_task
from app.core.world import world
from app.models.command import (
    CommandStatus,
    UserCommand,
)
from app.models.task import TaskRuntimePhase
from app.core.orchestration.task_status import TaskStatus
from app.orchestration.event_bus import event_bus


router = APIRouter(
    prefix="/commands",
    tags=["commands"],
)


class CreateCommandRequest(BaseModel):
    text: str
    priority: Optional[str] = None
    department: Optional[str] = None


def command_detail(command: UserCommand):
    task = (
        world.tasks.get(command.created_task_id)
        if command.created_task_id
        else None
    )

    return {
        "command": command.model_dump(mode="json"),
        "created_task": (
            task.model_dump(mode="json")
            if task
            else None
        ),
        "activity_log": [
            entry
            for entry in world.activity_log
            if (
                entry.get("task_id")
                == command.created_task_id
            )
        ],
    }


@router.post("")
async def create_command(req: CreateCommandRequest):
    command = UserCommand(
        raw_text=req.text,
        normalized_text=normalize_command_text(req.text),
    )
    world.add_command(command)

    await event_bus.emit(
        "command_received",
        {
            "command_id": command.id,
            "text": command.raw_text,
        },
    )

    try:
        route = route_user_command(
            req.text,
            requested_department=req.department,
            requested_priority=req.priority,
        )
        command.status = CommandStatus.PARSED

        await event_bus.emit(
            "command_parsed",
            {
                "command_id": command.id,
                "department": route.department,
                "priority": route.priority,
            },
        )

        command.inferred_department = route.department
        command.inferred_priority = route.priority
        command.inferred_capabilities = (
            route.required_capabilities
        )
        command.status = CommandStatus.ROUTED

        await event_bus.emit(
            "command_routed",
            {
                "command_id": command.id,
                "department": route.department,
                "capabilities": route.required_capabilities,
            },
        )

        task = create_task(
            title=route.title,
            description=route.description,
            department=route.department,
            priority=route.priority,
            required_capabilities=(
                route.required_capabilities
            ),
        )
        task.status = TaskStatus.QUEUED
        task.runtime_phase = TaskRuntimePhase.QUEUED

        command.created_task_id = task.id
        command.status = CommandStatus.TASK_CREATED
        command.processed_at = time.time()

        world.add_activity(
            None,
            task.id,
            "command_task_created",
            f"Command created task: {task.title}",
        )

        await event_bus.emit(
            "command_task_created",
            {
                "command_id": command.id,
                "task_id": task.id,
                "task_title": task.title,
                "department": task.department,
            },
        )

        return {
            "command": command.model_dump(mode="json"),
            "created_task": task.model_dump(mode="json"),
            "routing_explanation": route.explanation,
        }

    except Exception as exc:
        command.status = CommandStatus.FAILED
        command.error_message = str(exc)
        command.processed_at = time.time()

        await event_bus.emit(
            "command_failed",
            {
                "command_id": command.id,
                "error": command.error_message,
            },
        )

        raise HTTPException(
            status_code=400,
            detail=command.error_message,
        ) from exc


@router.get("")
def list_commands():
    return [
        command.model_dump(mode="json")
        for command in sorted(
            world.commands.values(),
            key=lambda item: item.created_at,
            reverse=True,
        )[:100]
    ]


@router.get("/{command_id}")
def get_command(command_id: str):
    command = world.commands.get(command_id)

    if not command:
        raise HTTPException(
            status_code=404,
            detail="Command not found",
        )

    return command_detail(command)
