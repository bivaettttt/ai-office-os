import asyncio

from app.core.agent_runtime.capabilities import (
    Capability,
    infer_required_capabilities,
    normalize_capability,
)
from app.core.agent_runtime.departments import (
    DEPARTMENT_DEFINITIONS,
)
from app.core.agent_runtime.matching import (
    CapabilityMatcher,
)
from app.core.agent_runtime.registry import AgentRegistry
from app.core.agent_runtime.runtime import AgentRuntimeService
from app.core.world import World
from app.models.agent import Agent
from app.models.department import Department
from app.models.task import Task


def make_agent(
    name: str,
    department: str,
    capabilities: list[str],
    *,
    status: str = "idle",
    workload: int = 0,
    performance_score: float = 1.0,
    is_manager: bool = False,
):
    return Agent(
        name=name,
        role="Manager" if is_manager else "Worker",
        department=department,
        personality="test",
        capabilities=capabilities,
        status=status,
        workload=workload,
        performance_score=performance_score,
        is_manager=is_manager,
        manager_for_department=(
            department if is_manager else None
        ),
    )


def test_capability_definitions_and_validation():
    assert (
        Capability.CODE_GENERATION.value
        == "code_generation"
    )
    assert normalize_capability("debugging") == "debugging"

    try:
        normalize_capability("unknown")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown capability accepted")


def test_department_definitions():
    assert set(DEPARTMENT_DEFINITIONS) == {
        "development",
        "analytics",
        "assistant",
        "content",
        "operations",
    }
    assert (
        "code_generation"
        in DEPARTMENT_DEFINITIONS[
            "development"
        ].default_capabilities
    )
    assert (
        DEPARTMENT_DEFINITIONS[
            "operations"
        ].manager_role
        == "Operations Manager"
    )


def test_agent_registry():
    test_world = World()
    department = Department(
        name="development",
        description="Development",
    )
    test_world.add_department(department)
    manager = make_agent(
        "Alex",
        "development",
        ["project_management"],
        is_manager=True,
    )
    worker = make_agent(
        "Ethan",
        "development",
        ["code_generation", "debugging"],
    )
    department.manager_agent_id = manager.id

    registry = AgentRegistry(test_world)
    registry.register(manager)
    registry.register(worker)

    assert registry.get(worker.id) == worker
    assert registry.list_by_department("development") == [
        manager,
        worker,
    ]
    assert registry.list_available_agents("development") == [
        worker
    ]
    assert registry.get_department_manager(
        "development"
    ) == manager
    assert registry.find_agents_by_capability(
        "debugging"
    ) == [worker]


def test_capability_matching_prefers_best_available_agent():
    test_world = World()
    registry = AgentRegistry(test_world)
    registry.register(
        make_agent(
            "Busy",
            "development",
            ["debugging"],
            workload=4,
        )
    )
    best = registry.register(
        make_agent(
            "Ready",
            "development",
            ["debugging", "code_generation"],
            workload=0,
            performance_score=1.2,
        )
    )
    registry.register(
        make_agent(
            "Other",
            "analytics",
            ["debugging", "code_generation"],
            workload=0,
        )
    )

    match = CapabilityMatcher(registry).find_best_agent(
        "development",
        ["debugging", "code_generation"],
    )

    assert match.agent == best
    assert match.fallback_used is False
    assert match.missing_capabilities == []


def test_capability_matching_uses_fallback():
    test_world = World()
    registry = AgentRegistry(test_world)
    fallback = registry.register(
        make_agent(
            "Researcher",
            "analytics",
            ["web_research", "data_analysis"],
        )
    )

    match = CapabilityMatcher(registry).find_best_agent(
        "development",
        ["web_research"],
    )

    assert match.agent == fallback
    assert match.fallback_used is True


def test_manager_selection_assigns_worker():
    test_world = World()
    department = Department(
        name="development",
        description="Development",
    )
    test_world.add_department(department)

    manager = make_agent(
        "Alex",
        "development",
        ["project_management"],
        is_manager=True,
    )
    worker = make_agent(
        "Ethan",
        "development",
        ["debugging"],
    )
    department.manager_agent_id = manager.id
    test_world.add_agent(manager)
    test_world.add_agent(worker)

    task = Task(
        title="Fix bug",
        description="Fix error",
        department="development",
        required_capabilities=["debugging"],
    )

    _manager, selected = asyncio.run(
        AgentRuntimeService(test_world).select_agent_for_task(
            task
        )
    )

    assert selected == worker
    assert task.assigned_by_manager_id == manager.id


def test_task_capability_inference():
    assert infer_required_capabilities(
        "Fix backend error",
        "development",
    ) == ["debugging", "code_generation"]

    assert infer_required_capabilities(
        "Research market and analyze metrics",
        "analytics",
    ) == ["web_research", "data_analysis"]

    assert infer_required_capabilities(
        "Write article post",
        "content",
    ) == ["content_writing"]
