from __future__ import annotations

from app.config.settings import settings
from app.core.runtime_timeline import build_runtime_timeline
from app.core.tools.audit import record_tool_audit
from app.core.tools.permissions import (
    PermissionScopeType,
    RiskLevel,
    ToolAuditAction,
    ToolInvocation,
)
from app.core.tools.registry import tool_registry
from app.core.world import World


PROFILE_DESCRIPTIONS = {
    "locked_down": (
        "Every tool requires approval; high and critical tools are blocked."
    ),
    "safe_local": (
        "Low risk tools can run; medium requires approval; high and "
        "critical tools are blocked."
    ),
    "assisted": (
        "Low risk tools can run; medium/high require approval; "
        "critical tools are blocked."
    ),
    "autonomous_safe": (
        "Low/medium tools can run only with matching active grants; "
        "high requires approval; critical tools are blocked."
    ),
}


def list_approval_details(world: World) -> list[dict]:
    return [
        build_approval_detail(world, invocation)
        for invocation in sorted(
            world.tool_invocations.values(),
            key=lambda item: item.created_at,
            reverse=True,
        )
        if invocation.status == "awaiting_approval"
    ]


def build_approval_detail(
    world: World,
    invocation: ToolInvocation,
    record_opened: bool = False,
) -> dict:
    tool = tool_registry.get(invocation.tool_id)
    audit_entries = [
        entry
        for entry in world.tool_audit_log
        if entry.invocation_id == invocation.id
    ]
    grants_used = [
        world.permission_grants[grant_id].model_dump(mode="json")
        for grant_id in invocation.used_grant_ids
        if grant_id in world.permission_grants
    ]
    related_task = (
        world.tasks.get(invocation.task_id)
        if invocation.task_id
        else None
    )
    related_agent = (
        world.agents.get(invocation.agent_id)
        if invocation.agent_id
        else None
    )
    related_department = invocation.department or (
        related_task.department
        if related_task
        else (
            related_agent.department
            if related_agent
            else None
        )
    )

    suggestions = (
        suggested_approval_scopes(invocation, tool)
        if tool
        else []
    )

    if record_opened and tool:
        record_tool_audit(
            world,
            invocation,
            tool,
            ToolAuditAction.APPROVAL_OPENED,
            "Approval detail opened.",
            invocation.policy_decision.decision
            if invocation.policy_decision
            else None,
        )
        if suggestions:
            record_tool_audit(
                world,
                invocation,
                tool,
                ToolAuditAction.APPROVAL_SCOPE_SUGGESTED,
                "Approval scopes suggested.",
                invocation.policy_decision.decision
                if invocation.policy_decision
                else None,
            )

    timeline = [
        entry
        for entry in build_runtime_timeline(
            world,
            limit=500,
        )["entries"]
        if entry.get("metadata", {}).get("invocation_id")
        == invocation.id
    ]

    return {
        "invocation": invocation.model_dump(mode="json"),
        "tool": tool.model_dump(mode="json") if tool else None,
        "policy_decision": (
            invocation.policy_decision.model_dump(mode="json")
            if invocation.policy_decision
            else None
        ),
        "required_permissions": (
            [
                permission.value
                for permission in tool.required_permissions
            ]
            if tool
            else []
        ),
        "risk_level": tool.risk_level if tool else None,
        "related_task": (
            related_task.model_dump(mode="json")
            if related_task
            else None
        ),
        "related_agent": (
            related_agent.model_dump(mode="json")
            if related_agent
            else None
        ),
        "related_department": related_department,
        "audit_trail": [
            entry.model_dump(mode="json")
            for entry in audit_entries
        ],
        "suggested_approval_scopes": suggestions,
        "grants_used": grants_used,
        "policy_profile": invocation.policy_profile,
        "policy_profile_description": PROFILE_DESCRIPTIONS.get(
            settings.TOOL_POLICY_PROFILE,
            "",
        ),
        "sandbox_contract": (
            world.sandbox_contracts[
                invocation.sandbox_contract_id
            ].model_dump(mode="json")
            if invocation.sandbox_contract_id
            and invocation.sandbox_contract_id
            in world.sandbox_contracts
            else None
        ),
        "timeline": timeline,
    }


def suggested_approval_scopes(
    invocation: ToolInvocation,
    tool,
) -> list[dict]:
    if tool.risk_level == RiskLevel.CRITICAL:
        return []

    permissions = [
        permission.value
        for permission in tool.required_permissions
    ]
    once = {
        "scope_type": "once",
        "scope_id": invocation.id,
        "permissions": permissions,
        "tool_id": tool.id,
        "recommended_duration_minutes": 0,
        "risk_warning": "Approves this invocation only.",
    }

    if tool.risk_level == RiskLevel.HIGH:
        return [once]

    if tool.risk_level == RiskLevel.MEDIUM:
        return [
            once,
            {
                "scope_type": PermissionScopeType.TASK.value,
                "scope_id": invocation.task_id,
                "permissions": permissions,
                "tool_id": tool.id,
                "recommended_duration_minutes": 30,
                "risk_warning": (
                    "Medium risk: prefer a short task-scoped grant."
                ),
            },
        ]

    suggestions = [once]
    if invocation.task_id:
        suggestions.append(
            {
                "scope_type": PermissionScopeType.TASK.value,
                "scope_id": invocation.task_id,
                "permissions": permissions,
                "tool_id": tool.id,
                "recommended_duration_minutes": 60,
                "risk_warning": "Low risk task-scoped grant.",
            }
        )
    if invocation.agent_id:
        suggestions.append(
            {
                "scope_type": PermissionScopeType.AGENT.value,
                "scope_id": invocation.agent_id,
                "permissions": permissions,
                "tool_id": tool.id,
                "recommended_duration_minutes": 60,
                "risk_warning": "Low risk agent-scoped grant.",
            }
        )
    if invocation.department:
        suggestions.append(
            {
                "scope_type": PermissionScopeType.DEPARTMENT.value,
                "scope_id": invocation.department,
                "permissions": permissions,
                "tool_id": tool.id,
                "recommended_duration_minutes": 60,
                "risk_warning": "Low risk department-scoped grant.",
            }
        )
    suggestions.append(
        {
            "scope_type": PermissionScopeType.GLOBAL.value,
            "scope_id": None,
            "permissions": permissions,
            "tool_id": tool.id,
            "recommended_duration_minutes": 15,
            "risk_warning": (
                "Global grants are broad; keep duration short."
            ),
        }
    )
    return suggestions
