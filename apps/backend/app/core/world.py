from __future__ import annotations

from typing import Dict
import time

from app.models.agent import Agent
from app.models.task import Task
from app.models.department import Department
from app.models.command import UserCommand
from app.core.tools.permissions import (
    PermissionGrant,
    ToolAuditEntry,
    ToolInvocation,
)
from app.core.tools.sandbox import SandboxContract


class World:

    def __init__(self):

        self.agents: Dict[str, Agent] = {}

        self.departments: Dict[str, Department] = {}

        self.tasks: Dict[str, Task] = {}

        self.events: list[dict] = []

        self.activity_log: list[dict] = []

        self.commands: Dict[str, UserCommand] = {}

        self.tool_invocations: Dict[str, ToolInvocation] = {}

        self.tool_audit_log: list[ToolAuditEntry] = []

        self.permission_grants: Dict[str, PermissionGrant] = {}

        self.sandbox_contracts: Dict[str, SandboxContract] = {}

    # =====================================================
    # AGENTS
    # =====================================================

    def add_agent(self, agent: Agent):

        self.agents[agent.id] = agent
        for department in self.departments.values():
            if (
                department.name == agent.department
                and agent.id not in department.agents
            ):
                department.agents.append(agent.id)
                break

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

    # =====================================================
    # COMMANDS
    # =====================================================

    def add_command(self, command: UserCommand):

        self.commands[command.id] = command

        if len(self.commands) > 100:
            oldest = sorted(
                self.commands.values(),
                key=lambda item: item.created_at,
            )[:-100]

            for item in oldest:
                self.commands.pop(item.id, None)

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
    # TOOLS
    # =====================================================

    def add_tool_invocation(
        self,
        invocation: ToolInvocation,
    ):

        self.tool_invocations[invocation.id] = invocation

    def add_tool_audit(
        self,
        entry: ToolAuditEntry,
    ):

        self.tool_audit_log.append(entry)
        self.tool_audit_log = self.tool_audit_log[-500:]

    def add_permission_grant(
        self,
        grant: PermissionGrant,
    ):

        self.permission_grants[grant.id] = grant

    def add_sandbox_contract(
        self,
        contract: SandboxContract,
    ):

        self.sandbox_contracts[contract.id] = contract

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
        self.activity_log = data.get(
            "activity_log",
            [],
        )[-500:]
        self.commands = {
            key: UserCommand.model_validate(value)
            for key, value
            in data.get("commands", {}).items()
        }
        self.tool_invocations = {
            key: ToolInvocation.model_validate(value)
            for key, value
            in data.get("tool_invocations", {}).items()
        }
        self.tool_audit_log = [
            ToolAuditEntry.model_validate(value)
            for value in data.get("tool_audit_log", [])
        ][-500:]
        self.permission_grants = {
            key: PermissionGrant.model_validate(value)
            for key, value
            in data.get("permission_grants", {}).items()
        }
        self.sandbox_contracts = {
            key: SandboxContract.model_validate(value)
            for key, value
            in data.get("sandbox_contracts", {}).items()
        }

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
    # ACTIVITY LOG
    # =====================================================

    def add_activity(
        self,
        agent_id: str | None,
        task_id: str | None,
        activity_type: str,
        message: str,
    ):

        self.activity_log.append(
            {
                "id": f"{int(time.time() * 1000)}-{len(self.activity_log)}",
                "timestamp": time.time(),
                "agent_id": agent_id,
                "task_id": task_id,
                "type": activity_type,
                "message": message,
            }
        )

        self.activity_log = self.activity_log[-500:]

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

            "activity_log": self.activity_log,

            "commands": {
                k: v.model_dump(mode="json")
                for k, v in self.commands.items()
            },

            "tool_invocations": {
                k: v.model_dump(mode="json")
                for k, v in self.tool_invocations.items()
            },

            "tool_audit_log": [
                item.model_dump(mode="json")
                for item in self.tool_audit_log
            ],

            "permission_grants": {
                k: v.model_dump(mode="json")
                for k, v in self.permission_grants.items()
            },

            "sandbox_contracts": {
                k: v.model_dump(mode="json")
                for k, v in self.sandbox_contracts.items()
            },
        }


# =========================================================
# SINGLETON
# =========================================================

world = World()
