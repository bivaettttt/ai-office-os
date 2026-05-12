from __future__ import annotations

from app.core.agent_runtime.matching import (
    AgentMatch,
    CapabilityMatcher,
)
from app.core.agent_runtime.registry import AgentRegistry
from app.models.agent import Agent
from app.models.task import Task
from app.orchestration.event_bus import event_bus


class DepartmentManagerService:
    def __init__(
        self,
        registry: AgentRegistry,
        matcher: CapabilityMatcher,
    ):
        self.registry = registry
        self.matcher = matcher

    async def select_worker(
        self,
        task: Task,
    ) -> tuple[Agent | None, Agent | None, AgentMatch]:
        manager = self.registry.get_department_manager(
            task.department
        )

        if manager:
            await event_bus.emit(
                "manager_selected_task",
                {
                    "manager_id": manager.id,
                    "manager_name": manager.name,
                    "task_id": task.id,
                    "task_title": task.title,
                    "department": task.department,
                },
            )

        match = self.matcher.find_best_agent(
            task.department,
            task.required_capabilities,
        )

        if not match.agent:
            await event_bus.emit(
                "no_capable_agent_available",
                {
                    "task_id": task.id,
                    "department": task.department,
                    "required_capabilities": task.required_capabilities,
                    "reason": match.reason,
                },
            )
            return manager, None, match

        event_name = (
            "capability_fallback_used"
            if match.fallback_used
            else "capability_match_found"
        )
        await event_bus.emit(
            event_name,
            {
                "task_id": task.id,
                "agent_id": match.agent.id,
                "agent_name": match.agent.name,
                "department": task.department,
                "matched_capabilities": match.matched_capabilities,
                "missing_capabilities": match.missing_capabilities,
                "score": match.score,
            },
        )

        if manager:
            task.assigned_by_manager_id = manager.id
            await event_bus.emit(
                "manager_assigned_worker",
                {
                    "manager_id": manager.id,
                    "manager_name": manager.name,
                    "agent_id": match.agent.id,
                    "agent_name": match.agent.name,
                    "task_id": task.id,
                    "task_title": task.title,
                    "department": task.department,
                },
            )

        return manager, match.agent, match
