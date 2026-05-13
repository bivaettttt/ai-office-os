from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.tools.approvals import (
    build_approval_detail,
    list_approval_details,
)
from app.core.tools.executor import ToolExecutor
from app.core.tools.permissions import PermissionScopeType
from app.core.world import world


router = APIRouter()


class ApprovalRequest(BaseModel):
    approved_by: str = "user"
    create_grant: bool = False
    grant_scope_type: PermissionScopeType | None = None
    grant_scope_id: str | None = None
    grant_expires_in_minutes: int | None = None


class RejectionRequest(BaseModel):
    rejected_by: str = "user"


@router.get("/approvals")
def list_approvals():
    return {
        "items": list_approval_details(world),
        "total": len(
            [
                invocation
                for invocation in world.tool_invocations.values()
                if invocation.status == "awaiting_approval"
            ]
        ),
    }


@router.get("/approvals/{invocation_id}")
def get_approval(invocation_id: str):
    invocation = world.tool_invocations.get(invocation_id)
    if invocation is None:
        raise HTTPException(
            status_code=404,
            detail="Approval not found.",
        )
    return build_approval_detail(
        world,
        invocation,
        record_opened=True,
    )


@router.post("/approvals/{invocation_id}/approve")
def approve(invocation_id: str, request: ApprovalRequest):
    invocation = ToolExecutor(world).approve(
        invocation_id,
        approved_by=request.approved_by,
        create_grant=request.create_grant,
        grant_expires_in_minutes=(
            request.grant_expires_in_minutes
        ),
        grant_scope_type=request.grant_scope_type,
        grant_scope_id=request.grant_scope_id,
    )

    if invocation is None:
        raise HTTPException(
            status_code=404,
            detail="Approval not found.",
        )

    return build_approval_detail(world, invocation)


@router.post("/approvals/{invocation_id}/reject")
def reject(invocation_id: str, request: RejectionRequest):
    invocation = ToolExecutor(world).reject(
        invocation_id,
        rejected_by=request.rejected_by,
    )

    if invocation is None:
        raise HTTPException(
            status_code=404,
            detail="Approval not found.",
        )

    return build_approval_detail(world, invocation)
