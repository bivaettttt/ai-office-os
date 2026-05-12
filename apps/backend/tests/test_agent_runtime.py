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
from app.core.agent_runtime.execution import (
    advance_task_steps,
    all_steps_completed,
    calculate_task_progress,
    initialize_task_execution,
    mark_active_step_failed,
    review_completed_task,
)
from app.core.agent_runtime.control import (
    cancel_task,
    pause_task,
    resume_task,
    retry_failed_step,
)
from app.core.agent_runtime.planning import (
    generate_task_steps,
)
from app.core.agent_runtime.registry import AgentRegistry
from app.core.agent_runtime.runtime import AgentRuntimeService
from app.core.orchestration.task_dispatcher import (
    TaskDispatcher,
)
from app.core.world import World
from app.core.world import world as global_world
from app.models.agent import Agent
from app.models.department import Department
from app.models.task import (
    Task,
    TaskRuntimePhase,
    TaskStepStatus,
)
from app.api.tasks import task_detail


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


def test_plan_generation_by_department():
    development_steps = generate_task_steps(
        "development"
    )
    analytics_steps = generate_task_steps(
        "analytics"
    )

    assert [
        step.title
        for step in development_steps
    ] == [
        "Understand request",
        "Inspect project context",
        "Implement change",
        "Validate result",
        "Summarize output",
    ]
    assert analytics_steps[0].title == (
        "Understand research goal"
    )


def test_task_steps_initialized_on_creation():
    task = Task(
        title="Build feature",
        description="Build feature",
        department="development",
        steps=generate_task_steps("development"),
    )
    task.plan = [step.title for step in task.steps]

    assert len(task.steps) == 5
    assert task.plan[0] == "Understand request"
    assert task.steps[0].status == "pending"


def test_first_step_starts_on_assignment():
    task = Task(
        title="Fix bug",
        description="Fix bug",
        department="development",
        steps=generate_task_steps("development"),
    )
    agent = make_agent(
        "Ethan",
        "development",
        ["debugging"],
    )

    asyncio.run(
        TaskDispatcher().dispatch_task(task, agent)
    )

    assert task.status == "in_progress"
    assert task.active_step_index == 0
    assert task.steps[0].status == "in_progress"
    assert task.steps[0].assigned_agent_id == agent.id
    assert task.started_at is not None


def test_progress_moves_through_steps():
    task = Task(
        title="Fix bug",
        description="Fix bug",
        department="development",
        steps=generate_task_steps("development")[:2],
    )
    agent_id = "agent-1"

    initialize_task_execution(task, agent_id)
    events = advance_task_steps(task, agent_id, 100)

    assert task.steps[0].status == "completed"
    assert task.steps[1].status == "in_progress"
    assert task.active_step_index == 1
    assert calculate_task_progress(task) == 50
    assert [
        event["type"]
        for event in events
    ] == ["step_completed", "step_started"]


def test_task_completes_only_after_all_steps_completed():
    task = Task(
        title="Fix bug",
        description="Fix bug",
        department="development",
        steps=generate_task_steps("development")[:2],
    )
    agent_id = "agent-1"

    initialize_task_execution(task, agent_id)
    advance_task_steps(task, agent_id, 100)

    assert all_steps_completed(task) is False

    advance_task_steps(task, agent_id, 100)

    assert all_steps_completed(task) is True
    assert task.progress == 100


def test_manager_review_stub():
    task = Task(
        title="Fix bug",
        description="Fix bug",
        department="development",
        steps=generate_task_steps("development")[:1],
    )
    initialize_task_execution(task, "agent-1")
    advance_task_steps(task, "agent-1", 100)

    summary = review_completed_task(
        task,
        "Ethan",
    )

    assert task.status == "completed"
    assert task.reviewed_at is not None
    assert task.completed_at is not None
    assert task.result_summary == summary
    assert "1 steps" in summary


def test_activity_log_entries():
    test_world = World()

    test_world.add_activity(
        "agent-1",
        "task-1",
        "task_assigned",
        "Assigned task",
    )
    test_world.add_activity(
        "agent-1",
        "task-1",
        "step_completed",
        "Completed step",
    )

    snapshot = test_world.serialize()

    assert len(snapshot["activity_log"]) == 2
    assert snapshot["activity_log"][0]["type"] == (
        "task_assigned"
    )
    assert snapshot["activity_log"][1]["message"] == (
        "Completed step"
    )


def test_runtime_phase_defaults():
    task = Task(
        title="Default phase",
        description="Default phase",
        department="assistant",
    )

    assert task.runtime_phase == "created"


def test_pause_task():
    test_world = World()
    task = Task(
        title="Pause me",
        description="Pause me",
        department="development",
        status="in_progress",
        runtime_phase=TaskRuntimePhase.EXECUTING,
        steps=generate_task_steps("development")[:1],
    )
    agent = make_agent(
        "Ethan",
        "development",
        ["debugging"],
        status="working",
    )
    task.assigned_to = agent.id
    agent.current_task_id = task.id
    test_world.add_agent(agent)
    test_world.add_task(task)

    pause_task(test_world, task)

    assert task.runtime_phase == "paused"
    assert agent.status == "idle"
    assert agent.current_task_id == task.id
    assert test_world.activity_log[-1]["type"] == (
        "task_paused"
    )


