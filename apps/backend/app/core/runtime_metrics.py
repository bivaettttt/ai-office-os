from __future__ import annotations

import time

from app.core.world import World


MANAGER_DECISION_TYPES = {
    "manager_selected_task",
    "manager_assigned_worker",
    "capability_match_found",
    "capability_fallback_used",
    "manager_review_approved",
    "manager_review_failed",
}


FAILURE_TYPES = {
    "task.failed",
    "task.step_failed",
    "command_failed",
    "task_failed",
    "step_failed",
    "manager_review_failed",
}


def build_runtime_metrics(world: World) -> dict:
    tasks = list(world.tasks.values())
    agents = list(world.agents.values())
    commands = list(world.commands.values())
    tool_invocations = list(world.tool_invocations.values())
    grants = list(world.permission_grants.values())
    audit_entries = list(world.tool_audit_log)
    pending_approvals_by_risk = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    }
    for invocation in tool_invocations:
        if invocation.status != "awaiting_approval":
            continue
        tool_audit = next(
            (
                entry
                for entry in audit_entries
                if entry.invocation_id == invocation.id
            ),
            None,
        )
        if tool_audit:
            pending_approvals_by_risk[
                tool_audit.risk_level.value
            ] += 1

    queued_tasks = [
        task
        for task in tasks
        if task.status == "queued"
    ]
    in_progress_tasks = [
        task
        for task in tasks
        if task.status in ["assigned", "in_progress", "review"]
    ]
    completed_tasks = [
        task
        for task in tasks
        if task.status == "completed"
    ]
    failed_tasks = [
        task
        for task in tasks
        if task.status == "failed"
    ]
    cancelled_tasks = [
        task
        for task in tasks
        if task.status == "cancelled"
    ]
    paused_tasks = [
        task
        for task in tasks
        if task.runtime_phase == "paused"
    ]
    busy_agents = [
        agent
        for agent in agents
        if agent.status == "working"
    ]
    idle_agents = [
        agent
        for agent in agents
        if agent.status == "idle"
    ]
    managers = [
        agent
        for agent in agents
        if agent.is_manager
    ]

    average_progress = (
        round(
            sum(task.progress for task in tasks)
            / len(tasks),
            2,
        )
        if tasks
        else 0
    )

    global_metrics = {
        "total_tasks": len(tasks),
        "queued_tasks": len(queued_tasks),
        "in_progress_tasks": len(in_progress_tasks),
        "completed_tasks": len(completed_tasks),
        "failed_tasks": len(failed_tasks),
        "cancelled_tasks": len(cancelled_tasks),
        "paused_tasks": len(paused_tasks),
        "total_agents": len(agents),
        "busy_agents": len(busy_agents),
        "idle_agents": len(idle_agents),
        "managers_count": len(managers),
        "average_task_progress": average_progress,
        "active_commands": len(
            [
                command
                for command in commands
                if command.status
                in ["received", "parsed", "routed"]
            ]
        ),
        "failed_commands": len(
            [
                command
                for command in commands
                if command.status == "failed"
            ]
        ),
        "pending_tool_approvals": len(
            [
                invocation
                for invocation in tool_invocations
                if invocation.status == "awaiting_approval"
            ]
        ),
        "completed_tool_invocations": len(
            [
                invocation
                for invocation in tool_invocations
                if invocation.status == "completed"
            ]
        ),
        "blocked_tool_invocations": len(
            [
                invocation
                for invocation in tool_invocations
                if invocation.status == "blocked"
            ]
        ),
        "active_permission_grants": len(
            [
                grant
                for grant in grants
                if grant.is_active()
            ]
        ),
        "expired_permission_grants": len(
            [
                grant
                for grant in grants
                if (
                    grant.expires_at is not None
                    and grant.expires_at <= time.time()
                    and grant.revoked_at is None
                )
            ]
        ),
        "revoked_permission_grants": len(
            [
                grant
                for grant in grants
                if grant.revoked_at is not None
            ]
        ),
        "invocations_allowed_by_grant": len(
            [
                invocation
                for invocation in tool_invocations
                if invocation.used_grant_ids
            ]
        ),
        "pending_approvals_by_risk": pending_approvals_by_risk,
        "approvals_approved_total": len(
            [
                entry
                for entry in audit_entries
                if entry.action
                in [
                    "approval_once_approved",
                    "approval_grant_approved",
                ]
            ]
        ),
        "approvals_rejected_total": len(
            [
                entry
                for entry in audit_entries
                if entry.action == "rejected"
            ]
        ),
        "dry_run_invocations_total": len(
            [
                invocation
                for invocation in tool_invocations
                if invocation.dry_run
            ]
        ),
        "sandbox_contracts_created": len(world.sandbox_contracts),
    }

    department_metrics = [
        build_department_metrics(
            department,
            agents,
            tasks,
        )
        for department in sorted(
            {
                *[agent.department for agent in agents],
                *[task.department for task in tasks],
            }
        )
    ]

    agent_workload = [
        build_agent_workload(
            world,
            agent,
        )
        for agent in sorted(
            agents,
            key=lambda item: (
                item.department,
                item.name,
            ),
        )
    ]

    recent_manager_decisions = recent_entries(
        world,
        MANAGER_DECISION_TYPES,
        12,
    )
    recent_failures = recent_entries(
        world,
        FAILURE_TYPES,
        12,
        since=time.time() - 30 * 60,
    )

    queue_health = build_queue_health(
        queued_tasks=len(queued_tasks),
        in_progress_tasks=len(in_progress_tasks),
        failed_recent=len(recent_failures),
        available_agents=len(
            [
                agent
                for agent in agents
                if (
                    agent.status == "idle"
                    and not agent.current_task_id
                    and not agent.is_manager
                )
            ]
        ),
    )

    return {
        "global_metrics": global_metrics,
        "department_metrics": department_metrics,
        "agent_workload": agent_workload,
        "recent_manager_decisions": recent_manager_decisions,
        "recent_failures": recent_failures,
        "queue_health": queue_health,
    }


