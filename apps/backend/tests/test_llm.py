import pytest
from pathlib import Path

from fastapi.testclient import TestClient

from app.config.settings import settings
from app.core.agent_runtime.execution import (
    review_completed_task,
)
from app.core.llm.guardrails import (
    LLMGuardrailError,
    redact_text,
)
from app.core.llm.mock_provider import MockProvider
from app.core.llm.reasoning import LLMReasoningService
from app.core.llm.service import LLMService
from app.core.llm.types import (
    LLMMessage,
    LLMMessageRole,
    LLMRequest,
    LLMResponse,
    LLMSafetyFlag,
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
        }
    )
    LLMReasoningService._request_timestamps.clear()
    LLMReasoningService._purpose_timestamps.clear()
    LLMReasoningService._cache.clear()
    LLMReasoningService._recent_rate_limited.clear()
    LLMReasoningService._recent_schema_failures.clear()
    LLMReasoningService._recent_fallbacks.clear()


def make_request(
    prompt: str,
    purpose: str = "test",
) -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(
                role=LLMMessageRole.USER,
                content=prompt,
            )
        ],
        purpose=purpose,
    )


def test_mock_provider_response():
    response = MockProvider().complete(
        make_request("hello")
    )

    assert response.provider == "mock"
    assert "hello" in response.content


def test_selected_provider_fallback_to_mock():
    test_world = World()
    response, _ = LLMService(
        test_world,
        provider_override="ollama",
    ).complete(make_request("hello"))

    assert response.provider == "mock"
    assert (
        LLMSafetyFlag.PROVIDER_FALLBACK_USED
        in response.safety_flags
    )


def test_real_calls_disabled_behavior():
    test_world = World()
    response, _ = LLMService(test_world).complete(
        make_request("hello")
    )

    assert response.provider == "mock"
    assert (
        LLMSafetyFlag.REAL_CALLS_DISABLED
        in response.safety_flags
    )


def test_guardrail_empty_prompt():
    with pytest.raises(LLMGuardrailError) as exc:
        LLMService(World()).complete(make_request(""))

    assert (
        LLMSafetyFlag.EMPTY_PROMPT_BLOCKED
        in exc.value.flags
    )


def test_guardrail_max_length():
    with pytest.raises(LLMGuardrailError) as exc:
        LLMService(World()).complete(
            make_request(
                "x" * (settings.LLM_MAX_PROMPT_CHARS + 1)
            )
        )

    assert (
        LLMSafetyFlag.PROMPT_TOO_LONG_BLOCKED
        in exc.value.flags
    )


def test_secret_redaction():
    redacted = redact_text(
        "LOCAL_" + "API" + "_KEY=abc sk-secret token=abc password=abc"
    )

    assert "sk-secret" not in redacted
    assert "token=abc" not in redacted
    assert "password=abc" not in redacted
    assert "[REDACTED]" in redacted


def test_block_tool_execution_purpose():
    with pytest.raises(LLMGuardrailError) as exc:
        LLMService(World()).complete(
            make_request(
                "run tool",
                purpose="tool_execution",
            )
        )

    assert (
        LLMSafetyFlag.TOOL_EXECUTION_BLOCKED
        in exc.value.flags
    )


def test_prompt_log_entry_created():
    test_world = World()
    response, log_entry_id = LLMService(test_world).complete(
        make_request("hello " + "API" + "_KEY=secret")
    )

    assert log_entry_id
    assert response.provider == "mock"
    assert len(test_world.llm_prompt_logs) == 1
    assert "[REDACTED]" in test_world.llm_prompt_logs[0].prompt_preview
    assert (
        LLMSafetyFlag.SECRET_REDACTED
        in test_world.llm_prompt_logs[0].safety_flags
    )


def test_llm_status_api_shape():
    reset_global_world()
    response = TestClient(app).get("/llm/status")

    assert response.status_code == 200
    data = response.json()
    assert data["selected_provider"] == "mock"
    assert data["active_provider"] == "mock"
    assert "providers" in data
    assert "ollama_base_url" in data["model_config"]
    assert {item["name"] for item in data["providers"]} == {
        "mock",
        "ollama",
    }


def test_allowed_providers_only_mock_and_ollama():
    data = TestClient(app).get("/llm/status").json()

    assert {item["name"] for item in data["providers"]} == {
        "mock",
        "ollama",
    }


def test_unknown_provider_falls_back_to_mock():
    test_world = World()
    response, _ = LLMService(
        test_world,
        provider_override="unknown",
    ).complete(make_request("hello"))

    assert response.provider == "mock"


def test_settings_do_not_require_external_keys():
    assert settings.LLM_PROVIDER in {"mock", "ollama"}
    assert hasattr(settings, "OLLAMA_BASE_URL")
    assert not hasattr(settings, "OPEN" + "AI_COMPATIBLE_API" + "_KEY")


