from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.tools.executor import ToolExecutor
from app.core.tools.approvals import build_approval_detail
from app.core.tools.permissions import (
    Permission,
    PermissionGrant,
    PermissionScopeType,
    RiskLevel,
    ToolAuditAction,
    ToolAuditEntry,
)
from app.core.tools.registry import tool_registry
from app.config.settings import settings
from app.core.world import world


router = APIRouter()


class ToolInvokeRequest(BaseModel):
    tool_id: str
    task_id: str | None = None
    agent_id: str | None = None
    department: str | None = None
    requested_by: str = "user"
    arguments: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False


class ToolApprovalRequest(BaseModel):
    approved_by: str = "user"
    create_grant: bool = False
    grant_expires_in_minutes: int | None = None


class ToolRejectRequest(BaseModel):
    rejected_by: str = "user"


class PermissionGrantRequest(BaseModel):
    scope_type: PermissionScopeType
    scope_id: str | None = None
    permission: Permission
    tool_id: str | None = None
    risk_level_max: RiskLevel | None = None
    expires_in_minutes: int | None = None
    granted_by: str = "user"
    reason: str = ""


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
        department=request.department,
        requested_by=request.requested_by,
        arguments=request.arguments,
        dry_run=request.dry_run,
    )
    return invocation.model_dump(mode="json")


@router.get("/tools/invocations/{invocation_id}/audit")
def tool_invocation_audit(invocation_id: str):
    invocation = world.tool_invocations.get(invocation_id)
    if invocation is None:
        raise HTTPException(
            status_code=404,
            detail="Tool invocation not found.",
        )
    return build_approval_detail(world, invocation)


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
        create_grant=(
            request.create_grant
            if request
            else False
        ),
        grant_expires_in_minutes=(
            request.grant_expires_in_minutes
            if request
            else None
        ),
    )

    if invocation is None:
        raise HTTPException(
            status_code=404,
            detail="Tool invocation not found.",
        )

    return invocation.model_dump(mode="json")


@router.get("/tools/grants")
def list_permission_grants():
    return {
        "policy_profile": settings.TOOL_POLICY_PROFILE,
        "grants": [
            grant.model_dump(mode="json")
            for grant in sorted(
                world.permission_grants.values(),
                key=lambda item: item.created_at,
                reverse=True,
            )
        ],
    }


@router.post("/tools/grants")
def create_permission_grant(
    request: PermissionGrantRequest,
):
    expires_at = (
        time.time() + request.expires_in_minutes * 60
        if request.expires_in_minutes
        else None
    )
    grant = PermissionGrant(
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        permission=request.permission,
        tool_id=request.tool_id,
        risk_level_max=request.risk_level_max,
        granted_by=request.granted_by,
        reason=request.reason,
        expires_at=expires_at,
    )
    world.add_permission_grant(grant)
    world.add_tool_audit(
        ToolAuditEntry(
            invocation_id=grant.id,
            tool_id=grant.tool_id or "permission_grant",
            action=ToolAuditAction.GRANT_CREATED,
            message=grant.reason or "Permission grant created.",
            risk_level=grant.risk_level_max or RiskLevel.LOW,
            permissions=[grant.permission],
            profile=settings.TOOL_POLICY_PROFILE,
            grant_ids=[grant.id],
            scope={
                "scope_type": grant.scope_type.value,
                "scope_id": grant.scope_id,
            },
            reason=grant.reason,
        )
    )
    world.add_event(
        "grant_created",
        {
            "grant_id": grant.id,
            "scope_type": grant.scope_type.value,
            "scope_id": grant.scope_id,
            "permission": grant.permission.value,
            "tool_id": grant.tool_id,
            "profile": settings.TOOL_POLICY_PROFILE,
        },
    )
    return grant.model_dump(mode="json")


@router.post("/tools/grants/{grant_id}/revoke")
def revoke_permission_grant(
    grant_id: str,
):
    grant = world.permission_grants.get(grant_id)
    if grant is None:
        raise HTTPException(
            status_code=404,
            detail="Permission grant not found.",
        )

    grant.active = False
    grant.revoked_at = time.time()
    world.add_permission_grant(grant)
    world.add_tool_audit(
        ToolAuditEntry(
            invocation_id=grant.id,
            tool_id=grant.tool_id or "permission_grant",
            action=ToolAuditAction.GRANT_REVOKED,
            message="Permission grant revoked.",
            risk_level=grant.risk_level_max or RiskLevel.LOW,
            permissions=[grant.permission],
            profile=settings.TOOL_POLICY_PROFILE,
            grant_ids=[grant.id],
            scope={
                "scope_type": grant.scope_type.value,
                "scope_id": grant.scope_id,
            },
            reason="Permission grant revoked.",
        )
    )
    world.add_event(
        "grant_revoked",
        {
            "grant_id": grant.id,
            "scope_type": grant.scope_type.value,
            "scope_id": grant.scope_id,
            "permission": grant.permission.value,
            "tool_id": grant.tool_id,
            "profile": settings.TOOL_POLICY_PROFILE,
        },
    )
    return grant.model_dump(mode="json")


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