def build_department_metrics(
    department: str,
    agents: list,
    tasks: list,
) -> dict:
    department_agents = [
        agent
        for agent in agents
        if agent.department == department
    ]
    department_tasks = [
        task
        for task in tasks
        if task.department == department
    ]
    busy_agents = [
        agent
        for agent in department_agents
        if agent.status == "working"
    ]
    idle_agents = [
        agent
        for agent in department_agents
        if agent.status == "idle"
    ]
    managers = [
        agent
        for agent in department_agents
        if agent.is_manager
    ]
    queued_tasks = [
        task
        for task in department_tasks
        if task.status == "queued"
    ]

    workload_score = round(
        (
            len(busy_agents)
            / max(len(department_agents), 1)
        )
        + len(queued_tasks) * 0.1,
        2,
    )

    return {
        "department": department,
        "total_agents": len(department_agents),
        "busy_agents": len(busy_agents),
        "idle_agents": len(idle_agents),
        "managers": len(managers),
        "queued_tasks": len(queued_tasks),
        "in_progress_tasks": len(
            [
                task
                for task in department_tasks
                if task.status
                in ["assigned", "in_progress", "review"]
            ]
        ),
        "completed_tasks": len(
            [
                task
                for task in department_tasks
                if task.status == "completed"
            ]
        ),
        "failed_tasks": len(
            [
                task
                for task in department_tasks
                if task.status == "failed"
            ]
        ),
        "workload_score": workload_score,
    }


def build_agent_workload(
    world: World,
    agent,
) -> dict:
    current_task = (
        world.tasks.get(agent.current_task_id)
        if agent.current_task_id
        else None
    )

    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "department": agent.department,
        "status": agent.status,
        "current_task_id": agent.current_task_id,
        "current_task_title": (
            current_task.title
            if current_task
            else None
        ),
        "workload": agent.workload,
        "performance_score": agent.performance_score,
        "capabilities": agent.capabilities,
        "recent_activity_count": len(
            [
                entry
                for entry in world.activity_log
                if entry.get("agent_id") == agent.id
            ][-10:]
        ),
    }


def recent_entries(
    world: World,
    types: set[str],
    limit: int,
    since: float | None = None,
) -> list[dict]:
    combined = [
        entry
        for entry in world.events
        if entry.get("type") in types
    ] + [
        entry
        for entry in world.activity_log
        if entry.get("type") in types
    ]

    if since is not None:
        combined = [
            entry
            for entry in combined
            if entry.get(
                "ts",
                entry.get("timestamp", 0),
            )
            >= since
        ]

    return sorted(
        combined,
        key=lambda item: item.get(
            "ts",
            item.get("timestamp", 0),
        ),
        reverse=True,
    )[:limit]


def build_queue_health(
    queued_tasks: int,
    in_progress_tasks: int,
    failed_recent: int,
    available_agents: int,
) -> str:
    if failed_recent > 0:
        return "blocked"

    if queued_tasks > 0 and available_agents == 0:
        return "blocked"

    if queued_tasks > available_agents * 2:
        return "overloaded"

    if in_progress_tasks > available_agents:
        return "busy"

    return "healthy"
