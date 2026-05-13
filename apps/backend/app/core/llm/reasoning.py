from __future__ import annotations

import hashlib
import json
import time

from collections import defaultdict, deque
from typing import Any

from pydantic import BaseModel, ValidationError

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
from app.core.llm.suggestions import (
    LLMSuggestionStatus,
    LLMSuggestionType,
    SuggestionService,
)
from app.core.llm.types import (
    CommandPreviewEnhancement,
    LLMReasoningDiagnostics,
    LLMSafetyFlag,
    ManagerReviewDraft,
    TaskPlanDraft,
    TaskSummaryResult,
    TimelineSummaryResult,
)
from app.core.runtime_timeline import build_runtime_timeline
from app.core.world import World


class LLMReasoningService:
    _request_timestamps: deque[float] = deque()
    _purpose_timestamps: dict[str, deque[float]] = defaultdict(deque)
    _cache: dict[str, dict[str, Any]] = {}
    _recent_rate_limited: deque[float] = deque()
    _recent_schema_failures: deque[float] = deque()
    _recent_fallbacks: deque[float] = deque()

    def __init__(
        self,
        world: World,
    ):
        self.world = world
        self.llm = LLMService(world)
        self.suggestions = SuggestionService(world)

    def status(self) -> dict:
        return {
            "reasoning_enabled": settings.LLM_REASONING_ENABLED,
            "provider_status": self.llm.status().model_dump(mode="json"),
            "allowed_purposes": sorted(ALLOWED_REASONING_PURPOSES),
            "blocked_purposes": sorted(FORBIDDEN_PURPOSES),
        }

    def diagnostics(self) -> dict:
        self._prune_runtime_state()
        return LLMReasoningDiagnostics(
            reasoning_enabled=settings.LLM_REASONING_ENABLED,
            allowed_purposes=sorted(ALLOWED_REASONING_PURPOSES),
            blocked_purposes=sorted(FORBIDDEN_PURPOSES),
            cache_size=len(self._cache),
            rate_limit_settings={
                "per_minute": settings.LLM_REASONING_RATE_LIMIT_PER_MINUTE,
                "per_purpose": settings.LLM_REASONING_RATE_LIMIT_PER_PURPOSE,
                "cache_ttl_seconds": settings.LLM_REASONING_CACHE_TTL_SECONDS,
            },
            recent_rate_limited_count=len(self._recent_rate_limited),
            recent_schema_failures_count=len(self._recent_schema_failures),
            recent_fallbacks_count=len(self._recent_fallbacks),
        ).model_dump(mode="json")

    def explain_command(
        self,
        *,
        text: str,
        department: str,
        priority: str,
        capabilities: list[str],
        routing_explanation: str,
    ) -> dict:
        fallback = self._fallback_text(
            text=routing_explanation,
            reason="reasoning_disabled",
        )
        if not settings.LLM_REASONING_ENABLED:
            return fallback

        request = command_explanation_request(
            text=text,
            department=department,
            priority=priority,
            capabilities=capabilities,
            routing_explanation=routing_explanation,
        )
        return self._run_text_reasoning(
            request=request,
            fallback=fallback,
            cache_input=json.dumps(
                {
                    "text": text,
                    "department": department,
                    "priority": priority,
                    "capabilities": capabilities,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )

    def enhance_command_preview(
        self,
        *,
        text: str,
        current_title: str,
        current_description: str,
        current_plan: list[str],
    ) -> dict:
        fallback = self._fallback_structured(
            {
                "improved_title": current_title,
                "improved_description": current_description,
                "plan_notes": [],
                "confidence_note": None,
            },
            reason="reasoning_disabled",
        )
        if not settings.LLM_REASONING_ENABLED:
            return fallback

        request = command_preview_enhancement_request(
            text=text,
            current_title=current_title,
            current_description=current_description,
            current_plan=current_plan,
        )
        return self._run_structured_reasoning(
            request=request,
            schema=CommandPreviewEnhancement,
            fallback=fallback,
            suggestion_type=LLMSuggestionType.COMMAND_PREVIEW.value,
        )

    def draft_task_plan(
        self,
        *,
        title: str,
        department: str,
        capabilities: list[str],
        current_plan: list[str],
    ) -> dict:
        fallback = self._fallback_structured(
            {
                "suggested_steps": current_plan,
                "risks": [],
                "assumptions": [],
            },
            reason="reasoning_disabled",
        )
        if not settings.LLM_REASONING_ENABLED:
            return fallback

        request = task_plan_draft_request(
            title=title,
            department=department,
            capabilities=capabilities,
            current_plan=current_plan,
        )
        return self._run_structured_reasoning(
            request=request,
            schema=TaskPlanDraft,
            fallback=fallback,
            suggestion_type=LLMSuggestionType.TASK_PLAN.value,
        )

    def draft_manager_review(
        self,
        *,
        task_title: str,
        steps: list[str],
        agent_name: str,
        result_summary: str,
        task_id: str | None = None,
    ) -> dict:
        fallback = self._fallback_structured(
            {
                "review_text": result_summary,
                "quality_notes": [],
                "approval_recommendation": "approve",
            },
            reason="reasoning_disabled",
        )
        if not settings.LLM_REASONING_ENABLED:
            return fallback

        request = manager_review_draft_request(
            task_title=task_title,
            steps=steps,
            agent_name=agent_name,
            result_summary=result_summary,
        )
        return self._run_structured_reasoning(
            request=request,
            schema=ManagerReviewDraft,
            fallback=fallback,
            suggestion_type=LLMSuggestionType.MANAGER_REVIEW.value,
            suggestion_task_id=task_id,
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
        fallback = self._fallback_structured(
            {
                "summary": (
                    task.result_summary
                    or f"{task.title}: {task.status} at {task.progress}%."
                ),
                "current_state": (
                    f"Task is {task.status} with runtime phase "
                    f"{task.runtime_phase}."
                ),
                "next_best_action": (
                    "Review completion"
                    if task.status == "completed"
                    else "Continue the current controlled workflow"
                ),
            },
            reason="reasoning_disabled",
        )

        if not settings.LLM_REASONING_ENABLED:
            return fallback

        request = task_summary_request(
            task_title=task.title,
            status=task.status,
            steps=[step.title for step in task.steps],
            timeline_highlights=[
                entry["message"] for entry in timeline
            ],
            task_id=task.id,
        )
        return self._run_structured_reasoning(
            request=request,
            schema=TaskSummaryResult,
            fallback=fallback,
            suggestion_type=LLMSuggestionType.TASK_SUMMARY.value,
            suggestion_task_id=task.id,
            cache_input=json.dumps(
                {
                    "task_id": task.id,
                    "status": task.status,
                    "progress": task.progress,
                    "steps": [
                        {
                            "title": step.title,
                            "status": step.status,
                            "progress": step.progress,
                        }
                        for step in task.steps
                    ],
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )

    def summarize_timeline(
        self,
        *,
        entries: list[str],
        task_id: str | None = None,
        command_id: str | None = None,
        agent_id: str | None = None,
    ) -> dict:
        fallback = self._fallback_structured(
            {
                "summary": "; ".join(entries[:4]),
                "key_events": entries[:3],
                "risks_or_blockers": [],
            },
            reason="reasoning_disabled",
        )
        if not settings.LLM_REASONING_ENABLED:
            return fallback

        request = timeline_summary_request(entries=entries)
        result = self._run_structured_reasoning(
            request=request,
            schema=TimelineSummaryResult,
            fallback=fallback,
            suggestion_type=LLMSuggestionType.TIMELINE_SUMMARY.value,
            suggestion_task_id=task_id,
            suggestion_command_id=command_id,
            suggestion_agent_id=agent_id,
            cache_input=json.dumps(
                {
                    "task_id": task_id,
                    "command_id": command_id,
                    "agent_id": agent_id,
                    "entries": entries[:12],
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )
        self.world.add_event(
            "llm_timeline_summary_generated",
            {
                "task_id": task_id,
                "command_id": command_id,
                "agent_id": agent_id,
                "provider": result["provider_used"],
            },
        )
        return result

    def _run_text_reasoning(
        self,
        *,
        request,
        fallback: dict,
        cache_input: str | None = None,
    ) -> dict:
        cache_key = self._cache_key(request.purpose, cache_input)
        if cache_key:
            cached = self._get_cache(cache_key)
            if cached is not None:
                self.world.add_event(
                    "llm_reasoning_cache_hit",
                    {"purpose": request.purpose},
                )
                return cached

        rate_limited = self._check_rate_limit(request.purpose)
        if rate_limited:
            return self._rate_limited_fallback(
                request.purpose,
                fallback,
            )

        self.world.add_event(
            "llm_reasoning_started",
            {"purpose": request.purpose},
        )
        try:
            response, _ = self.llm.complete(request)
            result = {
                "text": response.content,
                "provider_used": response.provider,
                "model_used": response.model,
                "safety_flags": [
                    flag.value for flag in response.safety_flags
                ],
                "fallback_used": (
                    LLMSafetyFlag.PROVIDER_FALLBACK_USED
                    in response.safety_flags
                ),
                "fallback_reason": None,
            }
            self.world.add_event(
                "llm_reasoning_completed",
                {
                    "purpose": request.purpose,
                    "provider": response.provider,
                },
            )
            if result["fallback_used"]:
                self._record_fallback()
                self.world.add_event(
                    "llm_reasoning_fallback_used",
                    {
                        "purpose": request.purpose,
                        "provider": response.provider,
                        "reason": "provider_fallback",
                    },
                )
            if cache_key:
                self._put_cache(cache_key, result)
            return result
        except LLMGuardrailError as exc:
            self.world.add_event(
                "llm_reasoning_blocked",
                {
                    "purpose": request.purpose,
                    "error": str(exc),
                },
            )
            self._record_fallback()
            return {
                **fallback,
                "safety_flags": [
                    flag.value for flag in exc.flags
                ],
                "fallback_used": True,
                "fallback_reason": "guardrail_blocked",
            }
        except Exception:
            self._record_fallback()
            self.world.add_event(
                "llm_reasoning_fallback_used",
                {
                    "purpose": request.purpose,
                    "reason": "provider_failed",
                },
            )
            return {
                **fallback,
                "fallback_used": True,
                "fallback_reason": "provider_failed",
            }

    def _run_structured_reasoning(
        self,
        *,
        request,
        schema: type[BaseModel],
        fallback: dict,
        suggestion_type: str | None = None,
        suggestion_task_id: str | None = None,
        suggestion_command_id: str | None = None,
        suggestion_agent_id: str | None = None,
        cache_input: str | None = None,
    ) -> dict:
        cache_key = self._cache_key(request.purpose, cache_input)
        if cache_key:
            cached = self._get_cache(cache_key)
            if cached is not None:
                self.world.add_event(
                    "llm_reasoning_cache_hit",
                    {"purpose": request.purpose},
                )
                return cached

        rate_limited = self._check_rate_limit(request.purpose)
        if rate_limited:
            return self._rate_limited_fallback(
                request.purpose,
                fallback,
            )

        self.world.add_event(
            "llm_reasoning_started",
            {"purpose": request.purpose},
        )
        try:
            response, _ = self.llm.complete(request)
            parsed, json_valid = safe_json_parse(response.content)
            if not json_valid:
                return self._schema_fallback(
                    request.purpose,
                    fallback=fallback,
                    provider=response.provider,
                    safety_flags=[
                        *[
                            flag.value
                            for flag in response.safety_flags
                        ],
                        LLMSafetyFlag.INVALID_JSON_FALLBACK.value,
                        LLMSafetyFlag.SCHEMA_VALIDATION_FAILED.value,
                    ],
                    reason="invalid_json",
                )

            try:
                validated = schema.model_validate(parsed)
            except ValidationError:
                return self._schema_fallback(
                    request.purpose,
                    fallback=fallback,
                    provider=response.provider,
                    safety_flags=[
                        *[
                            flag.value
                            for flag in response.safety_flags
                        ],
                        LLMSafetyFlag.SCHEMA_VALIDATION_FAILED.value,
                    ],
                    reason="schema_validation_failed",
                )

            result = {
                **validated.model_dump(mode="json"),
                "provider_used": response.provider,
                "model_used": response.model,
                "safety_flags": [
                    flag.value for flag in response.safety_flags
                ],
                "fallback_used": (
                    LLMSafetyFlag.PROVIDER_FALLBACK_USED
                    in response.safety_flags
                ),
                "fallback_reason": None,
            }
            self.world.add_event(
                "llm_reasoning_completed",
                {
                    "purpose": request.purpose,
                    "provider": response.provider,
                },
            )
            if result["fallback_used"]:
                self._record_fallback()
                self.world.add_event(
                    "llm_reasoning_fallback_used",
                    {
                        "purpose": request.purpose,
                        "provider": response.provider,
                        "reason": "provider_fallback",
                    },
                )
            if cache_key:
                self._put_cache(cache_key, result)
            suggestion_id = self._maybe_create_suggestion(
                suggestion_type=suggestion_type,
                result=result,
                task_id=suggestion_task_id or request.task_id,
                command_id=suggestion_command_id or request.command_id,
                agent_id=suggestion_agent_id or request.agent_id,
            )
            if suggestion_id:
                result["suggestion_id"] = suggestion_id
            return result
        except LLMGuardrailError as exc:
            self.world.add_event(
                "llm_reasoning_blocked",
                {
                    "purpose": request.purpose,
                    "error": str(exc),
                },
            )
            self._record_fallback()
            return {
                **fallback,
                "safety_flags": [
                    flag.value for flag in exc.flags
                ],
                "fallback_used": True,
                "fallback_reason": "guardrail_blocked",
            }
        except Exception:
            self._record_fallback()
            self.world.add_event(
                "llm_reasoning_fallback_used",
                {
                    "purpose": request.purpose,
                    "reason": "provider_failed",
                },
            )
            return {
                **fallback,
                "fallback_used": True,
                "fallback_reason": "provider_failed",
            }

    def _schema_fallback(
        self,
        purpose: str,
        *,
        fallback: dict,
        provider: str,
        safety_flags: list[str],
        reason: str,
    ) -> dict:
        self._record_fallback()
        self._record_schema_failure()
        self.world.add_event(
            "llm_reasoning_schema_validation_failed",
            {
                "purpose": purpose,
                "provider": provider,
                "reason": reason,
            },
        )
        self.world.add_event(
            "llm_reasoning_fallback_used",
            {
                "purpose": purpose,
                "provider": provider,
                "reason": reason,
            },
        )
        return {
            **fallback,
            "provider_used": provider,
            "safety_flags": safety_flags,
            "fallback_used": True,
            "fallback_reason": reason,
        }

    def _fallback_text(
        self,
        *,
        text: str,
        reason: str,
    ) -> dict:
        return {
            "text": text,
            "provider_used": "rules",
            "model_used": "rules",
            "safety_flags": [],
            "fallback_used": True,
            "fallback_reason": reason,
        }

    def _fallback_structured(
        self,
        payload: dict[str, Any],
        *,
        reason: str,
    ) -> dict:
        return {
            **payload,
            "provider_used": "rules",
            "model_used": "rules",
            "safety_flags": [],
            "fallback_used": True,
            "fallback_reason": reason,
        }

    def _check_rate_limit(
        self,
        purpose: str,
    ) -> bool:
        now = time.time()
        self._prune_runtime_state(now)
        self._request_timestamps.append(now)
        self._purpose_timestamps[purpose].append(now)

        global_limit = settings.LLM_REASONING_RATE_LIMIT_PER_MINUTE
        purpose_limit = settings.LLM_REASONING_RATE_LIMIT_PER_PURPOSE

        if (
            len(self._request_timestamps) > global_limit
            or len(self._purpose_timestamps[purpose]) > purpose_limit
        ):
            self._recent_rate_limited.append(now)
            return True
        return False

    def _rate_limited_fallback(
        self,
        purpose: str,
        fallback: dict,
    ) -> dict:
        self._record_fallback()
        self.world.add_event(
            "llm_reasoning_rate_limited",
            {"purpose": purpose},
        )
        return {
            **fallback,
            "safety_flags": [
                *fallback.get("safety_flags", []),
                LLMSafetyFlag.RATE_LIMITED.value,
            ],
            "fallback_used": True,
            "fallback_reason": "rate_limited",
        }

    def _maybe_create_suggestion(
        self,
        *,
        suggestion_type: str | None,
        result: dict[str, Any],
        task_id: str | None = None,
        command_id: str | None = None,
        agent_id: str | None = None,
    ) -> str | None:
        if not suggestion_type:
            return None
        if result.get("provider_used") == "rules":
            return None
        if result.get("fallback_reason") in {
            "invalid_json",
            "schema_validation_failed",
            "provider_failed",
            "guardrail_blocked",
            "rate_limited",
            "reasoning_disabled",
        }:
            return None

        content = (
            result.get("review_text")
            or result.get("summary")
            or result.get("improved_description")
            or result.get("text")
            or json.dumps(result, ensure_ascii=False)
        )
        suggestion = self.suggestions.create_suggestion(
            suggestion_type=suggestion_type,
            status=LLMSuggestionStatus.PENDING_REVIEW.value,
            task_id=task_id,
            command_id=command_id,
            agent_id=agent_id,
            source_provider=result.get("provider_used", "mock"),
            source_model=result.get("model_used", "unknown"),
            content=content,
            structured_payload={
                key: value
                for key, value in result.items()
                if key
                not in {
                    "provider_used",
                    "model_used",
                    "safety_flags",
                    "fallback_used",
                    "fallback_reason",
                    "suggestion_id",
                }
            },
            safety_flags=result.get("safety_flags", []),
            fallback_used=bool(result.get("fallback_used")),
        )
        return suggestion.id

    def _cache_key(
        self,
        purpose: str,
        cache_input: str | None,
    ) -> str | None:
        if cache_input is None:
            return None
        if purpose not in {
            "command_explanation",
            "task_summary",
            "timeline_summary",
        }:
            return None
        normalized = " ".join(cache_input.split())
        digest = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()
        return f"{purpose}:{digest}"

    def _get_cache(
        self,
        key: str,
    ) -> dict | None:
        self._prune_runtime_state()
        cached = self._cache.get(key)
        if not cached:
            return None
        if cached["expires_at"] <= time.time():
            self._cache.pop(key, None)
            return None
        return dict(cached["value"])

    def _put_cache(
        self,
        key: str,
        value: dict,
    ) -> None:
        self._cache[key] = {
            "value": dict(value),
            "expires_at": time.time()
            + settings.LLM_REASONING_CACHE_TTL_SECONDS,
        }

    @classmethod
    def _prune_runtime_state(
        cls,
        now: float | None = None,
    ) -> None:
        ts = now or time.time()
        cutoff = ts - 60
        recent_cutoff = ts - 600

        while cls._request_timestamps and cls._request_timestamps[0] <= cutoff:
            cls._request_timestamps.popleft()
        for purpose in list(cls._purpose_timestamps):
            queue = cls._purpose_timestamps[purpose]
            while queue and queue[0] <= cutoff:
                queue.popleft()
            if not queue:
                cls._purpose_timestamps.pop(purpose, None)

        expired = [
            key
            for key, item in cls._cache.items()
            if item["expires_at"] <= ts
        ]
        for key in expired:
            cls._cache.pop(key, None)

        for queue in (
            cls._recent_rate_limited,
            cls._recent_schema_failures,
            cls._recent_fallbacks,
        ):
            while queue and queue[0] <= recent_cutoff:
                queue.popleft()

    @classmethod
    def _record_schema_failure(cls) -> None:
        cls._recent_schema_failures.append(time.time())

    @classmethod
    def _record_fallback(cls) -> None:
        cls._recent_fallbacks.append(time.time())


def safe_json_parse(
    value: str,
) -> tuple[dict, bool]:
    try:
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed, True
    except Exception:
        pass
    return {}, False
