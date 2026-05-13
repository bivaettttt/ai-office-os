from __future__ import annotations

from app.core.world import World


ERROR_TYPES = {
    "task.failed",
    "task.step_failed",
    "task_failed",
    "step_failed",
    "command_failed",
    "manager_review_failed",
}

SUCCESS_TYPES = {
    "task.completed",
    "task.step_completed",
    "step_completed",
    "task_completed",
    "manager_review_approved",
    "command_task_created",
    "llm_reasoning_completed",
    "llm_reasoning_cache_hit",
    "llm_timeline_summary_generated",
    "llm_suggestion_approved",
    "llm_suggestion_applied",
}

WARNING_TYPES = {
    "capability_fallback_used",
    "task.paused",
    "task.cancelled",
    "task_retry_requested",
    "tool_approval_required",
    "tool_rejected",
    "grant_revoked",
    "grant_expired",
    "scoped_permission_missing",
    "approval_opened",
    "approval_scope_suggested",
    "approval_once_approved",
    "approval_grant_approved",
    "dry_run_requested",
    "dry_run_completed",
    "sandbox_contract_created",
    "sandbox_contract_blocked",
    "llm_provider_fallback_used",
    "llm_guardrail_blocked",
    "llm_reasoning_fallback_used",
    "llm_reasoning_blocked",
    "llm_reasoning_rate_limited",
    "llm_reasoning_schema_validation_failed",
    "llm_suggestion_created",
    "llm_suggestion_rejected",
    "llm_suggestion_expired",
}

MANAGER_TYPES = {
    "manager_selected_task",
    "manager_assigned_worker",
    "capability_match_found",
    "capability_fallback_used",
    "manager_review_approved",
    "manager_review_failed",
}

COMMAND_TYPES = {
    "command_received",
    "command_parsed",
    "command_routed",
    "command_task_created",
    "command_failed",
}

TOOL_TYPES = {
    "tool_requested",
    "tool_approval_required",
    "tool_approved",
    "tool_rejected",
    "tool_executed",
    "tool_blocked",
    "grant_created",
    "grant_revoked",
    "grant_expired",
    "policy_profile_applied",
    "scoped_permission_allowed",
    "scoped_permission_missing",
}

LLM_TYPES = {
    "llm_request_started",
    "llm_request_completed",
    "llm_request_failed",
    "llm_provider_fallback_used",
    "llm_guardrail_blocked",
    "llm_reasoning_started",
    "llm_reasoning_completed",
    "llm_reasoning_fallback_used",
    "llm_reasoning_blocked",
    "llm_reasoning_cache_hit",
    "llm_reasoning_rate_limited",
    "llm_reasoning_schema_validation_failed",
    "llm_timeline_summary_generated",
    "llm_suggestion_created",
    "llm_suggestion_approved",
    "llm_suggestion_rejected",
    "llm_suggestion_applied",
    "llm_suggestion_expired",
}


def build_runtime_timeline(
    world: World,
    task_id: str | None = None,
    command_id: str | None = None,
    agent_id: str | None = None,
    department: str | None = None,
    severity: str | None = None,
    limit: int = 100,
) -> dict:
    entries = collect_timeline_entries(world)

    if command_id:
        command = world.commands.get(command_id)
        related_task_id = (
            command.created_task_id
            if command
            else None
        )
        entries = [
            entry
            for entry in entries
            if (
                entry.get("related_command_id")
                == command_id
                or (
                    related_task_id
                    and entry.get("related_task_id")
                    == related_task_id
                )
            )
        ]

    if task_id:
        entries = [
            entry
            for entry in entries
            if entry.get("related_task_id") == task_id
        ]

    if agent_id:
        entries = [
            entry
            for entry in entries
            if entry.get("related_agent_id") == agent_id
        ]

    if department:
        entries = [
            entry
            for entry in entries
            if entry.get("metadata", {}).get(
                "department"
            )
            == department
        ]

    if severity:
        entries = [
            entry
            for entry in entries
            if entry["severity"] == severity
        ]

    entries = sorted(
        entries,
        key=lambda item: item["timestamp"],
        reverse=True,
    )

    return {
        "entries": entries[:limit],
        "filters_applied": {
            "task_id": task_id,
            "command_id": command_id,
            "agent_id": agent_id,
            "department": department,
            "severity": severity,
            "limit": limit,
        },
        "total": len(entries),
    }


