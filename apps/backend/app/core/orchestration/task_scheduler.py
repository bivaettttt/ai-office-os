from app.core.world import world

from app.core.orchestration.task_status import (
    TaskStatus,
)


class TaskScheduler:

    def get_available_agent(
        self,
        department: str,
    ):

        agents = world.agents.values()

        available = [
            agent
            for agent in agents
            if (
                agent.department == department
                and agent.status == "idle"
            )
        ]

        if not available:
            return None

        return available[0]

    def get_pending_tasks(self):

        return [

            task

            for task in world.tasks.values()

            if task.status in [
                TaskStatus.CREATED,
                TaskStatus.QUEUED,
            ]
        ]


scheduler = TaskScheduler()