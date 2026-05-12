from __future__ import annotations

from app.models.agent import Agent
from app.core.world import World


class AgentRegistry:
    def __init__(self, world: World):
        self.world = world

    def register(self, agent: Agent) -> Agent:
        self.world.add_agent(agent)
        return agent

    def get(self, agent_id: str) -> Agent | None:
        return self.world.agents.get(agent_id)

    def list_agents(self) -> list[Agent]:
        return list(self.world.agents.values())

    def list_by_department(
        self,
        department: str,
    ) -> list[Agent]:
        return [
            agent
            for agent in self.world.agents.values()
            if agent.department == department
        ]

    def list_available_agents(
        self,
        department: str | None = None,
    ) -> list[Agent]:
        return [
            agent
            for agent in self.world.agents.values()
            if (
                agent.status == "idle"
                and not agent.current_task_id
                and not agent.is_manager
                and (
                    department is None
                    or agent.department == department
                )
            )
        ]

    def get_department_manager(
        self,
        department: str,
    ) -> Agent | None:
        for agent in self.world.agents.values():
            if (
                agent.is_manager
                and agent.manager_for_department == department
            ):
                return agent

        department_model = next(
            (
                item
                for item in self.world.departments.values()
                if item.name == department
            ),
            None,
        )

        if department_model and department_model.manager_agent_id:
            return self.get(department_model.manager_agent_id)

        return None

    def find_agents_by_capability(
        self,
        capability: str,
    ) -> list[Agent]:
        return [
            agent
            for agent in self.world.agents.values()
            if capability in agent.capabilities
        ]