def collect_timeline_entries(world: World) -> list[dict]:
    entries: list[dict] = []

    for command in world.commands.values():
        entries.append(
            {
                "id": f"command-{command.id}",
                "timestamp": command.created_at,
                "source_type": "command",
                "source_id": command.id,
                "event_type": command.status,
                "title": "Command received",
                "message": command.raw_text,
                "severity": (
                    "error"
                    if command.status == "failed"
                    else "info"
                ),
                "related_task_id": command.created_task_id,
                "related_command_id": command.id,
                "related_agent_id": None,
                "metadata": {
                    "department": command.inferred_department,
                    "priority": command.inferred_priority,
                    "capabilities": command.inferred_capabilities,
                    "error_message": command.error_message,
                },
            }
        )

        if command.processed_at:
            entries.append(
                {
                    "id": f"command-processed-{command.id}",
                    "timestamp": command.processed_at,
                    "source_type": "command",
                    "source_id": command.id,
                    "event_type": command.status,
                    "title": "Command processed",
                    "message": (
                        command.error_message
                        or f"Created task {command.created_task_id}"
                    ),
                    "severity": (
                        "error"
                        if command.status == "failed"
                        else "success"
                    ),
                    "related_task_id": command.created_task_id,
                    "related_command_id": command.id,
                    "related_agent_id": None,
                    "metadata": {
                        "department": command.inferred_department,
                        "priority": command.inferred_priority,
                    },
                }
            )

    command_by_task = {
        command.created_task_id: command.id
        for command in world.commands.values()
        if command.created_task_id
    }

    for task in world.tasks.values():
        entries.append(
            task_entry(
                task,
                "task.created",
                "Task created",
                task.title,
                task.created_at,
                command_by_task.get(task.id),
            )
        )

        if task.assigned_at:
            entries.append(
                task_entry(
                    task,
                    "task.assigned",
                    "Task assigned",
                    task.title,
                    task.assigned_at,
                    command_by_task.get(task.id),
                    agent_id=task.assigned_to,
                )
            )

        for step in task.steps:
            if step.started_at:
                entries.append(
                    task_entry(
                        task,
                        "task.step_started",
                        step.title,
                        step.description,
                        step.started_at,
                        command_by_task.get(task.id),
                        agent_id=step.assigned_agent_id,
                    )
                )
            if step.completed_at:
                entries.append(
                    task_entry(
                        task,
                        f"task.step_{step.status}",
                        step.title,
                        step.description,
                        step.completed_at,
                        command_by_task.get(task.id),
                        agent_id=step.assigned_agent_id,
                    )
                )

        if task.reviewed_at:
            entries.append(
                task_entry(
                    task,
                    "task.reviewed",
                    "Manager review",
                    task.result_summary or task.title,
                    task.reviewed_at,
                    command_by_task.get(task.id),
                    source_type="manager",
                    agent_id=task.assigned_by_manager_id,
                )
            )

        if task.completed_at:
            entries.append(
                task_entry(
                    task,
                    "task.completed",
                    "Task completed",
                    task.result_summary or task.title,
                    task.completed_at,
                    command_by_task.get(task.id),
                    agent_id=task.assigned_to,
                )
            )

    for event in world.events:
        entries.append(
            raw_entry(
                event,
                command_by_task,
            )
        )

    for activity in world.activity_log:
        entries.append(
            activity_entry(
                activity,
                command_by_task,
            )
        )

    for audit in world.tool_audit_log:
        entries.append(tool_audit_entry(audit))

    for log in world.llm_prompt_logs:
        entries.append(llm_log_entry(log))

    return entries


def task_entry(
    task,
    event_type: str,
    title: str,
    message: str,
    timestamp: float,
    command_id: str | None,
    source_type: str = "task",
    agent_id: str | None = None,
) -> dict:
    return {
        "id": f"{event_type}-{task.id}-{timestamp}",
        "timestamp": timestamp,
        "source_type": source_type,
        "source_id": task.id,
        "event_type": event_type,
        "title": title,
        "message": message,
        "severity": severity_for(event_type),
        "related_task_id": task.id,
        "related_command_id": command_id,
        "related_agent_id": agent_id,
        "metadata": {
            "department": task.department,
            "status": task.status,
            "runtime_phase": task.runtime_phase,
        },
    }


def raw_entry(
    event: dict,
    command_by_task: dict[str, str],
) -> dict:
    payload = event.get("payload", {})
    task_id = payload.get("task_id")
    command_id = (
        payload.get("command_id")
        or command_by_task.get(task_id)
    )
    agent_id = payload.get("agent_id") or payload.get("manager_id")
    event_type = event.get("type", "event")

    return {
        "id": f"event-{event_type}-{event.get('ts', 0)}",
        "timestamp": event.get("ts", 0),
        "source_type": source_for(event_type),
        "source_id": str(agent_id or command_id or task_id or event_type),
        "event_type": event_type,
        "title": event_type,
        "message": str(
            payload.get("task_title")
            or payload.get("agent_name")
            or payload.get("error")
            or event_type
        ),
        "severity": severity_for(event_type),
        "related_task_id": task_id,
        "related_command_id": command_id,
        "related_agent_id": agent_id,
        "metadata": payload,
    }


