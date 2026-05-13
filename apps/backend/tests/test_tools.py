import pytest

from fastapi.testclient import TestClient

from app.core.tools.executor import ToolExecutor
from app.core.tools.approvals import suggested_approval_scopes
from app.core.tools.permissions import (
    Permission,
    PermissionGrant,
    PermissionScopeType,
    PolicyDecisionValue,
    PolicyProfile,
    RiskLevel,
    ToolAuditAction,
    ToolCategory,
    ToolDefinition,
    ToolInvocationStatus,
    validate_permissions,
)
from app.core.tools.policy import ExecutionPolicy
from app.core.tools.registry import tool_registry
from app.core.tools.sandbox import build_sandbox_contract
from app.core.runtime_metrics import build_runtime_metrics
from app.core.runtime_timeline import build_runtime_timeline
from app.core.world import World, world
from app.main import app


def reset_global_world():
    world.hydrate(
        {
            "agents": {},
            "departments": {},
            "tasks": {},
            "events": [],
            "activity_log": [],
            "commands": {},
            "tool_invocations": {},
            "tool_audit_log": [],
            "permission_grants": {},
            "sandbox_contracts": {},
        }
    )


def test_tool_registry_lists_tools():
    tools = tool_registry.list_tools()

    assert len(tools) >= 5
    assert {
        tool.id
        for tool in tools
    } >= {
        "generate_report_stub",
        "summarize_text_stub",
        "inspect_project_stub",
        "run_tests_stub",
        "web_research_stub",
    }


def test_permission_validation():
    permissions = validate_permissions(
        ["read_project_files", Permission.RUN_TESTS]
    )

    assert permissions == [
        Permission.READ_PROJECT_FILES,
        Permission.RUN_TESTS,
    ]

    with pytest.raises(ValueError):
        validate_permissions(["unknown_permission"])


def test_policy_allowed_low_risk():
    tool = tool_registry.get("generate_report_stub")
    decision = ExecutionPolicy().evaluate(tool)

    assert decision.decision == PolicyDecisionValue.ALLOWED


def test_default_policy_profile():
    assert ExecutionPolicy().profile == PolicyProfile.SAFE_LOCAL


def test_locked_down_behavior():
    tool = tool_registry.get("generate_report_stub")
    decision = ExecutionPolicy(
        profile=PolicyProfile.LOCKED_DOWN
    ).evaluate(tool)

    assert (
        decision.decision
        == PolicyDecisionValue.REQUIRES_APPROVAL
    )
    assert "locked_down" in decision.reason


def test_safe_local_behavior():
    low_tool = tool_registry.get("generate_report_stub")
    medium_tool = tool_registry.get("run_tests_stub")
    policy = ExecutionPolicy(profile=PolicyProfile.SAFE_LOCAL)

    assert (
        policy.evaluate(low_tool).decision
        == PolicyDecisionValue.ALLOWED
    )
    assert (
        policy.evaluate(medium_tool).decision
        == PolicyDecisionValue.REQUIRES_APPROVAL
    )


def test_assisted_behavior():
    medium_tool = tool_registry.get("run_tests_stub")
    decision = ExecutionPolicy(
        profile=PolicyProfile.ASSISTED
    ).evaluate(medium_tool)

    assert (
        decision.decision
        == PolicyDecisionValue.REQUIRES_APPROVAL
    )
    assert "assisted" in decision.reason


def test_policy_requires_approval_medium_risk():
    tool = tool_registry.get("run_tests_stub")
    decision = ExecutionPolicy().evaluate(tool)

    assert (
        decision.decision
        == PolicyDecisionValue.REQUIRES_APPROVAL
    )


def test_policy_blocks_forbidden_permission():
    tool = tool_registry.get("web_research_stub")
    decision = ExecutionPolicy().evaluate(tool)

    assert decision.decision == PolicyDecisionValue.BLOCKED
    assert "access_network" in decision.reason


def test_autonomous_safe_with_grant():
    tool = tool_registry.get("run_tests_stub")
    grant = PermissionGrant(
        scope_type=PermissionScopeType.GLOBAL,
        permission=Permission.RUN_TESTS,
        tool_id=tool.id,
        risk_level_max=RiskLevel.MEDIUM,
        granted_by="test",
    )
    decision = ExecutionPolicy(
        profile=PolicyProfile.AUTONOMOUS_SAFE
    ).evaluate(
        tool,
        grants=[grant],
    )

    assert decision.decision == PolicyDecisionValue.ALLOWED
    assert decision.used_grant_ids == [grant.id]


