from app.core.bootstrap import bootstrap_world
from app.core.factory import create_task
from app.core.world import world
from app.schemas.protocol import (
    AgentStatus,
    TaskStatus,
)


def reset_world():
    world.hydrate(
        {
            "agents": {},
            "departments": {},
            "tasks": {},
            "events": [],
        }
    )


def test_world_state_initialization():
    reset_world()

    bootstrap_world()

    snapshot = world.serialize()

    assert len(snapshot["agents"]) == 8
    assert len(snapshot["departments"]) == 4
    assert snapshot["tasks"] == {}


def test_create_task():
    reset_world()

    task = create_task(
        title="Create API",
        description="Create backend API",
        department="development",
    )

    assert task.id in world.tasks
    assert world.tasks[task.id].status == TaskStatus.CREATED


def test_update_task_status():
    reset_world()

    task = create_task(
        title="Create API",
        description="Create backend API",
        department="development",
    )

    updated = world.update_task(
        task.id,
        status=TaskStatus.IN_PROGRESS,
        progress=25,
    )

    assert updated is not None
    assert updated.status == TaskStatus.IN_PROGRESS
    assert updated.progress == 25


def test_update_agent_status():
    reset_world()
    bootstrap_world()

    agent = next(iter(world.agents.values()))

    updated = world.update_agent(
        agent.id,
        status=AgentStatus.WORKING,
        current_action="Testing",
    )

    assert updated is not None
    assert updated.status == AgentStatus.WORKING
    assert updated.current_action == "Testing"
