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
                '"plan_notes":"Keep the scope read-only and controlled."}'
            )
        elif template == "task_plan_draft":
            content = (
                '{"suggested_steps":["Clarify request",'
                '"Refine plan","Validate summary"]}'
            )
        elif template == "manager_review_draft":
            content = (
                "Manager review draft: execution matched the current plan "
                "and the summary is ready for controlled completion."
            )
        elif template == "task_summary":
            content = (
                "Task summary: the task progressed through its visible steps "
                "and remains inside the controlled local workflow."
            )
        elif template == "timeline_summary":
            content = (
                "Timeline summary: the recent events show a normal local "
                "sequence of routing, execution, and status updates."
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
