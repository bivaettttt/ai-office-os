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
}


def record_tool_audit(
    world: World,
    invocation: ToolInvocation,
    tool: ToolDefinition,
    action: ToolAuditAction,
    message: str,
    decision: PolicyDecisionValue | None = None,
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
        },
    )

    return entry
