from app.config.settings import settings
from app.core.factory import create_task
from app.core.persistence import (
    load_world_state,
    save_world_state,
)
from app.core.world import World, world


def reset_world():
    world.hydrate(
        {
            "agents": {},
            "departments": {},
            "tasks": {},
            "events": [],
        }
    )


def test_world_state_persistence_roundtrip(tmp_path):
    reset_world()

    original_enabled = settings.PERSISTENCE_ENABLED
    original_path = settings.PERSISTENCE_PATH
    settings.PERSISTENCE_ENABLED = True
    settings.PERSISTENCE_PATH = str(
        tmp_path / "world_state.json"
    )

    try:
        task = create_task(
            title="Persist task",
            description="Persist task",
            department="development",
        )

        save_world_state(world)

        restored = World()
        loaded = load_world_state(restored)

        assert loaded is True
        assert task.id in restored.tasks
        assert restored.tasks[task.id].title == "Persist task"
    finally:
        settings.PERSISTENCE_ENABLED = original_enabled
        settings.PERSISTENCE_PATH = original_path