def test_missing_grant_requires_approval():
    tool = tool_registry.get("run_tests_stub")
    decision = ExecutionPolicy(
        profile=PolicyProfile.AUTONOMOUS_SAFE
    ).evaluate(tool)

    assert (
        decision.decision
        == PolicyDecisionValue.REQUIRES_APPROVAL
    )
    assert "Scoped permission missing" in decision.reason


def test_expired_grant_ignored():
    tool = tool_registry.get("run_tests_stub")
    grant = PermissionGrant(
        scope_type=PermissionScopeType.GLOBAL,
        permission=Permission.RUN_TESTS,
        tool_id=tool.id,
        risk_level_max=RiskLevel.MEDIUM,
        granted_by="test",
        expires_at=1,
    )
    decision = ExecutionPolicy(
        profile=PolicyProfile.AUTONOMOUS_SAFE
    ).evaluate(
        tool,
        grants=[grant],
    )

    assert (
        decision.decision
        == PolicyDecisionValue.REQUIRES_APPROVAL
    )


def test_invoke_allowed_stub():
    test_world = World()
    invocation = ToolExecutor(test_world).invoke(
        "generate_report_stub",
        arguments={
            "topic": "Quarterly status",
        },
    )

    assert invocation.status == ToolInvocationStatus.COMPLETED
    assert invocation.result["kind"] == "report"
    assert len(test_world.tool_audit_log) == 4


def test_invoke_approval_required():
    test_world = World()
    invocation = ToolExecutor(test_world).invoke(
        "run_tests_stub",
    )

    assert (
        invocation.status
        == ToolInvocationStatus.AWAITING_APPROVAL
    )
    assert invocation.approval_required is True


def test_approve_invocation_executes_stub():
    test_world = World()
    executor = ToolExecutor(test_world)
    invocation = executor.invoke("run_tests_stub")

    approved = executor.approve(
        invocation.id,
        approved_by="ceo",
    )

    assert approved.status == ToolInvocationStatus.COMPLETED
    assert approved.approved_by == "ceo"
    assert approved.result["status"] == "simulated_pass"


def test_reject_invocation():
    test_world = World()
    executor = ToolExecutor(test_world)
    invocation = executor.invoke("run_tests_stub")

    rejected = executor.reject(
        invocation.id,
        rejected_by="ceo",
    )

    assert rejected.status == ToolInvocationStatus.CANCELLED
    assert "ceo" in rejected.error


def test_approve_with_grant_creates_grant():
    test_world = World()
    executor = ToolExecutor(test_world)
    invocation = executor.invoke(
        "run_tests_stub",
        agent_id="agent-1",
    )

    approved = executor.approve(
        invocation.id,
        approved_by="ceo",
        create_grant=True,
        grant_expires_in_minutes=5,
    )

    assert approved.status == ToolInvocationStatus.COMPLETED
    assert len(test_world.permission_grants) == 1
    grant = next(iter(test_world.permission_grants.values()))
    assert grant.scope_type == PermissionScopeType.AGENT
    assert grant.scope_id == "agent-1"
    assert approved.used_grant_ids == [grant.id]


def test_invocation_allowed_by_grant():
    test_world = World()
    tool = tool_registry.get("run_tests_stub")
    grant = PermissionGrant(
        scope_type=PermissionScopeType.GLOBAL,
        permission=Permission.RUN_TESTS,
        tool_id=tool.id,
        risk_level_max=RiskLevel.MEDIUM,
        granted_by="test",
    )
    test_world.add_permission_grant(grant)
    invocation = ToolExecutor(
        test_world,
        policy=ExecutionPolicy(
            profile=PolicyProfile.AUTONOMOUS_SAFE
        ),
    ).invoke("run_tests_stub")

    assert invocation.status == ToolInvocationStatus.COMPLETED
    assert invocation.used_grant_ids == [grant.id]
    assert any(
        entry.action
        == ToolAuditAction.SCOPED_PERMISSION_ALLOWED
        for entry in test_world.tool_audit_log
    )


