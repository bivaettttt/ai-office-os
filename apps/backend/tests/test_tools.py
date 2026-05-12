import pytest

from fastapi.testclient import TestClient

from app.core.tools.executor import ToolExecutor
from app.core.tools.permissions import (
    Permission,
    PolicyDecisionValue,
    ToolInvocationStatus,
    validate_permissions,
)
from app.core.tools.policy import ExecutionPolicy
from app.core.tools.registry import tool_registry
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
    assert len(test_world.tool_audit_log) == 3


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
        "policy_blocked",
    ]
    assert any(
        event["type"] == "tool_blocked"
        for event in test_world.events
    )


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
