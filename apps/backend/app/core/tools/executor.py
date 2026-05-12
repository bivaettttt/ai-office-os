from __future__ import annotations

import time
from typing import Any

from app.core.tools.audit import record_tool_audit
from app.core.tools.permissions import (
    PermissionGrant,
    PermissionScopeType,
    PolicyDecisionValue,
    ToolAuditAction,
    ToolInvocation,
    ToolInvocationStatus,
)
from app.core.tools.policy import ExecutionPolicy
from app.core.tools.registry import ToolRegistry, tool_registry
from app.core.tools.stubs import STUB_TOOL_HANDLERS
from app.core.world import World


class ToolExecutor:
    def __init__(
        self,
        world: World,
        registry: ToolRegistry | None = None,
        policy: ExecutionPolicy | None = None,
    ):
        self.world = world
        self.registry = registry or tool_registry
        self.policy = policy or ExecutionPolicy()

    def invoke(
        self,
        tool_id: str,
        requested_by: str = "user",
        arguments: dict[str, Any] | None = None,
        task_id: str | None = None,
        agent_id: str | None = None,
        department: str | None = None,
    ) -> ToolInvocation:
        tool = self.registry.get(tool_id)
        resolved_department = department or self._department_for(
            agent_id=agent_id,
            task_id=task_id,
        )
        invocation = ToolInvocation(
            tool_id=tool_id,
            task_id=task_id,
            agent_id=agent_id,
            department=resolved_department,
            requested_by=requested_by,
            arguments=arguments or {},
        )
        self.world.add_tool_invocation(invocation)

        if tool is None:
            invocation.status = ToolInvocationStatus.BLOCKED
            invocation.error = "Unknown tool id."
            invocation.completed_at = time.time()
            invocation.policy_decision = self.policy.evaluate(None)
            invocation.policy_profile = (
                invocation.policy_decision.profile
            )
            self.world.add_tool_invocation(invocation)
            return invocation

        record_tool_audit(
            self.world,
            invocation,
            tool,
            ToolAuditAction.REQUESTED,
            "Tool invocation requested.",
        )

        decision = self.policy.evaluate(
            tool,
            grants=list(self.world.permission_grants.values()),
            agent_id=agent_id,
            task_id=task_id,
            department=resolved_department,
        )
        invocation.policy_decision = decision
        invocation.policy_profile = decision.profile
        invocation.used_grant_ids = decision.used_grant_ids
        self.world.add_tool_invocation(invocation)
        record_tool_audit(
            self.world,
            invocation,
            tool,
            ToolAuditAction.POLICY_PROFILE_APPLIED,
            f"Policy profile applied: {decision.profile}.",
            decision.decision,
        )

        if decision.decision == PolicyDecisionValue.BLOCKED:
            invocation.status = ToolInvocationStatus.BLOCKED
            invocation.error = decision.reason
            invocation.completed_at = time.time()
            self.world.add_tool_invocation(invocation)
            record_tool_audit(
                self.world,
                invocation,
                tool,
                ToolAuditAction.POLICY_BLOCKED,
                decision.reason,
                decision.decision,
            )
            return invocation

        if decision.decision == PolicyDecisionValue.REQUIRES_APPROVAL:
            invocation.status = (
                ToolInvocationStatus.AWAITING_APPROVAL
            )
            invocation.approval_required = True
            self.world.add_tool_invocation(invocation)
            record_tool_audit(
                self.world,
                invocation,
                tool,
                ToolAuditAction.POLICY_REQUIRES_APPROVAL,
                decision.reason,
                decision.decision,
            )
            if "Scoped permission missing" in decision.reason:
                record_tool_audit(
                    self.world,
                    invocation,
                    tool,
                    ToolAuditAction.SCOPED_PERMISSION_MISSING,
                    decision.reason,
                    decision.decision,
                )
            return invocation

        if invocation.used_grant_ids:
            record_tool_audit(
                self.world,
                invocation,
                tool,
                ToolAuditAction.SCOPED_PERMISSION_ALLOWED,
                "Invocation allowed by active scoped grants.",
                decision.decision,
                grant_ids=invocation.used_grant_ids,
            )

        record_tool_audit(
            self.world,
            invocation,
            tool,
            ToolAuditAction.POLICY_ALLOWED,
            decision.reason,
            decision.decision,
        )
        return self._execute(invocation)

    def approve(
        self,
        invocation_id: str,
        approved_by: str = "user",
        create_grant: bool = False,
        grant_expires_in_minutes: int | None = None,
    ) -> ToolInvocation | None:
        invocation = self.world.tool_invocations.get(invocation_id)
        if invocation is None:
            return None

        tool = self.registry.get(invocation.tool_id)
        if tool is None:
            invocation.status = ToolInvocationStatus.BLOCKED
            invocation.error = "Unknown tool id."
            invocation.completed_at = time.time()
            self.world.add_tool_invocation(invocation)
            return invocation

        if invocation.status != ToolInvocationStatus.AWAITING_APPROVAL:
            return invocation

        invocation.status = ToolInvocationStatus.APPROVED
        invocation.approved_by = approved_by
        invocation.approved_at = time.time()
        if grant_expires_in_minutes:
            invocation.approval_expires_at = (
                time.time() + grant_expires_in_minutes * 60
            )
        self.world.add_tool_invocation(invocation)
        record_tool_audit(
            self.world,
            invocation,
            tool,
            ToolAuditAction.APPROVED,
            "Tool invocation approved.",
            invocation.policy_decision.decision
            if invocation.policy_decision
            else None,
        )
        if create_grant:
            created_grants = self.create_grants_for_invocation(
                invocation,
                tool,
                granted_by=approved_by,
                expires_in_minutes=grant_expires_in_minutes,
            )
            invocation.used_grant_ids = [
                grant.id
                for grant in created_grants
            ]
            self.world.add_tool_invocation(invocation)
        return self._execute(invocation)

    def reject(
        self,
        invocation_id: str,
        rejected_by: str = "user",
    ) -> ToolInvocation | None:
        invocation = self.world.tool_invocations.get(invocation_id)
        if invocation is None:
            return None

        tool = self.registry.get(invocation.tool_id)
        if tool is None:
            invocation.status = ToolInvocationStatus.BLOCKED
            invocation.error = "Unknown tool id."
            invocation.completed_at = time.time()
            self.world.add_tool_invocation(invocation)
            return invocation

        invocation.status = ToolInvocationStatus.CANCELLED
        invocation.error = f"Rejected by {rejected_by}."
        invocation.completed_at = time.time()
        self.world.add_tool_invocation(invocation)
        record_tool_audit(
            self.world,
            invocation,
            tool,
            ToolAuditAction.REJECTED,
            invocation.error,
            invocation.policy_decision.decision
            if invocation.policy_decision
            else None,
        )
        return invocation

    def _execute(
        self,
        invocation: ToolInvocation,
    ) -> ToolInvocation:
        tool = self.registry.get(invocation.tool_id)
        if tool is None:
            invocation.status = ToolInvocationStatus.BLOCKED
            invocation.error = "Unknown tool id."
            invocation.completed_at = time.time()
            self.world.add_tool_invocation(invocation)
            return invocation

        handler = STUB_TOOL_HANDLERS.get(tool.id)
        if handler is None:
            invocation.status = ToolInvocationStatus.BLOCKED
            invocation.error = "No safe stub handler exists."
            invocation.completed_at = time.time()
            self.world.add_tool_invocation(invocation)
            record_tool_audit(
                self.world,
                invocation,
                tool,
                ToolAuditAction.POLICY_BLOCKED,
                invocation.error,
                PolicyDecisionValue.BLOCKED,
            )
            return invocation

        invocation.status = ToolInvocationStatus.RUNNING
        self.world.add_tool_invocation(invocation)

        try:
            invocation.result = handler(invocation.arguments)
            invocation.status = ToolInvocationStatus.COMPLETED
            invocation.completed_at = time.time()
            self.world.add_tool_invocation(invocation)
            record_tool_audit(
                self.world,
                invocation,
                tool,
                ToolAuditAction.EXECUTED,
                "Safe stub tool executed.",
                invocation.policy_decision.decision
                if invocation.policy_decision
                else PolicyDecisionValue.ALLOWED,
            )
        except Exception as exc:
            invocation.status = ToolInvocationStatus.FAILED
            invocation.error = str(exc)
            invocation.completed_at = time.time()
            self.world.add_tool_invocation(invocation)
            record_tool_audit(
                self.world,
                invocation,
                tool,
                ToolAuditAction.FAILED,
                str(exc),
                invocation.policy_decision.decision
                if invocation.policy_decision
                else None,
            )

        return invocation

    def create_grants_for_invocation(
        self,
        invocation: ToolInvocation,
        tool,
        granted_by: str,
        expires_in_minutes: int | None = None,
    ) -> list[PermissionGrant]:
        scope_type = PermissionScopeType.GLOBAL
        scope_id = None
        if invocation.agent_id:
            scope_type = PermissionScopeType.AGENT
            scope_id = invocation.agent_id
        elif invocation.task_id:
            scope_type = PermissionScopeType.TASK
            scope_id = invocation.task_id
        elif invocation.department:
            scope_type = PermissionScopeType.DEPARTMENT
            scope_id = invocation.department

        expires_at = (
            time.time() + expires_in_minutes * 60
            if expires_in_minutes
            else None
        )
        grants = []
        for permission in tool.required_permissions:
            grant = PermissionGrant(
                scope_type=scope_type,
                scope_id=scope_id,
                permission=permission,
                tool_id=tool.id,
                risk_level_max=tool.risk_level,
                granted_by=granted_by,
                reason=(
                    f"Created from approval for invocation {invocation.id}."
                ),
                expires_at=expires_at,
            )
            self.world.add_permission_grant(grant)
            grants.append(grant)
            record_tool_audit(
                self.world,
                invocation,
                tool,
                ToolAuditAction.GRANT_CREATED,
                grant.reason,
                invocation.policy_decision.decision
                if invocation.policy_decision
                else None,
                grant_ids=[grant.id],
                scope={
                    "scope_type": grant.scope_type.value,
                    "scope_id": grant.scope_id,
                },
            )

        return grants

    def _department_for(
        self,
        agent_id: str | None,
        task_id: str | None,
    ) -> str | None:
        if agent_id and agent_id in self.world.agents:
            return self.world.agents[agent_id].department
        if task_id and task_id in self.world.tasks:
            return self.world.tasks[task_id].department
        return None
