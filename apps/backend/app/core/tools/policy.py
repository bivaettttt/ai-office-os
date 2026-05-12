from __future__ import annotations

from app.core.tools.permissions import (
    Permission,
    PermissionGrant,
    PermissionScopeType,
    PolicyDecision,
    PolicyDecisionValue,
    PolicyProfile,
    RiskLevel,
    ToolDefinition,
)
from app.config.settings import settings


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
        profile: PolicyProfile | str | None = None,
    ):
        self.forbidden_permissions = (
            forbidden_permissions
            if forbidden_permissions is not None
            else DEFAULT_FORBIDDEN_PERMISSIONS
        )
        self.profile = PolicyProfile(
            profile or settings.TOOL_POLICY_PROFILE
        )

    def evaluate(
        self,
        tool: ToolDefinition | None,
        grants: list[PermissionGrant] | None = None,
        agent_id: str | None = None,
        task_id: str | None = None,
        department: str | None = None,
    ) -> PolicyDecision:
        if tool is None:
            return PolicyDecision(
                decision=PolicyDecisionValue.BLOCKED,
                reason="Unknown tool id.",
                profile=self.profile,
            )

        if not tool.enabled:
            return PolicyDecision(
                decision=PolicyDecisionValue.BLOCKED,
                reason="Tool is disabled.",
                profile=self.profile,
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
                profile=self.profile,
            )

        matching_grants = matching_permission_grants(
            tool=tool,
            grants=grants or [],
            agent_id=agent_id,
            task_id=task_id,
            department=department,
        )
        missing_permissions = [
            permission
            for permission in tool.required_permissions
            if permission not in matching_grants
        ]
        used_grant_ids = sorted(
            {
                grant.id
                for grants_for_permission in matching_grants.values()
                for grant in grants_for_permission
            }
        )

        if (
            missing_permissions
            and self.profile == PolicyProfile.AUTONOMOUS_SAFE
        ):
            return PolicyDecision(
                decision=PolicyDecisionValue.REQUIRES_APPROVAL,
                reason=(
                    "Scoped permission missing for profile "
                    f"{self.profile}: "
                    + ", ".join(missing_permissions)
                ),
                profile=self.profile,
            )

        if self.profile == PolicyProfile.LOCKED_DOWN:
            if tool.risk_level in {
                RiskLevel.HIGH,
                RiskLevel.CRITICAL,
            }:
                return PolicyDecision(
                    decision=PolicyDecisionValue.BLOCKED,
                    reason=(
                        "locked_down blocks high and critical risk tools."
                    ),
                    profile=self.profile,
                )
            return PolicyDecision(
                decision=PolicyDecisionValue.REQUIRES_APPROVAL,
                reason="locked_down requires approval for every tool.",
                used_grant_ids=used_grant_ids,
                profile=self.profile,
            )

        if self.profile == PolicyProfile.SAFE_LOCAL:
            if tool.risk_level in {
                RiskLevel.HIGH,
                RiskLevel.CRITICAL,
            }:
                return PolicyDecision(
                    decision=PolicyDecisionValue.BLOCKED,
                    reason=(
                        "safe_local blocks high and critical risk tools."
                    ),
                    profile=self.profile,
                )
            if tool.risk_level == RiskLevel.MEDIUM or tool.requires_approval:
                return PolicyDecision(
                    decision=PolicyDecisionValue.REQUIRES_APPROVAL,
                    reason="safe_local requires approval for medium risk tools.",
                    used_grant_ids=used_grant_ids,
                    profile=self.profile,
                )

        if self.profile == PolicyProfile.ASSISTED:
            if tool.risk_level == RiskLevel.CRITICAL:
                return PolicyDecision(
                    decision=PolicyDecisionValue.BLOCKED,
                    reason="assisted blocks critical risk tools.",
                    profile=self.profile,
                )
            if tool.risk_level in {
                RiskLevel.MEDIUM,
                RiskLevel.HIGH,
            } or tool.requires_approval:
                return PolicyDecision(
                    decision=PolicyDecisionValue.REQUIRES_APPROVAL,
                    reason=(
                        "assisted requires approval for medium/high risk tools."
                    ),
                    used_grant_ids=used_grant_ids,
                    profile=self.profile,
                )

        if self.profile == PolicyProfile.AUTONOMOUS_SAFE:
            if tool.risk_level == RiskLevel.CRITICAL:
                return PolicyDecision(
                    decision=PolicyDecisionValue.BLOCKED,
                    reason="autonomous_safe blocks critical risk tools.",
                    profile=self.profile,
                )
            if tool.risk_level == RiskLevel.HIGH:
                return PolicyDecision(
                    decision=PolicyDecisionValue.REQUIRES_APPROVAL,
                    reason="autonomous_safe requires approval for high risk tools.",
                    used_grant_ids=used_grant_ids,
                    profile=self.profile,
                )
            return PolicyDecision(
                decision=PolicyDecisionValue.ALLOWED,
                reason="Allowed by active scoped permission grant.",
                used_grant_ids=used_grant_ids,
                profile=self.profile,
            )

        if tool.risk_level == RiskLevel.MEDIUM or tool.requires_approval:
            return PolicyDecision(
                decision=PolicyDecisionValue.REQUIRES_APPROVAL,
                reason="Tool requires approval before execution.",
                used_grant_ids=used_grant_ids,
                profile=self.profile,
            )

        return PolicyDecision(
            decision=PolicyDecisionValue.ALLOWED,
            reason="Low risk tool allowed by current policy.",
            used_grant_ids=used_grant_ids,
            profile=self.profile,
        )


RISK_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}


def matching_permission_grants(
    tool: ToolDefinition,
    grants: list[PermissionGrant],
    agent_id: str | None = None,
    task_id: str | None = None,
    department: str | None = None,
) -> dict[Permission, list[PermissionGrant]]:
    matched: dict[Permission, list[PermissionGrant]] = {}

    for permission in tool.required_permissions:
        for grant in grants:
            if not grant.is_active():
                continue
            if grant.permission != permission:
                continue
            if grant.tool_id and grant.tool_id != tool.id:
                continue
            if (
                grant.risk_level_max
                and RISK_ORDER[tool.risk_level]
                > RISK_ORDER[grant.risk_level_max]
            ):
                continue
            if not scope_matches(
                grant,
                agent_id=agent_id,
                task_id=task_id,
                department=department,
            ):
                continue

            matched.setdefault(permission, []).append(grant)

    return matched


def scope_matches(
    grant: PermissionGrant,
    agent_id: str | None = None,
    task_id: str | None = None,
    department: str | None = None,
) -> bool:
    if grant.scope_type == PermissionScopeType.GLOBAL:
        return True
    if grant.scope_type == PermissionScopeType.AGENT:
        return grant.scope_id == agent_id
    if grant.scope_type == PermissionScopeType.TASK:
        return grant.scope_id == task_id
    if grant.scope_type == PermissionScopeType.DEPARTMENT:
        return grant.scope_id == department
    return False
