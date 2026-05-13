from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm.guardrails import LLMGuardrailError
from app.core.llm.reasoning import LLMReasoningService
from app.core.llm.service import LLMService
from app.core.world import world


router = APIRouter()


class LLMTestRequest(BaseModel):
    prompt: str
    provider: str | None = None
    model: str | None = None


class CommandExplainRequest(BaseModel):
    text: str
    department: str | None = None
    priority: str | None = None


class TaskSummaryRequest(BaseModel):
    task_id: str


@router.get("/llm/status")
def llm_status():
    data = LLMService(world).status().model_dump(mode="json")
    data["model_config"] = data.pop("model_configuration")
    return data


@router.post("/llm/test")
def llm_test(request: LLMTestRequest):
    try:
        response, log_entry_id = LLMService(world).test_prompt(
            prompt=request.prompt,
            provider=request.provider,
            model=request.model,
        )
    except LLMGuardrailError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": str(exc),
                "safety_flags": [
                    flag.value
                    for flag in exc.flags
                ],
            },
        ) from exc

    return {
        "response": response.model_dump(mode="json"),
        "provider_used": response.provider,
        "safety_flags": [
            flag.value
            for flag in response.safety_flags
        ],
        "log_entry_id": log_entry_id,
    }


@router.get("/llm/logs")
def llm_logs(limit: int = 50):
    return {
        "items": [
            entry.model_dump(mode="json")
            for entry in sorted(
                world.llm_prompt_logs,
                key=lambda item: item.timestamp,
                reverse=True,
            )[:limit]
        ],
        "total": len(world.llm_prompt_logs),
    }


@router.get("/llm/reasoning/status")
def llm_reasoning_status():
    return LLMReasoningService(world).status()


@router.post("/llm/reasoning/command-explain")
def llm_reasoning_command_explain(
    request: CommandExplainRequest,
):
    from app.core.commands import route_user_command

    route = route_user_command(
        request.text,
        requested_department=request.department,
        requested_priority=request.priority,
    )
    result = LLMReasoningService(world).explain_command(
        text=request.text,
        department=route.department,
        priority=route.priority,
        capabilities=route.required_capabilities,
        routing_explanation=route.explanation,
    )
    return {
        "rules_routing": route.model_dump(mode="json"),
        "llm_explanation": result["text"],
        "provider_used": result["provider_used"],
        "safety_flags": result["safety_flags"],
        "fallback_used": result["fallback_used"],
    }


@router.post("/llm/reasoning/task-summary")
def llm_reasoning_task_summary(
    request: TaskSummaryRequest,
):
    result = LLMReasoningService(world).summarize_task(
        task_id=request.task_id,
    )
    return {
        "summary": result["text"],
        "provider_used": result["provider_used"],
        "safety_flags": result["safety_flags"],
        "fallback_used": result["fallback_used"],
    }