def test_audit_log_entries():
    test_world = World()
    invocation = ToolExecutor(test_world).invoke(
        "web_research_stub",
    )

    assert invocation.status == ToolInvocationStatus.BLOCKED
    assert [
        entry.action
        for entry in test_world.tool_audit_log
    ] == [
        "requested",
        "policy_profile_applied",
        "policy_blocked",
    ]
    assert any(
        event["type"] == "tool_blocked"
        for event in test_world.events
    )


def test_revoke_grant():
    reset_global_world()
    client = TestClient(app)
    created = client.post(
        "/tools/grants",
        json={
            "scope_type": "global",
            "permission": "create_report",
            "tool_id": "generate_report_stub",
            "reason": "test grant",
        },
    ).json()

    response = client.post(
        f"/tools/grants/{created['id']}/revoke"
    )

    assert response.status_code == 200
    assert response.json()["active"] is False
    assert response.json()["revoked_at"] is not None


def test_tools_api_shape():
    reset_global_world()
    client = TestClient(app)

    tools = client.get("/tools")
    assert tools.status_code == 200
    assert tools.json()

    invoked = client.post(
        "/tools/invoke",
        json={
            "tool_id": "generate_report_stub",
            "arguments": {
                "topic": "Ops",
            },
        },
    )
    assert invoked.status_code == 200
    assert invoked.json()["status"] == "completed"

    invocations = client.get("/tools/invocations")
    assert invocations.status_code == 200
    assert invocations.json()[0]["tool_id"] == (
        "generate_report_stub"
    )


def test_grants_api_shape():
    reset_global_world()
    client = TestClient(app)

    created = client.post(
        "/tools/grants",
        json={
            "scope_type": "global",
            "permission": "generate_content",
            "tool_id": "summarize_text_stub",
            "risk_level_max": "low",
            "expires_in_minutes": 10,
            "reason": "test",
        },
    )
    assert created.status_code == 200

    listed = client.get("/tools/grants")
    assert listed.status_code == 200
    data = listed.json()
    assert data["policy_profile"] == "safe_local"
    assert data["grants"][0]["permission"] == "generate_content"


def test_audit_entries_for_grants():
    reset_global_world()
    client = TestClient(app)
    client.post(
        "/tools/grants",
        json={
            "scope_type": "global",
            "permission": "create_report",
            "reason": "audit",
        },
    )

    assert world.tool_audit_log[-1].action == "grant_created"


def test_approvals_list_api():
    reset_global_world()
    client = TestClient(app)
    client.post(
        "/tools/invoke",
        json={
            "tool_id": "run_tests_stub",
        },
    )

    response = client.get("/approvals")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["tool"]["id"] == "run_tests_stub"


