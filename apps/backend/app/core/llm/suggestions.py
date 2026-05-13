from __future__ import annotations

import hashlib
import json
import time
import uuid

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from app.config.settings import settings

if TYPE_CHECKING:
    from app.core.world import World


class LLMSuggestionType(StrEnum):
    COMMAND_PREVIEW = "command_preview"
    TASK_PLAN = "task_plan"
    MANAGER_REVIEW = "manager_review"
    TASK_SUMMARY = "task_summary"
    TIMELINE_SUMMARY = "timeline_summary"


class LLMSuggestionStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    EXPIRED = "expired"


class LLMGeneratedSuggestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: LLMSuggestionType
    status: LLMSuggestionStatus = LLMSuggestionStatus.PENDING_REVIEW
    task_id: str | None = None
    command_id: str | None = None
    agent_id: str | None = None
    manager_id: str | None = None
    source_provider: str
    source_model: str
    content: str
    structured_payload: dict[str, Any] | None = None
    safety_flags: list[str] = Field(default_factory=list)
    fallback_used: bool = False
    created_at: float = Field(default_factory=time.time)
    reviewed_at: float | None = None
    reviewed_by: str | None = None
    applied_at: float | None = None
    rejection_reason: str | None = None


class SuggestionApplyEffectPreview(BaseModel):
    can_apply: bool
    effect: str


class PromotedCommandDraft(BaseModel):
    title: str
    description: str
    department: str
    priority: str
    capabilities: list[str] = Field(default_factory=list)
    plan_notes: list[str] = Field(default_factory=list)


class LLMSuggestionContext(BaseModel):
    suggestion: LLMGeneratedSuggestion
    related_task_summary: dict[str, Any] | None = None
    related_command_summary: dict[str, Any] | None = None
    manager_name: str | None = None
    agent_name: str | None = None
    department: str | None = None
    age_seconds: int
    can_apply: bool
    apply_effect_preview: str


class LLMSuggestionReviewQueueResponse(BaseModel):
    suggestions: list[LLMSuggestionContext]
    counts_by_status: dict[str, int]
    counts_by_type: dict[str, int]
    counts_by_department: dict[str, int]
    oldest_pending_age_seconds: int
    filters_applied: dict[str, Any]


class SuggestionBulkExpireRequest(BaseModel):
    older_than_minutes: int | None = None
    type: str | None = None
    status: str | None = None
    department: str | None = None


class SuggestionBulkRejectRequest(BaseModel):
    ids: list[str] = Field(default_factory=list)
    rejection_reason: str
    reviewed_by: str | None = None


