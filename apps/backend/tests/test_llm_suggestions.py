from pathlib import Path

from fastapi.testclient import TestClient

from app.core.llm.suggestions import (
    LLMSuggestionType,
    SuggestionService,
)
from app.core.runtime_metrics import build_runtime_metrics
from app.core.world import World, world
from app.main import app
from app.models.command import UserCommand
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


def test_review_queue_api_shape():
    reset_global_world()
    task = make_task()
    service = SuggestionService(world)
    service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        task_id=task.id,
        content="Queue summary",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    client = TestClient(app)

    response = client.get("/llm/suggestions/review-queue?only_pending=true")
    assert response.status_code == 200
    payload = response.json()
    assert "suggestions" in payload
    assert "counts_by_status" in payload
    assert payload["suggestions"][0]["related_task_summary"]["id"] == task.id


def test_review_queue_filters_and_counts():
    reset_global_world()
    dev_task = make_task()
    analytics_task = Task(
        title="Analytics suggestion task",
        description="Analytics suggestion task description",
        department="analytics",
    )
    world.add_task(analytics_task)
    service = SuggestionService(world)
    service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        task_id=dev_task.id,
        content="Dev summary",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    service.create_suggestion(
        suggestion_type=LLMSuggestionType.MANAGER_REVIEW.value,
        task_id=analytics_task.id,
        content="Analytics review",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    client = TestClient(app)

    response = client.get(
        "/llm/suggestions/review-queue?department=analytics&type=manager_review"
    )
    payload = response.json()
    assert response.status_code == 200
    assert len(payload["suggestions"]) == 1
    assert payload["counts_by_type"]["task_summary"] == 1
    assert payload["counts_by_department"]["analytics"] == 1


def test_expiration_policy_and_bulk_expire(monkeypatch):
    from app.config.settings import settings

    reset_global_world()
    monkeypatch.setattr(settings, "LLM_SUGGESTION_TTL_MINUTES", 1)
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        content="Old summary",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    suggestion.created_at -= 3600
    client = TestClient(app)

    response = client.post("/llm/suggestions/bulk-expire", json={})
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert service.get_suggestion(suggestion.id).status == "expired"


def test_bulk_reject():
    reset_global_world()
    service = SuggestionService(world)
    first = service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        content="A",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    second = service.create_suggestion(
        suggestion_type=LLMSuggestionType.MANAGER_REVIEW.value,
        content="B",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    client = TestClient(app)

    response = client.post(
        "/llm/suggestions/bulk-reject",
        json={
            "ids": [first.id, second.id],
            "rejection_reason": "bulk reject",
            "reviewed_by": "manager-bulk",
        },
    )
    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert service.get_suggestion(first.id).status == "rejected"
    assert service.get_suggestion(second.id).reviewed_by == "manager-bulk"


def test_apply_effect_preview_in_review_queue():
    reset_global_world()
    service = SuggestionService(world)
    service.create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_PLAN.value,
        content="Plan",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    client = TestClient(app)
    response = client.get("/llm/suggestions/review-queue")
    item = response.json()["suggestions"][0]
    assert "without changing active steps" in item["apply_effect_preview"]


def test_promote_command_preview_to_draft_does_not_create_task():
    reset_global_world()
    command = UserCommand(
        raw_text="сделай лендинг для кофейни",
        normalized_text="сделай лендинг для кофейни",
        inferred_department="development",
        inferred_priority="normal",
        inferred_capabilities=["code_generation"],
    )
    world.add_command(command)
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.COMMAND_PREVIEW.value,
        command_id=command.id,
        content="Improved preview",
        structured_payload={
            "improved_title": "Coffee landing page",
            "improved_description": "Build a coffee shop landing page",
            "department": "development",
            "priority": "high",
            "capabilities": ["code_generation"],
            "plan_notes": ["Keep layout simple"],
        },
        source_provider="mock",
        source_model="mock-safe-model",
    )
    client = TestClient(app)
    response = client.post(
        f"/llm/suggestions/{suggestion.id}/promote-command-draft"
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Coffee landing page"
    assert world.tasks == {}


def test_task_drilldown_includes_suggestions():
    reset_global_world()
    task = make_task()
    SuggestionService(world).create_suggestion(
        suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
        task_id=task.id,
        content="Summary",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    client = TestClient(app)
    response = client.get(f"/tasks/{task.id}")
    assert response.status_code == 200
    assert response.json()["suggestions"][0]["task_id"] == task.id


def test_command_drilldown_includes_suggestions():
    reset_global_world()
    command = UserCommand(
        raw_text="напиши пост для Telegram",
        normalized_text="напиши пост для telegram",
        inferred_department="content",
        inferred_priority="normal",
        inferred_capabilities=["content_writing"],
    )
    world.add_command(command)
    SuggestionService(world).create_suggestion(
        suggestion_type=LLMSuggestionType.COMMAND_PREVIEW.value,
        command_id=command.id,
        content="Preview",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    client = TestClient(app)
    response = client.get(f"/commands/{command.id}")
    assert response.status_code == 200
    assert response.json()["suggestions"][0]["command_id"] == command.id


def test_suggestion_governance_metrics_and_timeline():
    reset_global_world()
    service = SuggestionService(world)
    suggestion = service.create_suggestion(
        suggestion_type=LLMSuggestionType.COMMAND_PREVIEW.value,
        content="Preview",
        source_provider="mock",
        source_model="mock-safe-model",
    )
    suggestion.created_at -= 5 * 3600
    service.bulk_expire()
    service.promote_command_draft(suggestion.id)
    client = TestClient(app)
    client.get("/llm/suggestions/review-queue")

    metrics = build_runtime_metrics(world)["global_metrics"]
    assert metrics["llm_suggestions_expired_total"] >= 1
    assert metrics["llm_suggestions_promoted_total"] >= 1
    assert metrics["llm_review_queue_pending_count"] >= 0
    assert metrics["llm_suggestions_oldest_pending_age_seconds"] >= 0

    event_types = [item["type"] for item in world.events]
    assert "llm_suggestion_bulk_expired" in event_types
    assert "llm_suggestion_promoted_to_command_draft" in event_types
    assert "llm_review_queue_viewed" in event_types
