from fastapi.testclient import TestClient

from app.core.runtime_metrics import (
    build_queue_health,
    build_runtime_metrics,
)
from app.core.world import World, world
from app.main import app
from app.models.agent import Agent
from app.models.command import UserCommand
from app.models.department import Department
from app.models.task import Task


def make_agent(
    name: str,
    department: str,
    status: str = "idle",
    is_manager: bool = False,
):
    return Agent(
        name=name,
        role="Manager" if is_manager else "Worker",
        department=department,
        personality="test",
        status=status,
        is_manager=is_manager,
        manager_for_department=(
            department if is_manager else None
        ),
    )


def make_world():
    test_world = World()
    test_world.add_department(
        Department(
            name="development",
            description="Development",
        )
    )
    manager = make_agent(
        "Alex",
        "development",
        is_manager=True,
    )
    worker = make_agent(
        "Ethan",
        "development",
        status="working",
    )
    idle = make_agent(
        "Mia",
        "assistant",
    )
    task = Task(
        title="Build API",
        description="Build API",
        department="development",
        status="in_progress",
        progress=40,
        assigned_to=worker.id,
    )
    worker.current_task_id = task.id
    worker.workload = 1

    test_world.add_agent(manager)
    test_world.add_agent(worker)
    test_world.add_agent(idle)
    test_world.add_task(task)
    test_world.add_task(
        Task(
            title="Queued task",
            description="Queued task",
            department="development",
            status="queued",
        )
    )
    test_world.add_task(
        Task(
            title="Failed task",
            description="Failed task",
            department="assistant",
            status="failed",
        )
    )
    test_world.add_command(
        UserCommand(
            raw_text="Build API",
            status="task_created",
        )
    )
    test_world.add_event(
        "manager_assigned_worker",
        {
            "agent_name": worker.name,
            "task_title": task.title,
        },
    )
    test_world.add_activity(
        worker.id,
        task.id,
        "task_failed",
        "Failure happened",
    )

    return test_world


def reset_global_world():
    world.hydrate(
        {
            "agents": {},
            "departments": {},
            "tasks": {},
            "events": [],
            "activity_log": [],
            "commands": {},
        }
    )


def test_global_metrics_calculation():
    metrics = build_runtime_metrics(make_world())
    global_metrics = metrics["global_metrics"]

    assert global_metrics["total_tasks"] == 3
    assert global_metrics["queued_tasks"] == 1
    assert global_metrics["in_progress_tasks"] == 1
    assert global_metrics["failed_tasks"] == 1
    assert global_metrics["total_agents"] == 3
    assert global_metrics["busy_agents"] == 1
    assert global_metrics["managers_count"] == 1


def test_department_metrics():
    metrics = build_runtime_metrics(make_world())
    development = next(
        item
        for item in metrics["department_metrics"]
        if item["department"] == "development"
    )

    assert development["total_agents"] == 2
    assert development["busy_agents"] == 1
    assert development["queued_tasks"] == 1
    assert development["workload_score"] == 0.6


def test_agent_workload():
    metrics = build_runtime_metrics(make_world())
    worker = next(
        item
        for item in metrics["agent_workload"]
        if item["name"] == "Ethan"
    )

    assert worker["current_task_title"] == "Build API"
    assert worker["workload"] == 1
    assert worker["recent_activity_count"] == 1


def test_manager_decisions_extraction():
    metrics = build_runtime_metrics(make_world())

    assert (
        metrics["recent_manager_decisions"][0]["type"]
        == "manager_assigned_worker"
    )


def test_queue_health_healthy():
    assert (
        build_queue_health(
            queued_tasks=0,
            in_progress_tasks=0,
            failed_recent=0,
            available_agents=2,
        )
        == "healthy"
    )


def test_queue_health_overloaded():
    assert (
        build_queue_health(
            queued_tasks=5,
            in_progress_tasks=0,
            failed_recent=0,
            available_agents=2,
        )
        == "overloaded"
    )


def test_runtime_metrics_api_shape():
    reset_global_world()
    agent = make_agent(
        "Ethan",
        "development",
    )
    world.add_agent(agent)
    world.add_task(
        Task(
            title="Queued",
            description="Queued",
            department="development",
            status="queued",
        )
    )

    response = TestClient(app).get(
        "/runtime/metrics"
    )

    assert response.status_code == 200
    data = response.json()
    assert "global_metrics" in data
    assert "department_metrics" in data
    assert "agent_workload" in data
    assert "queue_health" in data
