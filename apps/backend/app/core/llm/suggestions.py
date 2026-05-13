from __future__ import annotations

import hashlib
import json
import time
import uuid

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

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
        task_id: str | None = None,
        command_id: str | None = None,
        limit: int | None = None,
    ) -> list[LLMGeneratedSuggestion]:
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
        return items[:limit] if limit else items

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
