import asyncio
import logging

from app.core.orchestration.task_scheduler import (
    scheduler,
)

from app.core.orchestration.task_dispatcher import (
    dispatcher,
)
from app.core.world import world
from app.orchestration.event_bus import event_bus

logger = logging.getLogger(__name__)


class TaskOrchestrator:

    async def process_tasks(self):

        while True:

            try:

                pending_tasks = (
                    scheduler.get_pending_tasks()
                )

                if len(pending_tasks) > 5:
                    await event_bus.emit(
                        "task.queue_overloaded",
                        {
                            "pending": len(pending_tasks),
                        },
                    )

                for task in pending_tasks:

                    agent = (
                        scheduler.get_available_agent(
                            task.department
                        )
                    )

                    if not agent:
                        task.status = "queued"
                        world.add_event(
                            "task.no_free_agents",
                            {
                                "task_id": task.id,
                                "department": task.department,
                            },
                        )
                        continue

                    await dispatcher.dispatch_task(
                        task,
                        agent,
                    )

                await asyncio.sleep(1)

            except Exception:

                logger.exception("task orchestrator error")

                await asyncio.sleep(3)


task_orchestrator = TaskOrchestrator()
