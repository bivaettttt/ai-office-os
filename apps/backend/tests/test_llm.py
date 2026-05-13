import pytest

from fastapi.testclient import TestClient

from app.config.settings import settings
from app.core.llm.guardrails import (
    LLMGuardrailError,
    redact_text,
)
from app.core.llm.mock_provider import MockProvider
from app.core.llm.service import LLMService
from app.core.llm.types import (
    LLMMessage,
    LLMMessageRole,
    LLMRequest,
    LLMSafetyFlag,
)
from app.core.world import World, world
from app.main import app


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
