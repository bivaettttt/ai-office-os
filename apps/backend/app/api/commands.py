from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.commands import (
    build_command_preview,
    normalize_command_text,
    route_user_command,
)
from app.core.runtime_timeline import (
    build_runtime_timeline,
)
from app.core.factory import create_task
from app.core.llm.reasoning import LLMReasoningService
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
    title: Optional[str] = None
    description: Optional[str] = None


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
        "timeline": build_runtime_timeline(
            world,
            command_id=command.id,
            limit=100,
        )["entries"],
        "routing_explanation": (
            f"Command routed to {command.inferred_department} "
            f"with {', '.join(command.inferred_capabilities)}."
            if command.inferred_department
            else None
        ),
    }


@router.post("/preview")
def preview_command(req: CreateCommandRequest):
    try:
        preview = build_command_preview(
            req.text,
            requested_department=req.department,
            requested_priority=req.priority,
            edited_title=req.title,
            edited_description=req.description,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    preview_payload = preview.model_dump(mode="json")
    reasoning = LLMReasoningService(world)
    explain_result = reasoning.explain_command(
        text=req.text,
        department=preview.inferred_department,
        priority=preview.inferred_priority,
        capabilities=preview.inferred_capabilities,
        routing_explanation=preview.routing_explanation,
    )
    enhancement_result = reasoning.enhance_command_preview(
        text=req.text,
        current_title=preview.proposed_title,
        current_description=preview.proposed_description,
        current_plan=[
            step["title"]
            for step in preview.proposed_steps
        ],
    )

    preview_payload["ai_explanation"] = explain_result["text"]
    preview_payload["ai_improved_title"] = enhancement_result.get(
        "improved_title"
    )
    preview_payload["ai_improved_description"] = enhancement_result.get(
        "improved_description"
    )
    preview_payload["ai_plan_notes"] = enhancement_result.get("plan_notes", [])
    preview_payload["ai_confidence_note"] = enhancement_result.get(
        "confidence_note"
    )
    preview_payload["llm_provider_used"] = (
        enhancement_result.get("provider_used")
        if enhancement_result.get("provider_used") != "rules"
        else explain_result.get("provider_used")
    )
    preview_payload["llm_fallback_used"] = bool(
        explain_result.get("fallback_used")
        or enhancement_result.get("fallback_used")
    )
    preview_payload["llm_safety_flags"] = sorted(
        set(
            [
                *explain_result.get("safety_flags", []),
                *enhancement_result.get("safety_flags", []),
            ]
        )
    )
    preview_payload["llm_fallback_reason"] = (
        enhancement_result.get("fallback_reason")
        or explain_result.get("fallback_reason")
    )

    return {"preview": preview_payload}


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
        preview = build_command_preview(
            req.text,
            requested_department=req.department,
            requested_priority=req.priority,
            edited_title=req.title,
            edited_description=req.description,
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
            title=preview.proposed_title,
            description=preview.proposed_description,
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
