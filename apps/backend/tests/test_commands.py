from fastapi.testclient import TestClient

from app.core.commands import (
    infer_priority,
    route_user_command,
)
from app.core.world import World, world
from app.main import app
from app.models.command import UserCommand


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


def test_command_model_defaults():
    command = UserCommand(
        raw_text="Make a landing",
    )

    assert command.status == "received"
    assert command.inferred_priority == "normal"
    assert command.created_task_id is None


def test_development_command_routing():
    route = route_user_command(
        "сделай landing website frontend"
    )

    assert route.department == "development"
    assert route.priority == "normal"
    assert "code_generation" in route.required_capabilities
    assert "website" in route.explanation


def test_analytics_command_routing():
    route = route_user_command(
        "analyze market competitors"
    )

    assert route.department == "analytics"
    assert "data_analysis" in route.required_capabilities


def test_assistant_command_routing():
    route = route_user_command(
        "напомни завтра купить билеты"
    )

    assert route.department == "assistant"
    assert "scheduling" in route.required_capabilities


def test_content_command_routing():
    route = route_user_command(
        "напиши post для telegram"
    )

    assert route.department == "content"
    assert "content_writing" in route.required_capabilities


def test_priority_inference():
    assert infer_priority("urgent task") == "high"
    assert infer_priority("срочно сделать") == "high"
    assert infer_priority("later please") == "low"
    assert infer_priority("обычная задача") == "normal"


def test_command_creates_task_and_stores_id():
    reset_global_world()
    client = TestClient(app)

    response = client.post(
        "/commands",
        json={
            "text": "сделай лендинг для кофейни",
        },
    )

    assert response.status_code == 200
    data = response.json()
    command = data["command"]
    task = data["created_task"]

    assert command["status"] == "task_created"
    assert command["created_task_id"] == task["id"]
    assert task["department"] == "development"
    assert task["steps"]


def test_command_history_limit():
    test_world = World()

    for index in range(105):
        test_world.add_command(
            UserCommand(
                raw_text=f"command {index}",
            )
        )

    assert len(test_world.commands) == 100


def test_command_detail_api_shape():
    reset_global_world()
    client = TestClient(app)
    created = client.post(
        "/commands",
        json={
            "text": "проанализируй рынок онлайн-школ",
        },
    ).json()

    command_id = created["command"]["id"]
    detail = client.get(
        f"/commands/{command_id}"
    )

    assert detail.status_code == 200
    data = detail.json()
    assert data["command"]["id"] == command_id
    assert data["created_task"]["department"] == "analytics"
    assert isinstance(data["activity_log"], list)
