from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm.guardrails import LLMGuardrailError
from app.core.llm.reasoning import LLMReasoningService
from app.core.llm.service import LLMService
from app.core.llm.suggestions import SuggestionService
from app.core.runtime_timeline import build_runtime_timeline
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


class TimelineSummaryRequest(BaseModel):
    task_id: str | None = None
    command_id: str | None = None
    agent_id: str | None = None
    limit: int = 30


class SuggestionReviewRequest(BaseModel):
    reviewed_by: str | None = None
    rejection_reason: str | None = None


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


@router.get("/llm/reasoning/diagnostics")
def llm_reasoning_diagnostics():
    return LLMReasoningService(world).diagnostics()


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
        "summary": result["summary"],
        "current_state": result["current_state"],
        "next_best_action": result.get("next_best_action"),
        "provider": result["provider_used"],
        "provider_used": result["provider_used"],
        "safety_flags": result["safety_flags"],
        "fallback_used": result["fallback_used"],
        "fallback_reason": result.get("fallback_reason"),
    }


@router.post("/llm/reasoning/timeline-summary")
def llm_reasoning_timeline_summary(
    request: TimelineSummaryRequest,
):
    timeline = build_runtime_timeline(
        world,
        task_id=request.task_id,
        command_id=request.command_id,
        agent_id=request.agent_id,
        limit=request.limit,
    )["entries"]
    result = LLMReasoningService(world).summarize_timeline(
        entries=[entry["message"] for entry in timeline],
        task_id=request.task_id,
        command_id=request.command_id,
        agent_id=request.agent_id,
    )
    return {
        "summary": result["summary"],
        "key_events": result["key_events"],
        "risks_or_blockers": result["risks_or_blockers"],
        "provider": result["provider_used"],
        "provider_used": result["provider_used"],
        "safety_flags": result["safety_flags"],
        "fallback_used": result["fallback_used"],
        "fallback_reason": result.get("fallback_reason"),
    }


@router.get("/llm/suggestions")
def list_llm_suggestions(
    type: str | None = None,
    status: str | None = None,
    task_id: str | None = None,
    command_id: str | None = None,
    limit: int = 50,
):
    service = SuggestionService(world)
    items = service.list_suggestions(
        suggestion_type=type,
        status=status,
        task_id=task_id,
        command_id=command_id,
        limit=limit,
    )
    return {
        "items": [
            item.model_dump(mode="json") for item in items
        ],
        "total": len(items),
    }


@router.get("/llm/suggestions/{suggestion_id}")
def get_llm_suggestion(
    suggestion_id: str,
):
    suggestion = SuggestionService(world).get_suggestion(
        suggestion_id
    )
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion.model_dump(mode="json")


@router.post("/llm/suggestions/{suggestion_id}/approve")
def approve_llm_suggestion(
    suggestion_id: str,
    request: SuggestionReviewRequest,
):
    try:
        suggestion = SuggestionService(world).approve_suggestion(
            suggestion_id,
            reviewed_by=request.reviewed_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return suggestion.model_dump(mode="json")


@router.post("/llm/suggestions/{suggestion_id}/reject")
def reject_llm_suggestion(
    suggestion_id: str,
    request: SuggestionReviewRequest,
):
    try:
        suggestion = SuggestionService(world).reject_suggestion(
            suggestion_id,
            reviewed_by=request.reviewed_by,
            rejection_reason=request.rejection_reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return suggestion.model_dump(mode="json")


@router.post("/llm/suggestions/{suggestion_id}/apply")
def apply_llm_suggestion(
    suggestion_id: str,
    request: SuggestionReviewRequest,
):
    try:
        result = SuggestionService(world).apply_suggestion(
            suggestion_id,
            reviewed_by=request.reviewed_by,
        )
        suggestion = SuggestionService(world).get_suggestion(
            suggestion_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "suggestion": suggestion.model_dump(mode="json") if suggestion else None,
        "result": result,
    }
