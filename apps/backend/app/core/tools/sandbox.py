from __future__ import annotations

import time
import uuid

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.tools.permissions import (
    ToolCategory,
    ToolDefinition,
)


class SandboxContract(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    tool_id: str
    category: ToolCategory
    allowed_operations: list[str] = Field(default_factory=list)
    denied_operations: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    filesystem_scope: Optional[dict[str, Any]] = None
    network_scope: Optional[dict[str, Any]] = None
    timeout_seconds: int = 30
    max_output_size: int = 8192
    requires_dry_run: bool = False
    created_at: float = Field(default_factory=time.time)


class ToolExecutionRequest(BaseModel):
    invocation_id: str
    tool_id: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    sandbox_contract_id: str
    dry_run: bool = True
    agent_id: Optional[str] = None
    task_id: Optional[str] = None


class ToolExecutionResult(BaseModel):
    invocation_id: str
    status: str
    output: dict[str, Any] | None = None
    error: Optional[str] = None
    dry_run: bool = True
    side_effects_declared: list[str] = Field(default_factory=list)
    side_effects_performed: list[str] = Field(default_factory=list)
    started_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None


def build_sandbox_contract(
    tool: ToolDefinition,
) -> SandboxContract:
    common = {
        "tool_id": tool.id,
        "category": tool.category,
        "required_permissions": [
            permission.value
            for permission in tool.required_permissions
        ],
    }

    if tool.category == ToolCategory.FILESYSTEM:
        return SandboxContract(
            **common,
            allowed_operations=["read_metadata_stub"],
            denied_operations=["write_file", "delete_file", "read_real_file"],
            filesystem_scope={
                "mode": "placeholder_read_only",
                "paths": ["<project-root>"],
            },
            requires_dry_run=False,
        )

    if tool.category == ToolCategory.TERMINAL:
        return SandboxContract(
            **common,
            allowed_operations=["dry_run_plan"],
            denied_operations=["run_command", "spawn_process"],
            requires_dry_run=True,
            timeout_seconds=10,
        )

    if tool.category in {
        ToolCategory.BROWSER,
        ToolCategory.NETWORK,
    }:
        return SandboxContract(
            **common,
            allowed_operations=["dry_run_plan"],
            denied_operations=["http_request", "browser_navigation"],
            network_scope={
                "mode": "denied",
            },
            requires_dry_run=True,
            timeout_seconds=10,
        )

    if tool.category in {
        ToolCategory.GENERATION,
        ToolCategory.ANALYSIS,
    }:
        return SandboxContract(
            **common,
            allowed_operations=["safe_stub_execution"],
            denied_operations=["external_api_call", "file_write"],
            requires_dry_run=False,
        )

    return SandboxContract(
        **common,
        allowed_operations=["dry_run_plan"],
        denied_operations=["real_side_effects"],
        requires_dry_run=True,
    )


def build_dry_run_result(
    invocation_id: str,
    tool: ToolDefinition,
    contract: SandboxContract,
    arguments: dict[str, Any],
) -> ToolExecutionResult:
    started_at = time.time()
    return ToolExecutionResult(
        invocation_id=invocation_id,
        status="dry_run_completed",
        output={
            "what_would_run": (
                f"{tool.id} would execute under sandbox contract "
                f"{contract.id}."
            ),
            "arguments": arguments,
            "required_permissions": contract.required_permissions,
            "expected_side_effects": [],
            "risk_warnings": risk_warnings_for(tool, contract),
        },
        dry_run=True,
        side_effects_declared=[],
        side_effects_performed=[],
        started_at=started_at,
        completed_at=time.time(),
    )


def risk_warnings_for(
    tool: ToolDefinition,
    contract: SandboxContract,
) -> list[str]:
    warnings = [
        f"Tool risk level: {tool.risk_level.value}.",
    ]
    if contract.requires_dry_run:
        warnings.append(
            "Sandbox contract requires dry-run only execution."
        )
    if contract.denied_operations:
        warnings.append(
            "Denied operations: "
            + ", ".join(contract.denied_operations)
        )
    return warnings
