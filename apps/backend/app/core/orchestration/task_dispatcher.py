import time

from app.core.orchestration.task_status import (
    TaskStatus,
)
from app.core.agent_runtime.execution import (
    initialize_task_execution,
)
from app.core.world import world
from app.models.task import TaskRuntimePhase

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
        task.runtime_phase = TaskRuntimePhase.EXECUTING
        task.assigned_at = time.time()
        task.updated_at = time.time()
        first_step = initialize_task_execution(
            task,
            agent.id,
        )

        # =====================================
        # AGENT
        # =====================================

        agent.status = "working"

        agent.current_task_id = task.id
        agent.task_progress = task.progress
        agent.workload += 1

        agent.current_action = (
            f"Working on: {task.title}"
        )

        agent.last_update = time.time()
        agent.last_active_at = time.time()

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
                "manager_id": task.assigned_by_manager_id,
                "required_capabilities": task.required_capabilities,
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

        world.add_activity(
            agent.id,
            task.id,
            "task_assigned",
            f"{agent.name} assigned to {task.title}",
        )

        if first_step:
            await event_bus.emit(
                "task.step_started",
                {
                    "task_id": task.id,
                    "task_title": task.title,
                    "step_id": first_step.id,
                    "step_title": first_step.title,
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                },
            )
            world.add_activity(
                agent.id,
                task.id,
                "step_started",
                (
                    f"{agent.name} started step: "
                    f"{first_step.title}"
                ),
            )


dispatcher = TaskDispatcher()
