import time

from app.core.orchestration.task_status import (
    TaskStatus,
)

from app.orchestration.event_bus import (
    event_bus,
)


class TaskDispatcher:

    async def dispatch_task(
        self,
        task,
        agent,
    ):

        # =====================================
        # TASK
        # =====================================

        task.assigned_to = agent.id

        task.status = TaskStatus.IN_PROGRESS
        task.assigned_at = time.time()
        task.updated_at = time.time()

        # =====================================
        # AGENT
        # =====================================

        agent.status = "working"

        agent.current_task_id = task.id
        agent.task_progress = task.progress

        agent.current_action = (
            f"Working on: {task.title}"
        )

        agent.last_update = time.time()

        # =====================================
        # EVENTS
        # =====================================

        await event_bus.emit(

            "task.assigned",

            {
                "task_id": task.id,
                "task_title": task.title,
                "agent_id": agent.id,
                "agent_name": agent.name,
            }
        )

        await event_bus.emit(

            "task.started",

            {
                "task_id": task.id,
                "task_title": task.title,
                "agent_id": agent.id,
                "agent_name": agent.name,
            }
        )


dispatcher = TaskDispatcher()