def test_llm_test_api_uses_mock_by_default():
    reset_global_world()
    response = TestClient(app).post(
        "/llm/test",
        json={
            "prompt": "hello",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider_used"] == "mock"
    assert data["log_entry_id"]


def test_llm_logs_api_shape():
    reset_global_world()
    client = TestClient(app)
    client.post(
        "/llm/test",
        json={
            "prompt": "hello",
        },
    )

    response = client.get("/llm/logs")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["provider"] == "mock"


def test_reasoning_status_api():
    reset_global_world()
    response = TestClient(app).get(
        "/llm/reasoning/status"
    )

    assert response.status_code == 200
    data = response.json()
    assert "reasoning_enabled" in data
    assert "provider_status" in data
    assert "command_explanation" in data["allowed_purposes"]
    assert "tool_execution" in data["blocked_purposes"]


def test_command_explanation_uses_mock_by_default(
    monkeypatch,
):
    reset_global_world()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )
    monkeypatch.setattr(
        settings,
        "LLM_PROVIDER",
        "mock",
    )

    response = TestClient(app).post(
        "/llm/reasoning/command-explain",
        json={"text": "сделай лендинг для кофейни"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider_used"] == "mock"
    assert data["llm_explanation"]


def test_ollama_unavailable_reasoning_falls_back_to_mock(
    monkeypatch,
):
    reset_global_world()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )
    monkeypatch.setattr(
        settings,
        "LLM_PROVIDER",
        "ollama",
    )

    response = TestClient(app).post(
        "/llm/reasoning/command-explain",
        json={"text": "проанализируй рынок"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider_used"] == "mock"
    assert data["fallback_used"] is True


def test_invalid_json_fallback(
    monkeypatch,
):
    reset_global_world()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )

    original_complete = MockProvider.complete

    def broken_complete(self, request):
        if request.purpose == "command_preview_enhancement":
            return LLMResponse(
                content="{invalid",
                provider="mock",
                model=self.default_model(),
            )
        return original_complete(self, request)

    monkeypatch.setattr(
        MockProvider,
        "complete",
        broken_complete,
    )

    response = TestClient(app).post(
        "/commands/preview",
        json={"text": "сделай лендинг для кофейни"},
    )

    assert response.status_code == 200
    preview = response.json()["preview"]
    assert preview["ai_improved_title"] == preview["proposed_title"]
    assert "invalid_json_fallback" in preview["llm_safety_flags"]


def test_schema_missing_fields_fallback(
    monkeypatch,
):
    reset_global_world()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )

    original_complete = MockProvider.complete

    def missing_fields(self, request):
        if request.purpose == "command_preview_enhancement":
            return LLMResponse(
                content='{"improved_title":"Only title"}',
                provider="mock",
                model=self.default_model(),
            )
        return original_complete(self, request)

    monkeypatch.setattr(
        MockProvider,
        "complete",
        missing_fields,
    )

    response = TestClient(app).post(
        "/commands/preview",
        json={"text": "сделай лендинг для кофейни"},
    )

    assert response.status_code == 200
    preview = response.json()["preview"]
    assert "schema_validation_failed" in preview["llm_safety_flags"]


def test_manager_review_draft_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )

    def broken_review(*args, **kwargs):
        raise RuntimeError("reasoning failed")

    monkeypatch.setattr(
        LLMReasoningService,
        "draft_manager_review",
        broken_review,
    )

    task = Task(
        title="Review test",
        description="Review test description",
        department="development",
        steps=[
            TaskStep(
                title="Understand request",
                description="",
                status="completed",
                progress=100,
            )
        ],
    )
    summary = review_completed_task(task, "Agent One")

    assert "Task completed by Agent One." in summary


def test_task_summary_endpoint(
    monkeypatch,
):
    reset_global_world()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )

    task = Task(
        title="Summary test",
        description="Summary test description",
        department="analytics",
        status="in_progress",
        progress=60,
        steps=[
            TaskStep(
                title="Collect sources",
                description="",
                status="in_progress",
                progress=60,
            )
        ],
    )
    world.add_task(task)

    response = TestClient(app).post(
        "/llm/reasoning/task-summary",
        json={"task_id": task.id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]
    assert data["current_state"]
    assert data["provider_used"] == "mock"


def test_timeline_summary_endpoint(
    monkeypatch,
):
    reset_global_world()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )
    world.add_event("command_routed", {"command_id": "c1"})
    world.add_event("task_completed", {"task_id": "t1"})

    response = TestClient(app).post(
        "/llm/reasoning/timeline-summary",
        json={"limit": 10},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]
    assert isinstance(data["key_events"], list)
    assert isinstance(data["risks_or_blockers"], list)


