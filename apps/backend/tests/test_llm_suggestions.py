from pathlib import Path

from fastapi.testclient import TestClient

from app.core.llm.suggestions import (
    LLMSuggestionType,
    SuggestionService,
)
from app.core.runtime_metrics import build_runtime_metrics
from app.core.world import World, world
from app.main import app
from app.models.task import Task, TaskStep


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
            "llm_prompt_logs": [],
            "llm_suggestions": [],
        }
    )


def make_task() -> Task:
    task = Task(
        title="Suggestion task",
        description="Suggestion task description",
        department="development",
        steps=[
            TaskStep(
                title="Implement change",
                description="Work on change",
                progress=30,
                status="in_progress",
            )
        ],
    )
    world.add_task(task)
    return task


def test_create_suggestion():
    reset_global_world()
    suggestion = SuggestionService(world).create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        task_id="task-1",
        content="Draft task summary",
        structured_payload={"summary": "Draft task summary"},
        source_provider="mock",
        source_model="mock-safe-model",
    )

    assert suggestion.id
    assert len(world.llm_suggestions) == 1


def test_list_suggestions():
    reset_global_world()
    service = SuggestionService(world)
    service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        task_id="task-1",
        content="Summary A",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    service.create_suggestion(
        suggestion_type=LLMSuggestionType.MANAGER_REVIEW.value,
        task_id="task-2",
        content="Review B",
        source_provider="mock",
        source_model="mock-safe-model",
    )

    items = service.list_suggestions(task_id="task-1")
    assert len(items) == 1
    assert items[0].task_id == "task-1"


def test_approve_suggestion():
    reset_global_world()
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        content="Draft task summary",
        source_provider="mock",
        source_model="mock-safe-model",
    )

    updated = service.approve_suggestion(
        suggestion.id,
        reviewed_by="manager-test",
    )
    assert updated.status == "approved"
    assert updated.reviewed_by == "manager-test"


def test_reject_suggestion():
    reset_global_world()
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        content="Draft task summary",
        source_provider="mock",
        source_model="mock-safe-model",
    )

    updated = service.reject_suggestion(
        suggestion.id,
        reviewed_by="manager-test",
        rejection_reason="Not useful",
    )
    assert updated.status == "rejected"
    assert updated.rejection_reason == "Not useful"


def test_apply_task_summary_suggestion():
    reset_global_world()
    task = make_task()
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        task_id=task.id,
        content="Applied summary",
        structured_payload={"summary": "Applied summary"},
        source_provider="mock",
        source_model="mock-safe-model",
    )

    result = service.apply_suggestion(suggestion.id)
    assert result["applied"] is True
    assert world.tasks[task.id].summary_note == "Applied summary"


def test_apply_manager_review_suggestion():
    reset_global_world()
    task = make_task()
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.MANAGER_REVIEW.value,
        task_id=task.id,
        content="Review draft",
        structured_payload={"review_text": "Review draft"},
        source_provider="mock",
        source_model="mock-safe-model",
    )

    result = service.apply_suggestion(suggestion.id)
    assert result["applied"] is True
    assert world.tasks[task.id].review_draft == "Review draft"


def test_task_plan_suggestion_does_not_replace_active_steps():
    reset_global_world()
    task = make_task()
    original_step_ids = [step.id for step in task.steps]
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_PLAN.value,
        task_id=task.id,
        content="Plan proposal",
        structured_payload={
            "suggested_steps": ["Step A", "Step B"],
            "risks": ["Risk A"],
            "assumptions": ["Assumption A"],
        },
        source_provider="mock",
        source_model="mock-safe-model",
    )

    service.apply_suggestion(suggestion.id)
    assert [step.id for step in world.tasks[task.id].steps] == original_step_ids
    assert world.tasks[task.id].proposed_plan == ["Step A", "Step B"]


def test_command_preview_suggestion_does_not_auto_create_task():
    reset_global_world()
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.COMMAND_PREVIEW.value,
        content="Preview only",
        source_provider="mock",
        source_model="mock-safe-model",
    )

    result = service.apply_suggestion(suggestion.id)
    assert result["applied"] is False
    assert world.tasks == {}


