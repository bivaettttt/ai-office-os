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


def validate_permissions(
    values: list[str | Permission],
) -> list[Permission]:
    return [Permission(value) for value in values]