def test_prompt_log_created_with_reasoning_purpose(
    monkeypatch,
):
    test_world = World()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )
    result = LLMReasoningService(test_world).explain_command(
        text="напиши пост",
        department="content",
        priority="normal",
        capabilities=["content_writing"],
        routing_explanation="Detected content intent.",
    )

    assert result["provider_used"] == "mock"
    assert len(test_world.llm_prompt_logs) == 1
    assert (
        test_world.llm_prompt_logs[0].purpose
        == "command_explanation"
    )


def test_reasoning_metrics_increment(
    monkeypatch,
):
    test_world = World()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )
    LLMReasoningService(test_world).explain_command(
        text="проанализируй рынок",
        department="analytics",
        priority="normal",
        capabilities=["data_analysis"],
        routing_explanation="Detected analytics intent.",
    )

    metrics = build_runtime_metrics(test_world)
    assert (
        metrics["global_metrics"]["llm_reasoning_requests_total"]
        == 1
    )


def test_reasoning_rate_limit_fallback(
    monkeypatch,
):
    reset_global_world()
    test_world = World()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_RATE_LIMIT_PER_MINUTE",
        1,
    )
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_RATE_LIMIT_PER_PURPOSE",
        1,
    )
    service = LLMReasoningService(test_world)

    first = service.enhance_command_preview(
        text="сделай лендинг",
        current_title="A",
        current_description="B",
        current_plan=["One"],
    )
    second = service.enhance_command_preview(
        text="сделай лендинг v2",
        current_title="A2",
        current_description="B2",
        current_plan=["One"],
    )

    assert first["provider_used"] == "mock"
    assert second["provider_used"] == "rules"
    assert "rate_limited" in second["safety_flags"]


def test_reasoning_cache_hit(
    monkeypatch,
):
    reset_global_world()
    test_world = World()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )
    service = LLMReasoningService(test_world)

    first = service.explain_command(
        text="напиши пост",
        department="content",
        priority="normal",
        capabilities=["content_writing"],
        routing_explanation="Detected content intent.",
    )
    second = service.explain_command(
        text="напиши пост",
        department="content",
        priority="normal",
        capabilities=["content_writing"],
        routing_explanation="Detected content intent.",
    )

    assert first["text"] == second["text"]
    assert any(
        event["type"] == "llm_reasoning_cache_hit"
        for event in test_world.events
    )


def test_reasoning_diagnostics_api_shape(
    monkeypatch,
):
    reset_global_world()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )
    response = TestClient(app).get(
        "/llm/reasoning/diagnostics"
    )

    assert response.status_code == 200
    data = response.json()
    assert "cache_size" in data
    assert "rate_limit_settings" in data
    assert "recent_rate_limited_count" in data


def test_reasoning_metrics_schema_and_cache_counts(
    monkeypatch,
):
    reset_global_world()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )
    world.add_event("llm_reasoning_cache_hit", {"purpose": "task_summary"})
    world.add_event(
        "llm_reasoning_schema_validation_failed",
        {"purpose": "command_preview_enhancement"},
    )
    world.add_event(
        "llm_reasoning_rate_limited",
        {"purpose": "timeline_summary"},
    )

    metrics = build_runtime_metrics(world)
    global_metrics = metrics["global_metrics"]
    assert global_metrics["llm_reasoning_cache_hits_total"] == 1
    assert global_metrics["llm_reasoning_schema_failures_total"] == 1
    assert global_metrics["llm_reasoning_rate_limited_total"] == 1


def test_reasoning_does_not_invoke_tools(
    monkeypatch,
):
    test_world = World()
    monkeypatch.setattr(
        settings,
        "LLM_REASONING_ENABLED",
        True,
    )
    LLMReasoningService(test_world).explain_command(
        text="сделай лендинг",
        department="development",
        priority="normal",
        capabilities=["code_generation"],
        routing_explanation="Detected development intent.",
    )

    assert test_world.tool_invocations == {}


def test_no_external_provider_references_in_llm_layer():
    root = Path(__file__).resolve().parents[3]
    files = [
        root / "apps/backend/app/core/llm",
        root / "apps/backend/app/api/llm.py",
        root / ".env.example",
        root / "README.md",
    ]
    forbidden_external = "open" + "ai"
    forbidden_variant = "open" + "ai" + "_comp" + "atible"
    for target in files:
        if target.is_dir():
            texts = [
                path.read_text(encoding="utf-8")
                for path in target.rglob("*.py")
            ]
        else:
            texts = [target.read_text(encoding="utf-8")]
        joined = "\n".join(texts).lower()
        assert forbidden_external not in joined
        assert forbidden_variant not in joined