def test_resume_task():
    test_world = World()
    task = Task(
        title="Resume me",
        description="Resume me",
        department="development",
        status="in_progress",
        runtime_phase=TaskRuntimePhase.PAUSED,
        steps=generate_task_steps("development")[:1],
    )
    agent = make_agent(
        "Ethan",
        "development",
        ["debugging"],
        status="idle",
    )
    task.assigned_to = agent.id
    agent.current_task_id = task.id
    test_world.add_agent(agent)
    test_world.add_task(task)

    resume_task(test_world, task)

    assert task.runtime_phase == "executing"
    assert task.status == "in_progress"
    assert agent.status == "working"
    assert test_world.activity_log[-1]["type"] == (
        "task_resumed"
    )


def test_cancel_task_releases_agent():
    test_world = World()
    task = Task(
        title="Cancel me",
        description="Cancel me",
        department="development",
        status="in_progress",
        runtime_phase=TaskRuntimePhase.EXECUTING,
    )
    agent = make_agent(
        "Ethan",
        "development",
        ["debugging"],
        status="working",
        workload=1,
    )
    task.assigned_to = agent.id
    agent.current_task_id = task.id
    test_world.add_agent(agent)
    test_world.add_task(task)

    cancel_task(test_world, task)

    assert task.status == "cancelled"
    assert task.runtime_phase == "cancelled"
    assert agent.status == "idle"
    assert agent.current_task_id is None
    assert agent.workload == 0
    assert test_world.activity_log[-1]["type"] == (
        "task_cancelled"
    )


def test_failed_step_marks_task_failed():
    task = Task(
        title="Fail step",
        description="Fail step",
        department="development",
        status="in_progress",
        runtime_phase=TaskRuntimePhase.EXECUTING,
        steps=generate_task_steps("development")[:1],
    )
    initialize_task_execution(task, "agent-1")

    step = mark_active_step_failed(
        task,
        "test failure",
    )

    assert step is not None
    assert step.status == "failed"
    assert task.status == "failed"
    assert task.runtime_phase == "failed"
    assert task.failure_reason == "test failure"


def test_retry_failed_step():
    test_world = World()
    task = Task(
        title="Retry step",
        description="Retry step",
        department="development",
        status="failed",
        runtime_phase=TaskRuntimePhase.FAILED,
        failure_reason="failed once",
        steps=generate_task_steps("development")[:1],
    )
    agent = make_agent(
        "Ethan",
        "development",
        ["debugging"],
        status="idle",
    )
    task.assigned_to = agent.id
    test_world.add_agent(agent)
    test_world.add_task(task)
    initialize_task_execution(task, agent.id)
    mark_active_step_failed(task, "failed once")

    step = retry_failed_step(test_world, task)

    assert step is not None
    assert step.status == "in_progress"
    assert task.status == "in_progress"
    assert task.runtime_phase == "executing"
    assert task.failure_reason is None
    assert agent.status == "working"
    assert test_world.activity_log[-1]["type"] == (
        "task_retry_started"
    )


def test_manager_review_approve():
    task = Task(
        title="Review approve",
        description="Review approve",
        department="development",
        steps=generate_task_steps("development")[:1],
    )
    initialize_task_execution(task, "agent-1")
    advance_task_steps(task, "agent-1", 100)

    summary = review_completed_task(task, "Ethan")

    assert task.runtime_phase == "completed"
    assert task.status == "completed"
    assert task.result_summary == summary


def test_manager_review_failed_for_failed_step():
    task = Task(
        title="Review fail",
        description="Review fail",
        department="development",
        steps=generate_task_steps("development")[:1],
    )
    task.steps[0].status = TaskStepStatus.FAILED

    summary = review_completed_task(task, "Ethan")

    assert task.runtime_phase == "failed"
    assert task.status == "failed"
    assert task.failure_reason == summary


def test_task_detail_api_shape():
    global_world.hydrate(
        {
            "agents": {},
            "departments": {},
            "tasks": {},
            "events": [],
            "activity_log": [],
        }
    )
    agent = make_agent(
        "Ethan",
        "development",
        ["debugging"],
    )
    manager = make_agent(
        "Alex",
        "development",
        ["project_management"],
        is_manager=True,
    )
    task = Task(
        title="Detail",
        description="Detail",
        department="development",
        assigned_to=agent.id,
        assigned_by_manager_id=manager.id,
    )
    global_world.add_agent(agent)
    global_world.add_agent(manager)
    global_world.add_task(task)
    global_world.add_activity(
        agent.id,
        task.id,
        "task_assigned",
        "Assigned",
    )

    detail = task_detail(task)

    assert detail["task"]["id"] == task.id
    assert detail["assigned_agent"]["id"] == agent.id
    assert detail["assigned_manager"]["id"] == manager.id
    assert detail["activity_log"][0]["task_id"] == task.id
