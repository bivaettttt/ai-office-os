from app.memory.agent_memory import (
    agent_memory,
)

from app.core.factory import create_task

from app.orchestration.event_bus import (
    event_bus,
)


class Orchestrator:

    async def process_user_request(
        self,
        message: str,
    ):

        department = self.detect_department(
            message
        )

        task = create_task(
            title=message,
            description=message,
            department=department,
            priority="normal",
        )

        # =====================================
        # MANAGER STATE
        # =====================================

        agent_memory[
            "manager"
        ]["status"] = "working"

        agent_memory[
            "manager"
        ]["task"] = message

        # =====================================
        # EVENTS
        # =====================================

        await event_bus.emit(
            "task.created",
            {
                "task_id": task.id,
                "title": task.title,
                "department": department,
            },
        )

        await event_bus.emit(
            "manager.updated",
            {
                "status": "working",
                "task": message,
            },
        )

        return {
            "status": "created",
            "department": department,
            "task_id": task.id,
        }

    # =====================================================
    # ROUTING
    # =====================================================

    def detect_department(
        self,
        message: str,
    ):

        text = message.lower()

        # =====================================
        # DEVELOPMENT
        # =====================================

        if (
            "site" in text
            or "app" in text
            or "code" in text
            or "backend" in text
            or "frontend" in text
            or "api" in text
        ):
            return "development"

        # =====================================
        # ANALYTICS
        # =====================================

        if (
            "research" in text
            or "analyze" in text
            or "market" in text
            or "competitor" in text
        ):
            return "analytics"

        # =====================================
        # ASSISTANT
        # =====================================

        if (
            "schedule" in text
            or "telegram" in text
            or "message" in text
            or "calendar" in text
        ):
            return "assistant"

        if (
            "content" in text
            or "article" in text
            or "seo" in text
            or "post" in text
        ):
            return "content"

        return "assistant"


orchestrator = Orchestrator()
