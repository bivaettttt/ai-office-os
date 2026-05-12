from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.tools.executor import ToolExecutor
from app.core.tools.registry import tool_registry
from app.core.world import world


router = APIRouter()


class ToolInvokeRequest(BaseModel):
    tool_id: str
    task_id: str | None = None
    agent_id: str | None = None
    requested_by: str = "user"
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolApprovalRequest(BaseModel):
    approved_by: str = "user"


class ToolRejectRequest(BaseModel):
    rejected_by: str = "user"


def executor() -> ToolExecutor:
    return ToolExecutor(world)


@router.get("/tools")
def list_tools():
    return [
        tool.model_dump(mode="json")
        for tool in tool_registry.list_tools()
    ]


@router.get("/tools/invocations")
def list_tool_invocations():
    return [
        invocation.model_dump(mode="json")
        for invocation in sorted(
            world.tool_invocations.values(),
            key=lambda item: item.created_at,
            reverse=True,
        )
    ]


@router.post("/tools/invoke")
def invoke_tool(request: ToolInvokeRequest):
    invocation = executor().invoke(
        tool_id=request.tool_id,
        task_id=request.task_id,
        agent_id=request.agent_id,
        requested_by=request.requested_by,
        arguments=request.arguments,
    )
    return invocation.model_dump(mode="json")


@router.post("/tools/invocations/{invocation_id}/approve")
def approve_tool_invocation(
    invocation_id: str,
    request: ToolApprovalRequest | None = None,
):
    invocation = executor().approve(
        invocation_id,
        approved_by=(
            request.approved_by
            if request
            else "user"
        ),
    )

    if invocation is None:
        raise HTTPException(
            status_code=404,
            detail="Tool invocation not found.",
        )

    return invocation.model_dump(mode="json")


@router.post("/tools/invocations/{invocation_id}/reject")
def reject_tool_invocation(
    invocation_id: str,
    request: ToolRejectRequest | None = None,
):
    invocation = executor().reject(
        invocation_id,
        rejected_by=(
            request.rejected_by
            if request
            else "user"
        ),
    )

    if invocation is None:
        raise HTTPException(
            status_code=404,
            detail="Tool invocation not found.",
        )

    return invocation.model_dump(mode="json")
