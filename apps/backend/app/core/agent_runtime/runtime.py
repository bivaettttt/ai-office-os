from __future__ import annotations

from app.core.agent_runtime.managers import (
    DepartmentManagerService,
)
from app.core.agent_runtime.matching import (
    CapabilityMatcher,
)
from app.core.agent_runtime.registry import AgentRegistry
from app.core.world import World
from app.models.agent import Agent
from app.models.task import Task


class AgentRuntimeService:
    def __init__(self, world: World):
        self.registry = AgentRegistry(world)
        self.matcher = CapabilityMatcher(self.registry)
        self.managers = DepartmentManagerService(
            self.registry,
            self.matcher,
        )

    async def select_agent_for_task(
        self,
        task: Task,
    ) -> tuple[Agent | None, Agent | None]:
        manager, worker, _match = (
            await self.managers.select_worker(task)
        )
        return manager, worker
