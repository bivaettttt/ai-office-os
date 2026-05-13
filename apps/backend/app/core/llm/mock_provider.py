from __future__ import annotations

from app.core.llm.providers import LLMProvider
from app.core.llm.types import LLMRequest, LLMResponse


class MockProvider(LLMProvider):
    name = "mock"

    def is_available(self) -> bool:
        return True

    def availability_reason(self) -> str | None:
        return None

    def default_model(self) -> str:
        return "mock-safe-model"

    def complete(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        template = request.metadata.get("reasoning_template")
        user_text = next(
            (
                message.content
                for message in reversed(request.messages)
                if message.role == "user"
            ),
            "",
        )
        model = request.model or self.default_model()
        content = (
            f"[mock:{model}] Safe deterministic response for "
            f"{request.purpose}: {user_text[:160]}"
        )

        if template == "command_explanation":
            department = request.metadata.get("department", "assistant")
            priority = request.metadata.get("priority", "normal")
            content = (
                f"This command is routed to {department} with {priority} "
                "priority based on the current local routing rules."
            )
        elif template == "command_preview_enhancement":
            content = (
                '{"improved_title":"Refined command draft",'
                '"improved_description":"Clarified local command description.",'
                '"plan_notes":["Keep the scope read-only and controlled.",'
                '"Preserve the existing task routing flow."],'
                '"confidence_note":"Local mock reasoning returned a safe deterministic preview."}'
            )
        elif template == "task_plan_draft":
            content = (
                '{"suggested_steps":["Clarify request",'
                '"Refine plan","Validate summary"],'
                '"risks":["No real execution is performed at this stage."],'
                '"assumptions":["The current department routing remains unchanged."]}'
            )
        elif template == "manager_review_draft":
            content = (
                '{"review_text":"Execution matched the visible plan and the task can be closed in the controlled local flow.",'
                '"quality_notes":["Result stayed inside the approved local reasoning boundary."],'
                '"approval_recommendation":"approve"}'
            )
        elif template == "task_summary":
            content = (
                '{"summary":"The task progressed through its visible steps inside the controlled local workflow.",'
                '"current_state":"Task state is consistent with the current step and progress.",'
                '"next_best_action":"Continue the current controlled task flow or review completion."}'
            )
        elif template == "timeline_summary":
            content = (
                '{"summary":"The recent timeline shows a normal local sequence of routing, execution, and status updates.",'
                '"key_events":["Command routed","Task executed","Status updated"],'
                '"risks_or_blockers":[]}'
            )

        return LLMResponse(
            content=content,
            provider=self.name,
            model=model,
            usage={
                "prompt_chars": sum(
                    len(message.content)
                    for message in request.messages
                ),
                "completion_chars": min(len(user_text), 160),
            },
            finish_reason="stop",
        )
