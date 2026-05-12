from __future__ import annotations

from app.core.tools.permissions import (
    Permission,
    PolicyDecision,
    PolicyDecisionValue,
    RiskLevel,
    ToolDefinition,
)


DEFAULT_FORBIDDEN_PERMISSIONS = {
    Permission.WRITE_PROJECT_FILES,
    Permission.RUN_SHELL_COMMAND,
    Permission.ACCESS_NETWORK,
    Permission.ACCESS_BROWSER,
    Permission.ACCESS_CALENDAR,
    Permission.ACCESS_MESSAGING,
    Permission.ACCESS_SECRETS,
    Permission.MODIFY_SYSTEM,
}


class ExecutionPolicy:
    def __init__(
        self,
        forbidden_permissions: set[Permission] | None = None,
    ):
        self.forbidden_permissions = (
            forbidden_permissions
            if forbidden_permissions is not None
            else DEFAULT_FORBIDDEN_PERMISSIONS
        )

    def evaluate(
        self,
        tool: ToolDefinition | None,
    ) -> PolicyDecision:
        if tool is None:
            return PolicyDecision(
                decision=PolicyDecisionValue.BLOCKED,
                reason="Unknown tool id.",
            )

        if not tool.enabled:
            return PolicyDecision(
                decision=PolicyDecisionValue.BLOCKED,
                reason="Tool is disabled.",
            )

        blocked_permissions = [
            permission
            for permission in tool.required_permissions
            if permission in self.forbidden_permissions
        ]

        if blocked_permissions:
            return PolicyDecision(
                decision=PolicyDecisionValue.BLOCKED,
                reason=(
                    "Blocked by forbidden permissions: "
                    + ", ".join(blocked_permissions)
                ),
            )

        if tool.risk_level in {
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        }:
            return PolicyDecision(
                decision=PolicyDecisionValue.REQUIRES_APPROVAL,
                reason=(
                    f"{tool.risk_level} risk tools always require approval."
                ),
            )

        if (
            tool.risk_level == RiskLevel.MEDIUM
            or tool.requires_approval
        ):
            return PolicyDecision(
                decision=PolicyDecisionValue.REQUIRES_APPROVAL,
                reason="Tool requires approval before execution.",
            )

        return PolicyDecision(
            decision=PolicyDecisionValue.ALLOWED,
            reason="Low risk tool allowed by current policy.",
        )