def test_approval_detail_api():
    reset_global_world()
    client = TestClient(app)
    invocation = client.post(
        "/tools/invoke",
        json={
            "tool_id": "run_tests_stub",
            "task_id": "task-1",
        },
    ).json()

    response = client.get(
        f"/approvals/{invocation['id']}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["invocation"]["id"] == invocation["id"]
    assert data["required_permissions"] == ["run_tests"]
    assert data["suggested_approval_scopes"]


def test_suggested_scopes_low_medium_high_critical():
    low_invocation = ToolExecutor(World()).invoke(
        "generate_report_stub",
        task_id="task-1",
        agent_id="agent-1",
    )
    low_tool = tool_registry.get("generate_report_stub")
    medium_tool = tool_registry.get("run_tests_stub")
    high_tool = tool_registry.get("web_research_stub")
    critical_tool = ToolDefinition(
        id="critical_stub",
        name="Critical",
        description="Critical",
        category=ToolCategory.SYSTEM,
        required_permissions=[Permission.MODIFY_SYSTEM],
        risk_level=RiskLevel.CRITICAL,
    )

    assert {
        scope["scope_type"]
        for scope in suggested_approval_scopes(
            low_invocation,
            low_tool,
        )
    } >= {"once", "task", "agent"}
    assert [
        scope["scope_type"]
        for scope in suggested_approval_scopes(
            low_invocation,
            medium_tool,
        )
    ] == ["once", "task"]
    assert [
        scope["scope_type"]
        for scope in suggested_approval_scopes(
            low_invocation,
            high_tool,
        )
    ] == ["once"]
    assert (
        suggested_approval_scopes(
            low_invocation,
            critical_tool,
        )
        == []
    )


def test_sandbox_contract_creation():
    tool = tool_registry.get("run_tests_stub")
    contract = build_sandbox_contract(tool)

    assert contract.tool_id == "run_tests_stub"
    assert contract.requires_dry_run is True
    assert "run_command" in contract.denied_operations


def test_dry_run_does_not_execute_tool():
    test_world = World()
    invocation = ToolExecutor(test_world).invoke(
        "run_tests_stub",
        dry_run=True,
    )

    assert invocation.status == ToolInvocationStatus.COMPLETED
    assert invocation.dry_run is True
    assert invocation.result["status"] == "dry_run_completed"
    assert invocation.result["side_effects_performed"] == []
    assert "simulated_pass" not in str(invocation.result)


def test_dry_run_returns_execution_plan():
    test_world = World()
    invocation = ToolExecutor(test_world).invoke(
        "generate_report_stub",
        arguments={
            "topic": "Plan",
        },
        dry_run=True,
    )

    output = invocation.result["output"]
    assert "what_would_run" in output
    assert output["required_permissions"] == ["create_report"]
    assert invocation.sandbox_contract_id in test_world.sandbox_contracts


def test_audit_drilldown_api():
    reset_global_world()
    client = TestClient(app)
    invocation = client.post(
        "/tools/invoke",
        json={
            "tool_id": "run_tests_stub",
        },
    ).json()

    response = client.get(
        f"/tools/invocations/{invocation['id']}/audit"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["invocation"]["id"] == invocation["id"]
    assert data["audit_trail"]


def test_approve_once_from_approval_center():
    reset_global_world()
    client = TestClient(app)
    invocation = client.post(
        "/tools/invoke",
        json={
            "tool_id": "run_tests_stub",
        },
    ).json()

    response = client.post(
        f"/approvals/{invocation['id']}/approve",
        json={
            "approved_by": "ceo",
        },
    )

    assert response.status_code == 200
    assert response.json()["invocation"]["status"] == "completed"
    assert any(
        entry.action == "approval_once_approved"
        for entry in world.tool_audit_log
    )


def test_approve_with_scoped_grant_from_approval_center():
    reset_global_world()
    client = TestClient(app)
    invocation = client.post(
        "/tools/invoke",
        json={
            "tool_id": "run_tests_stub",
            "task_id": "task-1",
        },
    ).json()

    response = client.post(
        f"/approvals/{invocation['id']}/approve",
        json={
            "approved_by": "ceo",
            "create_grant": True,
            "grant_scope_type": "task",
            "grant_scope_id": "task-1",
            "grant_expires_in_minutes": 15,
        },
    )

    assert response.status_code == 200
    assert len(world.permission_grants) == 1
    grant = next(iter(world.permission_grants.values()))
    assert grant.scope_type == "task"
    assert grant.scope_id == "task-1"


def test_reject_approval_center():
    reset_global_world()
    client = TestClient(app)
    invocation = client.post(
        "/tools/invoke",
        json={
            "tool_id": "run_tests_stub",
        },
    ).json()

    response = client.post(
        f"/approvals/{invocation['id']}/reject",
        json={
            "rejected_by": "ceo",
        },
    )

    assert response.status_code == 200
    assert response.json()["invocation"]["status"] == "cancelled"


def test_metrics_for_approvals_and_dry_run():
    test_world = World()
    executor = ToolExecutor(test_world)
    pending = executor.invoke("run_tests_stub")
    executor.invoke("generate_report_stub", dry_run=True)
    executor.approve(pending.id)
    rejected = executor.invoke("run_tests_stub")
    executor.reject(rejected.id)

    metrics = build_runtime_metrics(test_world)["global_metrics"]

    assert metrics["approvals_approved_total"] == 1
    assert metrics["approvals_rejected_total"] == 1
    assert metrics["dry_run_invocations_total"] == 1
    assert metrics["sandbox_contracts_created"] == 1
    assert metrics["pending_approvals_by_risk"]["medium"] == 0


def test_timeline_events_for_dry_run_and_sandbox():
    test_world = World()
    invocation = ToolExecutor(test_world).invoke(
        "generate_report_stub",
        dry_run=True,
    )

    timeline = build_runtime_timeline(test_world)
    event_types = {
        entry["event_type"]
        for entry in timeline["entries"]
        if entry.get("metadata", {}).get("invocation_id")
        == invocation.id
    }

    assert "dry_run_requested" in event_types
    assert "dry_run_completed" in event_types
    assert "sandbox_contract_created" in event_types
