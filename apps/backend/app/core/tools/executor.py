from __future__ import annotations

import time
from typing import Any

from app.core.tools.audit import record_tool_audit
from app.core.tools.permissions import (
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
    ) -> ToolInvocation:
        tool = self.registry.get(tool_id)
        invocation = ToolInvocation(
            tool_id=tool_id,
            task_id=task_id,
            agent_id=agent_id,
            requested_by=requested_by,
            arguments=arguments or {},
        )
        self.world.add_tool_invocation(invocation)

        if tool is None:
            invocation.status = ToolInvocationStatus.BLOCKED
            invocation.error = "Unknown tool id."
            invocation.completed_at = time.time()
            invocation.policy_decision = self.policy.evaluate(None)
            self.world.add_tool_invocation(invocation)
            return invocation

        record_tool_audit(
            self.world,
            invocation,
            tool,
            ToolAuditAction.REQUESTED,
            "Tool invocation requested.",
        )

        decision = self.policy.evaluate(tool)
        invocation.policy_decision = decision

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
            return invocation

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