def test_dedupe_behavior():
    reset_global_world()
    service = SuggestionService(world)
    first = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        task_id="task-1",
        content="Same summary",
        structured_payload={"summary": "Same summary"},
        source_provider="mock",
        source_model="mock-safe-model",
    )
    second = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        task_id="task-1",
        content="Same summary",
        structured_payload={"summary": "Same summary"},
        source_provider="mock",
        source_model="mock-safe-model",
    )

    assert first.id == second.id
    assert len(world.llm_suggestions) == 1


def test_persistence_defaults():
    hydrated = World()
    hydrated.hydrate(
        {
            "agents": {},
            "departments": {},
            "tasks": {},
            "events": [],
        }
    )
    assert hydrated.llm_suggestions == []


def test_timeline_events():
    reset_global_world()
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        content="Draft task summary",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    service.approve_suggestion(suggestion.id)
    service.reject_suggestion(suggestion.id, rejection_reason="nope")
    service.expire_suggestion(suggestion.id)

    event_types = [item["type"] for item in world.events]
    assert "llm_suggestion_created" in event_types
    assert "llm_suggestion_approved" in event_types
    assert "llm_suggestion_rejected" in event_types
    assert "llm_suggestion_expired" in event_types


def test_metrics_increments():
    reset_global_world()
    task = make_task()
    service = SuggestionService(world)
    pending = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        task_id=task.id,
        content="Pending summary",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    approved = service.create_suggestion(
        suggestion_type=LLMSuggestionType.MANAGER_REVIEW.value,
        task_id=task.id,
        content="Approved review",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    rejected = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_PLAN.value,
        task_id=task.id,
        content="Rejected plan",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    applied = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TIMELINE_SUMMARY.value,
        task_id=task.id,
        content="Applied timeline",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    service.approve_suggestion(approved.id)
    service.reject_suggestion(rejected.id)
    service.apply_suggestion(applied.id)

    metrics = build_runtime_metrics(world)["global_metrics"]
    assert metrics["llm_suggestions_pending"] == 1
    assert metrics["llm_suggestions_approved_total"] == 1
    assert metrics["llm_suggestions_rejected_total"] == 1
    assert metrics["llm_suggestions_applied_total"] == 1


def test_no_tools_invoked():
    reset_global_world()
    service = SuggestionService(world)
    service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        content="Draft task summary",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    assert world.tool_invocations == {}


def test_no_external_provider_references():
    root = Path(__file__).resolve().parents[3]
    texts = [
        (root / "apps/backend/app/core/llm/suggestions.py").read_text(encoding="utf-8"),
        (root / "apps/backend/app/api/llm.py").read_text(encoding="utf-8"),
    ]
    forbidden_external = "open" + "ai"
    forbidden_variant = "open" + "ai" + "_comp" + "atible"
    joined = "\n".join(texts).lower()
    assert forbidden_external not in joined
    assert forbidden_variant not in joined


def test_suggestions_api_shape():
    reset_global_world()
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        task_id="task-1",
        content="Draft task summary",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    client = TestClient(app)

    listed = client.get("/llm/suggestions")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    detail = client.get(f"/llm/suggestions/{suggestion.id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == suggestion.id

    approved = client.post(
        f"/llm/suggestions/{suggestion.id}/approve",
        json={"reviewed_by": "manager-ui"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


def test_reasoning_creates_task_summary_suggestion(monkeypatch):
    from app.config.settings import settings

    reset_global_world()
    task = make_task()
    monkeypatch.setattr(settings, "LLM_REASONING_ENABLED", True)
    client = TestClient(app)

    response = client.post(
        "/llm/reasoning/task-summary",
        json={"task_id": task.id},
    )
    assert response.status_code == 200
    assert any(
        item.type == LLMSuggestionType.TASK_SUMMARY
        and item.task_id == task.id
        for item in world.llm_suggestions
    )


def test_reasoning_creates_command_preview_suggestion(monkeypatch):
    from app.config.settings import settings

    reset_global_world()
    monkeypatch.setattr(settings, "LLM_REASONING_ENABLED", True)
    client = TestClient(app)

    response = client.post(
        "/commands/preview",
        json={"text": "сделай лендинг для кофейни"},
    )
    assert response.status_code == 200
    assert any(
        item.type == LLMSuggestionType.COMMAND_PREVIEW
        for item in world.llm_suggestions
    )
