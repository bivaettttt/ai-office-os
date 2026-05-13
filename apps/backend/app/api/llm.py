from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm.guardrails import LLMGuardrailError
from app.core.llm.service import LLMService
from app.core.world import world


router = APIRouter()


class LLMTestRequest(BaseModel):
    prompt: str
    provider: str | None = None
    model: str | None = None


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
