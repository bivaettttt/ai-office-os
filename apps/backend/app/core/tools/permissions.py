from __future__ import annotations

import time
import uuid

from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolCategory(StrEnum):
    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    BROWSER = "browser"
    NETWORK = "network"
    CALENDAR = "calendar"
    MESSAGING = "messaging"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    SYSTEM = "system"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyProfile(StrEnum):
    LOCKED_DOWN = "locked_down"
    SAFE_LOCAL = "safe_local"
    ASSISTED = "assisted"
    AUTONOMOUS_SAFE = "autonomous_safe"


class PermissionScopeType(StrEnum):
    AGENT = "agent"
    DEPARTMENT = "department"
    TASK = "task"
    GLOBAL = "global"


class Permission(StrEnum):
    READ_PROJECT_FILES = "read_project_files"
    WRITE_PROJECT_FILES = "write_project_files"
    RUN_TESTS = "run_tests"
    RUN_SHELL_COMMAND = "run_shell_command"
    ACCESS_NETWORK = "access_network"
    ACCESS_BROWSER = "access_browser"
    ACCESS_CALENDAR = "access_calendar"
    ACCESS_MESSAGING = "access_messaging"
    ACCESS_SECRETS = "access_secrets"
    MODIFY_SYSTEM = "modify_system"
    CREATE_REPORT = "create_report"
    GENERATE_CONTENT = "generate_content"


class PolicyDecisionValue(StrEnum):
    ALLOWED = "allowed"
    REQUIRES_APPROVAL = "requires_approval"
    BLOCKED = "blocked"


class ToolInvocationStatus(StrEnum):
    REQUESTED = "requested"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ToolAuditAction(StrEnum):
    REQUESTED = "requested"
    POLICY_ALLOWED = "policy_allowed"
    POLICY_REQUIRES_APPROVAL = "policy_requires_approval"
    POLICY_BLOCKED = "policy_blocked"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    GRANT_CREATED = "grant_created"
    GRANT_REVOKED = "grant_revoked"
    GRANT_EXPIRED = "grant_expired"
    POLICY_PROFILE_APPLIED = "policy_profile_applied"
    SCOPED_PERMISSION_ALLOWED = "scoped_permission_allowed"
    SCOPED_PERMISSION_MISSING = "scoped_permission_missing"


class ToolDefinition(BaseModel):
    id: str
    name: str
    description: str
    category: ToolCategory
    required_capabilities: list[str] = Field(default_factory=list)
    required_permissions: list[Permission] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    enabled: bool = True
    requires_approval: bool = False


class PolicyDecision(BaseModel):
    decision: PolicyDecisionValue
    reason: str
    used_grant_ids: list[str] = Field(default_factory=list)
    profile: PolicyProfile = PolicyProfile.SAFE_LOCAL


class ToolInvocation(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    tool_id: str
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    requested_by: str = "user"
    arguments: dict[str, Any] = Field(default_factory=dict)
    status: ToolInvocationStatus = (
        ToolInvocationStatus.REQUESTED
    )
    policy_decision: Optional[PolicyDecision] = None
    approval_required: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[float] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    policy_profile: PolicyProfile = PolicyProfile.SAFE_LOCAL
    used_grant_ids: list[str] = Field(default_factory=list)
    approval_expires_at: Optional[float] = None
    department: Optional[str] = None


class ToolAuditEntry(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    timestamp: float = Field(default_factory=time.time)
    invocation_id: str
    tool_id: str
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    action: ToolAuditAction
    decision: Optional[PolicyDecisionValue] = None
    message: str
    risk_level: RiskLevel
    permissions: list[Permission] = Field(default_factory=list)
    profile: Optional[PolicyProfile] = None
    grant_ids: list[str] = Field(default_factory=list)
    scope: Optional[dict[str, Any]] = None
    reason: Optional[str] = None


class PermissionGrant(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    scope_type: PermissionScopeType
    scope_id: Optional[str] = None
    permission: Permission
    tool_id: Optional[str] = None
    risk_level_max: Optional[RiskLevel] = None
    granted_by: str = "user"
    reason: str = ""
    expires_at: Optional[float] = None
    created_at: float = Field(default_factory=time.time)
    revoked_at: Optional[float] = None
    active: bool = True

    def is_active(
        self,
        now: float | None = None,
    ) -> bool:
        current_time = now or time.time()
        return (
            self.active
            and self.revoked_at is None
            and (
                self.expires_at is None
                or self.expires_at > current_time
            )
        )


def validate_permissions(
    values: list[str | Permission],
) -> list[Permission]:
    return [Permission(value) for value in values]
