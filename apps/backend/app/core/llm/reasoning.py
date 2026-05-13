from __future__ import annotations

import json

from app.config.settings import settings
from app.core.llm.guardrails import (
    ALLOWED_REASONING_PURPOSES,
    FORBIDDEN_PURPOSES,
    LLMGuardrailError,
)
from app.core.llm.prompts import (
    command_explanation_request,
    command_preview_enhancement_request,
    manager_review_draft_request,
    task_plan_draft_request,
    task_summary_request,
    timeline_summary_request,
)
from app.core.llm.service import LLMService
from app.core.llm.types import LLMSafetyFlag
from app.core.runtime_timeline import build_runtime_timeline
from app.core.world import World


class LLMReasoningService:
    def __init__(
        self,
        world: World,
    ):
        self.world = world
        self.llm = LLMService(world)

    def status(self) -> dict:
        return {
            "reasoning_enabled": settings.LLM_REASONING_ENABLED,
            "provider_status": self.llm.status().model_dump(mode="json"),
            "allowed_purposes": sorted(ALLOWED_REASONING_PURPOSES),
            "blocked_purposes": sorted(FORBIDDEN_PURPOSES),
        }

    def explain_command(
        self,
        *,
        text: str,
        department: str,
        priority: str,
        capabilities: list[str],
        routing_explanation: str,
    ) -> dict:
        if not settings.LLM_REASONING_ENABLED:
            return self._fallback(
                text=routing_explanation,
                reason="reasoning_disabled",
            )

        request = command_explanation_request(
            text=text,
            department=department,
            priority=priority,
            capabilities=capabilities,
            routing_explanation=routing_explanation,
        )
        return self._run_text_reasoning(
            request=request,
            fallback_text=routing_explanation,
        )

    def enhance_command_preview(
        self,
        *,
        text: str,
        current_title: str,
        current_description: str,
        current_plan: list[str],
    ) -> dict:
        if not settings.LLM_REASONING_ENABLED:
            return {
                "improved_title": current_title,
                "improved_description": current_description,
                "plan_notes": "",
                "provider_used": "rules",
                "safety_flags": [],
                "fallback_used": True,
            }

        request = command_preview_enhancement_request(
            text=text,
            current_title=current_title,
            current_description=current_description,
            current_plan=current_plan,
        )
        return self._run_json_reasoning(
            request=request,
            fallback={
                "improved_title": current_title,
                "improved_description": current_description,
                "plan_notes": "",
            },
        )

    def draft_task_plan(
        self,
        *,
        title: str,
        department: str,
        capabilities: list[str],
        current_plan: list[str],
    ) -> dict:
        if not settings.LLM_REASONING_ENABLED:
            return {
                "suggested_steps": current_plan,
                "provider_used": "rules",
                "safety_flags": [],
                "fallback_used": True,
            }

        request = task_plan_draft_request(
            title=title,
            department=department,
            capabilities=capabilities,
            current_plan=current_plan,
        )
        return self._run_json_reasoning(
            request=request,
            fallback={
                "suggested_steps": current_plan,
            },
        )

    def draft_manager_review(
        self,
        *,
        task_title: str,
        steps: list[str],
        agent_name: str,
        result_summary: str,
    ) -> dict:
        if not settings.LLM_REASONING_ENABLED:
            return self._fallback(
                text=result_summary,
                reason="reasoning_disabled",
            )

        request = manager_review_draft_request(
            task_title=task_title,
            steps=steps,
            agent_name=agent_name,
            result_summary=result_summary,
        )
        return self._run_text_reasoning(
            request=request,
            fallback_text=result_summary,
        )

    def summarize_task(
        self,
        *,
        task_id: str,
    ) -> dict:
        task = self.world.tasks.get(task_id)
        if task is None:
            raise ValueError("Task not found")

        timeline = build_runtime_timeline(
            self.world,
            task_id=task_id,
            limit=20,
        )["entries"]
        fallback_text = (
            task.result_summary
            or f"{task.title}: {task.status} at {task.progress}%."
        )

        if not settings.LLM_REASONING_ENABLED:
            return self._fallback(
                text=fallback_text,
                reason="reasoning_disabled",
            )

        request = task_summary_request(
            task_title=task.title,
            status=task.status,
            steps=[step.title for step in task.steps],
            timeline_highlights=[
                entry["message"] for entry in timeline
            ],
            task_id=task.id,
        )
        return self._run_text_reasoning(
            request=request,
            fallback_text=fallback_text,
        )

    def summarize_timeline(
        self,
        *,
        entries: list[str],
    ) -> dict:
        if not settings.LLM_REASONING_ENABLED:
            return self._fallback(
                text="; ".join(entries[:4]),
                reason="reasoning_disabled",
            )

        request = timeline_summary_request(entries=entries)
        return self._run_text_reasoning(
            request=request,
            fallback_text="; ".join(entries[:4]),
        )

    def _run_text_reasoning(
        self,
        *,
        request,
        fallback_text: str,
    ) -> dict:
        self.world.add_event(
            "llm_reasoning_started",
            {"purpose": request.purpose},
        )
        try:
            response, _ = self.llm.complete(request)
            fallback_used = (
                LLMSafetyFlag.PROVIDER_FALLBACK_USED
                in response.safety_flags
            )
            self.world.add_event(
                "llm_reasoning_completed",
                {
                    "purpose": request.purpose,
                    "provider": response.provider,
                },
            )
            if fallback_used:
                self.world.add_event(
                    "llm_reasoning_fallback_used",
                    {
                        "purpose": request.purpose,
                        "provider": response.provider,
                    },
                )
            return {
                "text": response.content,
                "provider_used": response.provider,
                "safety_flags": [
                    flag.value for flag in response.safety_flags
                ],
                "fallback_used": fallback_used,
            }
        except LLMGuardrailError as exc:
            self.world.add_event(
                "llm_reasoning_blocked",
                {
                    "purpose": request.purpose,
                    "error": str(exc),
                },
            )
            return {
                "text": fallback_text,
                "provider_used": "rules",
                "safety_flags": [
                    flag.value for flag in exc.flags
                ],
                "fallback_used": True,
            }
        except Exception:
            self.world.add_event(
                "llm_reasoning_fallback_used",
                {"purpose": request.purpose},
            )
            return self._fallback(
                text=fallback_text,
                reason="provider_failed",
            )

    def _run_json_reasoning(
        self,
        *,
        request,
        fallback: dict,
    ) -> dict:
        self.world.add_event(
            "llm_reasoning_started",
            {"purpose": request.purpose},
        )
        try:
            response, _ = self.llm.complete(request)
            fallback_used = (
                LLMSafetyFlag.PROVIDER_FALLBACK_USED
                in response.safety_flags
            )
            parsed, invalid_json = safe_json_parse(response.content)
            if invalid_json:
                self.world.add_event(
                    "llm_reasoning_fallback_used",
                    {
                        "purpose": request.purpose,
                        "reason": "invalid_json",
                    },
                )
                return {
                    **fallback,
                    "provider_used": response.provider,
                    "safety_flags": [
                        *[
                            flag.value
                            for flag in response.safety_flags
                        ],
                        LLMSafetyFlag.INVALID_JSON_FALLBACK.value,
                    ],
                    "fallback_used": True,
                }

            self.world.add_event(
                "llm_reasoning_completed",
                {
                    "purpose": request.purpose,
                    "provider": response.provider,
                },
            )
            if fallback_used:
                self.world.add_event(
                    "llm_reasoning_fallback_used",
                    {
                        "purpose": request.purpose,
                        "provider": response.provider,
                    },
                )
            return {
                **fallback,
                **parsed,
                "provider_used": response.provider,
                "safety_flags": [
                    flag.value for flag in response.safety_flags
                ],
                "fallback_used": fallback_used,
            }
        except LLMGuardrailError as exc:
            self.world.add_event(
                "llm_reasoning_blocked",
                {
                    "purpose": request.purpose,
                    "error": str(exc),
                },
            )
            return {
                **fallback,
                "provider_used": "rules",
                "safety_flags": [
                    flag.value for flag in exc.flags
                ],
                "fallback_used": True,
            }
        except Exception:
            self.world.add_event(
                "llm_reasoning_fallback_used",
                {"purpose": request.purpose},
            )
            return {
                **fallback,
                "provider_used": "rules",
                "safety_flags": [],
                "fallback_used": True,
            }

    def _fallback(
        self,
        *,
        text: str,
        reason: str,
    ) -> dict:
        return {
            "text": text,
            "provider_used": "rules",
            "safety_flags": [],
            "fallback_used": True,
            "fallback_reason": reason,
        }


def safe_json_parse(
    value: str,
) -> tuple[dict, bool]:
    try:
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed, False
    except Exception:
        pass
    return {}, True