def activity_entry(
    activity: dict,
    command_by_task: dict[str, str],
) -> dict:
    task_id = activity.get("task_id")
    event_type = activity.get("type", "activity")

    return {
        "id": activity.get("id", f"activity-{event_type}"),
        "timestamp": activity.get("timestamp", 0),
        "source_type": source_for(event_type),
        "source_id": str(
            activity.get("agent_id")
            or task_id
            or event_type
        ),
        "event_type": event_type,
        "title": event_type,
        "message": activity.get("message", event_type),
        "severity": severity_for(event_type),
        "related_task_id": task_id,
        "related_command_id": command_by_task.get(task_id),
        "related_agent_id": activity.get("agent_id"),
        "metadata": activity,
    }


def tool_audit_entry(
    audit,
) -> dict:
    action_event_type = {
        "requested": "tool_requested",
        "policy_requires_approval": "tool_approval_required",
        "policy_blocked": "tool_blocked",
        "approved": "tool_approved",
        "rejected": "tool_rejected",
        "executed": "tool_executed",
        "failed": "tool_blocked",
        "grant_created": "grant_created",
        "grant_revoked": "grant_revoked",
        "grant_expired": "grant_expired",
        "policy_profile_applied": "policy_profile_applied",
        "scoped_permission_allowed": "scoped_permission_allowed",
        "scoped_permission_missing": "scoped_permission_missing",
        "approval_opened": "approval_opened",
        "approval_scope_suggested": "approval_scope_suggested",
        "approval_once_approved": "approval_once_approved",
        "approval_grant_approved": "approval_grant_approved",
        "dry_run_requested": "dry_run_requested",
        "dry_run_completed": "dry_run_completed",
        "sandbox_contract_created": "sandbox_contract_created",
        "sandbox_contract_blocked": "sandbox_contract_blocked",
    }.get(
        str(audit.action),
        f"tool_{audit.action}",
    )

    return {
        "id": f"tool-audit-{audit.id}",
        "timestamp": audit.timestamp,
        "source_type": "system",
        "source_id": audit.tool_id,
        "event_type": action_event_type,
        "title": action_event_type,
        "message": audit.message,
        "severity": severity_for(action_event_type),
        "related_task_id": audit.task_id,
        "related_command_id": None,
        "related_agent_id": audit.agent_id,
        "metadata": audit.model_dump(mode="json"),
    }


def llm_log_entry(
    log,
) -> dict:
    event_type = (
        "llm_request_completed"
        if log.status == "completed"
        else (
            "llm_guardrail_blocked"
            if log.status == "blocked"
            else "llm_request_failed"
        )
    )
    return {
        "id": f"llm-log-{log.id}",
        "timestamp": log.timestamp,
        "source_type": "system",
        "source_id": log.provider,
        "event_type": event_type,
        "title": event_type,
        "message": log.response_preview or log.error or log.prompt_preview,
        "severity": severity_for(event_type),
        "related_task_id": log.task_id,
        "related_command_id": log.command_id,
        "related_agent_id": log.agent_id,
        "metadata": log.model_dump(mode="json"),
    }


def severity_for(event_type: str) -> str:
    if event_type in ERROR_TYPES or "failed" in event_type:
        return "error"
    if event_type == "llm_guardrail_blocked":
        return "warning"
    if event_type in {"tool_blocked"}:
        return "error"
    if event_type in SUCCESS_TYPES or "completed" in event_type:
        return "success"
    if event_type in {
        "tool_executed",
        "tool_approved",
        "grant_created",
        "scoped_permission_allowed",
        "approval_once_approved",
        "approval_grant_approved",
        "dry_run_completed",
        "sandbox_contract_created",
    }:
        return "success"
    if event_type in {"sandbox_contract_blocked"}:
        return "error"
    if event_type in WARNING_TYPES or "cancelled" in event_type:
        return "warning"
    return "info"


def source_for(event_type: str) -> str:
    if event_type in COMMAND_TYPES:
        return "command"
    if event_type in LLM_TYPES:
        return "system"
    if event_type in TOOL_TYPES:
        return "system"
    if event_type in MANAGER_TYPES or event_type.startswith("manager"):
        return "manager"
    if event_type.startswith("agent"):
        return "agent"
    if event_type.startswith("task") or event_type.startswith("step"):
        return "task"
    return "system"
