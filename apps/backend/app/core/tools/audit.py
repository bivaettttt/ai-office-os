from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.tools.permissions import (
    PolicyDecisionValue,
    ToolAuditAction,
    ToolAuditEntry,
    ToolDefinition,
    ToolInvocation,
)

if TYPE_CHECKING:
    from app.core.world import World


EVENT_BY_ACTION = {
    ToolAuditAction.REQUESTED: "tool_requested",
    ToolAuditAction.POLICY_ALLOWED: "tool_requested",
    ToolAuditAction.POLICY_REQUIRES_APPROVAL: (
        "tool_approval_required"
    ),
    ToolAuditAction.POLICY_BLOCKED: "tool_blocked",
    ToolAuditAction.APPROVED: "tool_approved",
    ToolAuditAction.REJECTED: "tool_rejected",
    ToolAuditAction.EXECUTED: "tool_executed",
    ToolAuditAction.FAILED: "tool_blocked",
    ToolAuditAction.GRANT_CREATED: "grant_created",
    ToolAuditAction.GRANT_REVOKED: "grant_revoked",
    ToolAuditAction.GRANT_EXPIRED: "grant_expired",
    ToolAuditAction.POLICY_PROFILE_APPLIED: "policy_profile_applied",
    ToolAuditAction.SCOPED_PERMISSION_ALLOWED: (
        "scoped_permission_allowed"
    ),
    ToolAuditAction.SCOPED_PERMISSION_MISSING: (
        "scoped_permission_missing"
    ),
    ToolAuditAction.APPROVAL_OPENED: "approval_opened",
    ToolAuditAction.APPROVAL_SCOPE_SUGGESTED: (
        "approval_scope_suggested"
    ),
    ToolAuditAction.APPROVAL_ONCE_APPROVED: (
        "approval_once_approved"
    ),
    ToolAuditAction.APPROVAL_GRANT_APPROVED: (
        "approval_grant_approved"
    ),
    ToolAuditAction.DRY_RUN_REQUESTED: "dry_run_requested",
    ToolAuditAction.DRY_RUN_COMPLETED: "dry_run_completed",
    ToolAuditAction.SANDBOX_CONTRACT_CREATED: (
        "sandbox_contract_created"
    ),
    ToolAuditAction.SANDBOX_CONTRACT_BLOCKED: (
        "sandbox_contract_blocked"
    ),
}


def record_tool_audit(
    world: World,
    invocation: ToolInvocation,
    tool: ToolDefinition,
    action: ToolAuditAction,
    message: str,
    decision: PolicyDecisionValue | None = None,
    grant_ids: list[str] | None = None,
    scope: dict | None = None,
) -> ToolAuditEntry:
    entry = ToolAuditEntry(
        invocation_id=invocation.id,
        tool_id=tool.id,
        task_id=invocation.task_id,
        agent_id=invocation.agent_id,
        action=action,
        decision=decision,
        message=message,
        risk_level=tool.risk_level,
        permissions=tool.required_permissions,
        profile=(
            invocation.policy_profile
            if invocation
            else None
        ),
        grant_ids=grant_ids or invocation.used_grant_ids,
        scope=scope
        or {
            "agent_id": invocation.agent_id,
            "task_id": invocation.task_id,
            "department": invocation.department,
        },
        reason=message,
    )

    world.add_tool_audit(entry)
    world.add_event(
        EVENT_BY_ACTION[action],
        {
            "invocation_id": invocation.id,
            "tool_id": tool.id,
            "task_id": invocation.task_id,
            "agent_id": invocation.agent_id,
            "action": action.value,
            "decision": (
                decision.value
                if decision
                else None
            ),
            "message": message,
            "risk_level": tool.risk_level.value,
            "permissions": [
                permission.value
                for permission in tool.required_permissions
            ],
            "profile": (
                invocation.policy_profile.value
                if invocation.policy_profile
                else None
            ),
            "grant_ids": grant_ids or invocation.used_grant_ids,
            "scope": scope
            or {
                "agent_id": invocation.agent_id,
                "task_id": invocation.task_id,
                "department": invocation.department,
            },
            "reason": message,
        },
    )

    return entry
