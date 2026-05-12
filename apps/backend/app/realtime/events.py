from app.orchestration.event_bus import (
    event_bus,
)


# =========================================================
# AGENT STATUS
# =========================================================

async def emit_agent_status(
    agent_name: str,
    status: str,
    task: str,
    phase: str,
):

    await event_bus.emit(
        "agent.status",
        {
            "agent": agent_name,
            "status": status,
            "task": task,
            "phase": phase,
        },
    )


# =========================================================
# TASK STARTED
# =========================================================

async def emit_task_started(
    agent_name: str,
    task_title: str,
):

    await event_bus.emit(
        "task.started",
        {
            "agent": agent_name,
            "task": task_title,
        },
    )


# =========================================================
# TASK COMPLETED
# =========================================================

async def emit_task_completed(
    agent_name: str,
    task_title: str,
):

    await event_bus.emit(
        "task.completed",
        {
            "agent": agent_name,
            "task": task_title,
        },
    )


# =========================================================
# TASK FAILED
# =========================================================

async def emit_task_failed(
    agent_name: str,
    task_title: str,
):

    await event_bus.emit(
        "task.failed",
        {
            "agent": agent_name,
            "task": task_title,
        },
    )