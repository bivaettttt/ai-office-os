from fastapi.testclient import TestClient

from app.core.commands import (
    build_command_preview,
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


def test_preview_does_not_create_task():
    reset_global_world()
    client = TestClient(app)

    response = client.post(
        "/commands/preview",
        json={
            "text": "сделай лендинг для кофейни",
        },
    )

    assert response.status_code == 200
    assert world.tasks == {}
    assert world.commands == {}


def test_preview_returns_proposed_task():
    preview = build_command_preview(
        "напиши пост для Telegram"
    )

    assert preview.inferred_department == "content"
    assert preview.proposed_title == (
        "напиши пост для Telegram"
    )
    assert preview.proposed_steps


def test_confidence_score():
    preview = build_command_preview(
        "urgent frontend website"
    )

    assert preview.confidence_score >= 0.7


def test_low_confidence_warning():
    preview = build_command_preview("do")

    assert any(
        warning.code == "low_confidence"
        for warning in preview.warnings
    )
    assert any(
        warning.code == "too_short"
        for warning in preview.warnings
    )


def test_invalid_empty_command():
    client = TestClient(app)
    response = client.post(
        "/commands/preview",
        json={
            "text": "",
        },
    )

    assert response.status_code == 422


def test_department_override_preview():
    preview = build_command_preview(
        "сделай что-нибудь",
        requested_department="operations",
    )

    assert preview.inferred_department == "operations"
    assert preview.confidence_score >= 0.2


def test_priority_override_preview():
    preview = build_command_preview(
        "напиши пост",
        requested_priority="high",
    )

    assert preview.inferred_priority == "high"


def test_edited_title_description_on_create():
    reset_global_world()
    client = TestClient(app)

    response = client.post(
        "/commands",
        json={
            "text": "напиши пост для Telegram",
            "title": "Telegram launch post",
            "description": "Draft a short launch post",
        },
    )

    assert response.status_code == 200
    task = response.json()["created_task"]
    assert task["title"] == "Telegram launch post"
    assert task["description"] == "Draft a short launch post"


def test_failed_command_recovery_shape():
    reset_global_world()
    client = TestClient(app)

    response = client.post(
        "/commands",
        json={
            "text": "hello",
            "department": "unknown",
        },
    )

    assert response.status_code == 400
    command = next(iter(world.commands.values()))
    assert command.status == "failed"
    assert command.error_message


def test_preview_plan_generation():
    response = TestClient(app).post(
        "/commands/preview",
        json={
            "text": "проанализируй рынок онлайн-школ",
        },
    )

    assert response.status_code == 200
    steps = response.json()["preview"]["proposed_steps"]
    assert steps[0]["title"] == "Understand research goal"