class SuggestionService:
    def __init__(self, world: "World"):
        self.world = world

    def create_suggestion(
        self,
        *,
        suggestion_type: str,
        content: str,
        source_provider: str,
        source_model: str,
        structured_payload: dict[str, Any] | None = None,
        safety_flags: list[str] | None = None,
        fallback_used: bool = False,
        task_id: str | None = None,
        command_id: str | None = None,
        agent_id: str | None = None,
        manager_id: str | None = None,
        status: str = LLMSuggestionStatus.PENDING_REVIEW.value,
    ) -> LLMGeneratedSuggestion:
        payload = structured_payload or {}
        dedupe_key = self._dedupe_key(
            suggestion_type=suggestion_type,
            task_id=task_id,
            command_id=command_id,
            content=content,
            payload=payload,
        )
        existing = self._find_by_dedupe_key(dedupe_key)
        if existing is not None and existing.status in {
            LLMSuggestionStatus.DRAFT,
            LLMSuggestionStatus.PENDING_REVIEW,
            LLMSuggestionStatus.APPROVED,
        }:
            return existing

        suggestion = LLMGeneratedSuggestion(
            type=suggestion_type,
            status=status,
            task_id=task_id,
            command_id=command_id,
            agent_id=agent_id,
            manager_id=manager_id,
            source_provider=source_provider,
            source_model=source_model,
            content=content,
            structured_payload=payload,
            safety_flags=safety_flags or [],
            fallback_used=fallback_used,
        )
        self.world.add_llm_suggestion(suggestion)
        self.world.add_event(
            "llm_suggestion_created",
            {
                "suggestion_id": suggestion.id,
                "suggestion_type": suggestion.type,
                "task_id": task_id,
                "command_id": command_id,
            },
        )
        return suggestion

    def list_suggestions(
        self,
        *,
        suggestion_type: str | None = None,
        status: str | None = None,
        department: str | None = None,
        manager_id: str | None = None,
        task_id: str | None = None,
        command_id: str | None = None,
        only_pending: bool = False,
        limit: int | None = None,
    ) -> list[LLMGeneratedSuggestion]:
        self.expire_old_suggestions()
        items = list(reversed(self.world.llm_suggestions))
        if suggestion_type:
            items = [
                item
                for item in items
                if item.type == suggestion_type
            ]
        if status:
            items = [
                item
                for item in items
                if item.status == status
            ]
        if only_pending:
            items = [
                item
                for item in items
                if item.status == LLMSuggestionStatus.PENDING_REVIEW
            ]
        if manager_id:
            items = [
                item
                for item in items
                if item.manager_id == manager_id
            ]
        if task_id:
            items = [
                item for item in items if item.task_id == task_id
            ]
        if command_id:
            items = [
                item
                for item in items
                if item.command_id == command_id
            ]
        if department:
            items = [
                item
                for item in items
                if self._resolve_department(item) == department
            ]
        return items[:limit] if limit else items

    def review_queue(
        self,
        *,
        suggestion_type: str | None = None,
        status: str | None = None,
        department: str | None = None,
        task_id: str | None = None,
        command_id: str | None = None,
        manager_id: str | None = None,
        only_pending: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        self.expire_old_suggestions()
        items = self.list_suggestions(
            suggestion_type=suggestion_type,
            status=status,
            department=department,
            task_id=task_id,
            command_id=command_id,
            manager_id=manager_id,
            only_pending=only_pending,
            limit=limit,
        )
        all_items = list(self.world.llm_suggestions)
        counts_by_status: dict[str, int] = {}
        counts_by_type: dict[str, int] = {}
        counts_by_department: dict[str, int] = {}
        pending_ages: list[int] = []
        now = time.time()

        for item in all_items:
            counts_by_status[item.status.value] = (
                counts_by_status.get(item.status.value, 0) + 1
            )
            counts_by_type[item.type.value] = (
                counts_by_type.get(item.type.value, 0) + 1
            )
            item_department = self._resolve_department(item) or "unknown"
            counts_by_department[item_department] = (
                counts_by_department.get(item_department, 0) + 1
            )
            if item.status == LLMSuggestionStatus.PENDING_REVIEW:
                pending_ages.append(int(now - item.created_at))

        self.world.add_event(
            "llm_review_queue_viewed",
            {
                "status": status,
                "type": suggestion_type,
                "department": department,
                "task_id": task_id,
                "command_id": command_id,
                "manager_id": manager_id,
                "only_pending": only_pending,
            },
        )
        return LLMSuggestionReviewQueueResponse(
            suggestions=[self._context_for(item) for item in items],
            counts_by_status=counts_by_status,
            counts_by_type=counts_by_type,
            counts_by_department=counts_by_department,
            oldest_pending_age_seconds=max(pending_ages, default=0),
            filters_applied={
                "status": status,
                "type": suggestion_type,
                "department": department,
                "task_id": task_id,
                "command_id": command_id,
                "manager_id": manager_id,
                "only_pending": only_pending,
                "limit": limit,
            },
        ).model_dump(mode="json")

    def get_suggestion(
        self,
        suggestion_id: str,
    ) -> LLMGeneratedSuggestion | None:
        return next(
            (
                item
                for item in self.world.llm_suggestions
                if item.id == suggestion_id
            ),
            None,
        )

    def approve_suggestion(
        self,
        suggestion_id: str,
        *,
        reviewed_by: str | None = None,
    ) -> LLMGeneratedSuggestion:
        suggestion = self._require(suggestion_id)
        suggestion.status = LLMSuggestionStatus.APPROVED
        suggestion.reviewed_at = time.time()
        suggestion.reviewed_by = reviewed_by or "manager"
        self.world.add_event(
            "llm_suggestion_approved",
            {
                "suggestion_id": suggestion.id,
                "task_id": suggestion.task_id,
                "command_id": suggestion.command_id,
            },
        )
        return suggestion

    def reject_suggestion(
        self,
        suggestion_id: str,
        *,
        reviewed_by: str | None = None,
        rejection_reason: str | None = None,
    ) -> LLMGeneratedSuggestion:
        suggestion = self._require(suggestion_id)
        suggestion.status = LLMSuggestionStatus.REJECTED
        suggestion.reviewed_at = time.time()
        suggestion.reviewed_by = reviewed_by or "manager"
        suggestion.rejection_reason = rejection_reason
        self.world.add_event(
            "llm_suggestion_rejected",
            {
                "suggestion_id": suggestion.id,
                "task_id": suggestion.task_id,
                "command_id": suggestion.command_id,
                "reason": rejection_reason,
            },
        )
        return suggestion

    def apply_suggestion(
        self,
        suggestion_id: str,
        *,
        reviewed_by: str | None = None,
    ) -> dict[str, Any]:
        suggestion = self._require(suggestion_id)

        if suggestion.type == LLMSuggestionType.COMMAND_PREVIEW:
            result = {
                "applied": False,
                "message": "Command preview suggestions stay in UI only.",
            }
        else:
            task = (
                self.world.tasks.get(suggestion.task_id)
                if suggestion.task_id
                else None
            )
            if task is None:
                raise ValueError("Related task not found")

            payload = suggestion.structured_payload or {}
            if suggestion.type == LLMSuggestionType.TASK_SUMMARY:
                task.summary_note = payload.get("summary") or suggestion.content
            elif suggestion.type == LLMSuggestionType.MANAGER_REVIEW:
                task.review_draft = (
                    payload.get("review_text") or suggestion.content
                )
            elif suggestion.type == LLMSuggestionType.TASK_PLAN:
                task.proposed_plan = payload.get("suggested_steps", [])
                task.plan_notes = [
                    *payload.get("risks", []),
                    *payload.get("assumptions", []),
                ]
            elif suggestion.type == LLMSuggestionType.TIMELINE_SUMMARY:
                task.summary_note = payload.get("summary") or suggestion.content
            else:
                raise ValueError("Unsupported suggestion type")

            task.updated_at = time.time()
            result = {
                "applied": True,
                "task_id": task.id,
                "message": "Suggestion applied safely without changing execution.",
            }

        suggestion.status = LLMSuggestionStatus.APPLIED
        suggestion.reviewed_at = suggestion.reviewed_at or time.time()
        suggestion.reviewed_by = reviewed_by or suggestion.reviewed_by or "manager"
        suggestion.applied_at = time.time()
        self.world.add_event(
            "llm_suggestion_applied",
            {
                "suggestion_id": suggestion.id,
                "task_id": suggestion.task_id,
                "command_id": suggestion.command_id,
                "suggestion_type": suggestion.type,
            },
        )
        return result

    def expire_old_suggestions(
        self,
        *,
        older_than_minutes: int | None = None,
        suggestion_type: str | None = None,
        status: str | None = None,
        department: str | None = None,
    ) -> list[LLMGeneratedSuggestion]:
        ttl_minutes = older_than_minutes or settings.LLM_SUGGESTION_TTL_MINUTES
        cutoff = time.time() - ttl_minutes * 60
        expired: list[LLMGeneratedSuggestion] = []
        for item in self.world.llm_suggestions:
            if item.status not in {
                LLMSuggestionStatus.DRAFT,
                LLMSuggestionStatus.PENDING_REVIEW,
            }:
                continue
            if item.created_at > cutoff:
                continue
            if suggestion_type and item.type != suggestion_type:
                continue
            if status and item.status != status:
                continue
            if department and self._resolve_department(item) != department:
                continue
            item.status = LLMSuggestionStatus.EXPIRED
            expired.append(item)
            self.world.add_event(
                "llm_suggestion_expired",
                {
                    "suggestion_id": item.id,
                    "task_id": item.task_id,
                    "command_id": item.command_id,
                },
            )
        return expired

    def bulk_expire(
        self,
        *,
        older_than_minutes: int | None = None,
        suggestion_type: str | None = None,
        status: str | None = None,
        department: str | None = None,
    ) -> dict[str, Any]:
        expired = self.expire_old_suggestions(
            older_than_minutes=older_than_minutes,
            suggestion_type=suggestion_type,
            status=status,
            department=department,
        )
        self.world.add_event(
            "llm_suggestion_bulk_expired",
            {
                "count": len(expired),
                "type": suggestion_type,
                "status": status,
                "department": department,
            },
        )
        return {
            "count": len(expired),
            "ids": [item.id for item in expired],
        }

    def bulk_reject(
        self,
        *,
        ids: list[str],
        rejection_reason: str,
        reviewed_by: str | None = None,
    ) -> dict[str, Any]:
        rejected_ids: list[str] = []
        for suggestion_id in ids:
            item = self._require(suggestion_id)
            if item.status in {
                LLMSuggestionStatus.DRAFT,
                LLMSuggestionStatus.PENDING_REVIEW,
                LLMSuggestionStatus.APPROVED,
            }:
                self.reject_suggestion(
                    suggestion_id,
                    reviewed_by=reviewed_by,
                    rejection_reason=rejection_reason,
                )
                rejected_ids.append(suggestion_id)
        self.world.add_event(
            "llm_suggestion_bulk_rejected",
            {
                "count": len(rejected_ids),
                "ids": rejected_ids,
            },
        )
        return {
            "count": len(rejected_ids),
            "ids": rejected_ids,
        }

    def promote_command_draft(
        self,
        suggestion_id: str,
    ) -> dict[str, Any]:
        suggestion = self._require(suggestion_id)
        if suggestion.type != LLMSuggestionType.COMMAND_PREVIEW:
            raise ValueError("Only command_preview suggestions can be promoted")
        payload = suggestion.structured_payload or {}
        draft = PromotedCommandDraft(
            title=payload.get("improved_title") or "AI Draft",
            description=payload.get("improved_description") or suggestion.content,
            department=payload.get("department") or "assistant",
            priority=payload.get("priority") or "normal",
            capabilities=payload.get("capabilities") or [],
            plan_notes=payload.get("plan_notes") or [],
        )
        self.world.add_event(
            "llm_suggestion_promoted_to_command_draft",
            {
                "suggestion_id": suggestion.id,
                "command_id": suggestion.command_id,
                "draft": draft.model_dump(mode="json"),
            },
        )
        return draft.model_dump(mode="json")

    def expire_suggestion(
        self,
        suggestion_id: str,
    ) -> LLMGeneratedSuggestion:
        suggestion = self._require(suggestion_id)
        suggestion.status = LLMSuggestionStatus.EXPIRED
        self.world.add_event(
            "llm_suggestion_expired",
            {
                "suggestion_id": suggestion.id,
                "task_id": suggestion.task_id,
                "command_id": suggestion.command_id,
            },
        )
        return suggestion

    def _require(
        self,
        suggestion_id: str,
    ) -> LLMGeneratedSuggestion:
        suggestion = self.get_suggestion(suggestion_id)
        if suggestion is None:
            raise ValueError("Suggestion not found")
        return suggestion

    def _dedupe_key(
        self,
        *,
        suggestion_type: str,
        task_id: str | None,
        command_id: str | None,
        content: str,
        payload: dict[str, Any],
    ) -> str:
        normalized = json.dumps(
            {
                "type": suggestion_type,
                "task_id": task_id,
                "command_id": command_id,
                "content": content,
                "payload": payload,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _find_by_dedupe_key(
        self,
        dedupe_key: str,
    ) -> LLMGeneratedSuggestion | None:
        for item in reversed(self.world.llm_suggestions):
            current_key = self._dedupe_key(
                suggestion_type=item.type,
                task_id=item.task_id,
                command_id=item.command_id,
                content=item.content,
                payload=item.structured_payload or {},
            )
            if current_key == dedupe_key:
                return item
        return None

    def _resolve_department(
        self,
        item: LLMGeneratedSuggestion,
    ) -> str | None:
        if item.task_id and item.task_id in self.world.tasks:
            return self.world.tasks[item.task_id].department
        if item.command_id and item.command_id in self.world.commands:
            return self.world.commands[item.command_id].inferred_department
        payload = item.structured_payload or {}
        department = payload.get("department")
        return str(department) if department else None

    def _apply_effect_preview(
        self,
        item: LLMGeneratedSuggestion,
    ) -> SuggestionApplyEffectPreview:
        if item.type == LLMSuggestionType.TASK_SUMMARY:
            return SuggestionApplyEffectPreview(
                can_apply=True,
                effect="Will update task.summary_note only",
            )
        if item.type == LLMSuggestionType.MANAGER_REVIEW:
            return SuggestionApplyEffectPreview(
                can_apply=True,
                effect="Will update task.review_draft only",
            )
        if item.type == LLMSuggestionType.TASK_PLAN:
            return SuggestionApplyEffectPreview(
                can_apply=True,
                effect="Will store proposed_plan/plan_notes without changing active steps",
            )
        if item.type == LLMSuggestionType.COMMAND_PREVIEW:
            return SuggestionApplyEffectPreview(
                can_apply=False,
                effect="Can be promoted to task draft; will not start orchestration automatically",
            )
        return SuggestionApplyEffectPreview(
            can_apply=True,
            effect="Will update summary_note only",
        )

    def _context_for(
        self,
        item: LLMGeneratedSuggestion,
    ) -> LLMSuggestionContext:
        task = self.world.tasks.get(item.task_id) if item.task_id else None
        command = self.world.commands.get(item.command_id) if item.command_id else None
        manager = self.world.agents.get(item.manager_id) if item.manager_id else None
        agent = self.world.agents.get(item.agent_id) if item.agent_id else None
        preview = self._apply_effect_preview(item)
        return LLMSuggestionContext(
            suggestion=item,
            related_task_summary=(
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "department": task.department,
                }
                if task
                else None
            ),
            related_command_summary=(
                {
                    "id": command.id,
                    "raw_text": command.raw_text,
                    "status": command.status,
                    "department": command.inferred_department,
                }
                if command
                else None
            ),
            manager_name=manager.name if manager else None,
            agent_name=agent.name if agent else None,
            department=self._resolve_department(item),
            age_seconds=int(time.time() - item.created_at),
            can_apply=preview.can_apply,
            apply_effect_preview=preview.effect,
        )

    def count_pending(self) -> int:
        return len(
            [
                item
                for item in self.world.llm_suggestions
                if item.status == LLMSuggestionStatus.PENDING_REVIEW
            ]
        )

    def oldest_pending_age_seconds(self) -> int:
        pending = [
            int(time.time() - item.created_at)
            for item in self.world.llm_suggestions
            if item.status == LLMSuggestionStatus.PENDING_REVIEW
        ]
        return max(pending, default=0)
