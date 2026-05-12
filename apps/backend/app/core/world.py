from __future__ import annotations

from typing import Dict
import time

from app.models.agent import Agent
from app.models.task import Task
from app.models.department import Department


class World:

    def __init__(self):

        self.agents: Dict[str, Agent] = {}

        self.departments: Dict[str, Department] = {}

        self.tasks: Dict[str, Task] = {}

        self.events: list[dict] = []

    # =====================================================
    # AGENTS
    # =====================================================

    def add_agent(self, agent: Agent):

        self.agents[agent.id] = agent

    def update_agent(
        self,
        agent_id: str,
        **changes,
    ):

        agent = self.agents.get(agent_id)

        if not agent:
            return None

        for key, value in changes.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        agent.last_update = time.time()

        return agent

    # =====================================================
    # DEPARTMENTS
    # =====================================================

    def add_department(
        self,
        department: Department,
    ):

        self.departments[
            department.id
        ] = department

    # =====================================================
    # TASKS
    # =====================================================

    def add_task(self, task: Task):

        self.tasks[task.id] = task

    def update_task(
        self,
        task_id: str,
        **changes,
    ):

        task = self.tasks.get(task_id)

        if not task:
            return None

        for key, value in changes.items():
            if hasattr(task, key):
                setattr(task, key, value)

        task.updated_at = time.time()

        return task

    # =====================================================
    # HYDRATION
    # =====================================================

    def hydrate(
        self,
        data: dict,
    ):

        self.agents = {
            key: Agent.model_validate(value)
            for key, value
            in data.get("agents", {}).items()
        }

        self.departments = {
            key: Department.model_validate(value)
            for key, value
            in data.get("departments", {}).items()
        }

        self.tasks = {
            key: Task.model_validate(value)
            for key, value
            in data.get("tasks", {}).items()
        }

        self.events = data.get("events", [])[-200:]

    # =====================================================
    # EVENTS
    # =====================================================

    def add_event(
        self,
        event_type: str,
        payload: dict | None = None,
    ):

        self.events.append(
            {
                "type": event_type,
                "payload": payload or {},
                "ts": time.time(),
            }
        )

        self.events = self.events[-200:]

    # =====================================================
    # SERIALIZE
    # =====================================================

    def serialize(self):

        return {
            "agents": {
                k: v.model_dump(mode="json")
                for k, v in self.agents.items()
            },

            "departments": {
                k: v.model_dump(mode="json")
                for k, v in self.departments.items()
            },

            "tasks": {
                k: v.model_dump(mode="json")
                for k, v in self.tasks.items()
            },

            "events": self.events,
        }


# =========================================================
# SINGLETON
# =========================================================

world = World()
