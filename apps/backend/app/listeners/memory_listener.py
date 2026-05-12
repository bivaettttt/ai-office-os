from app.orchestration.event_bus import (
    event_bus,
)

from app.orchestration.events import (
    TASK_STARTED,
    TASK_COMPLETED,
    TASK_FAILED,
    AGENT_RECOVERED,
)

from app.memory.shared_memory import (
    shared_memory,
)


# =========================================================
# TASK STARTED
# =========================================================

async def on_task_started(data):

    agent = data.get("agent")

    task = data.get("task")

    shared_memory.add_event(
        f"{agent} начал задачу: {task}"
    )


# =========================================================
# TASK COMPLETED
# =========================================================

async def on_task_completed(data):

    agent = data.get("agent")

    shared_memory.add_event(
        f"{agent} завершил задачу"
    )


# =========================================================
# TASK FAILED
# =========================================================

async def on_task_failed(data):

    agent = data.get("agent")

    shared_memory.add_event(
        f"{agent} столкнулся с ошибкой"
    )


# =========================================================
# AGENT RECOVERED
# =========================================================

async def on_agent_recovered(data):

    agent = data.get("agent")

    shared_memory.add_event(
        f"{agent} восстановил работу"
    )


# =========================================================
# REGISTER
# =========================================================

def register_memory_listeners():

    event_bus.subscribe(
        TASK_STARTED,
        on_task_started,
    )

    event_bus.subscribe(
        TASK_COMPLETED,
        on_task_completed,
    )

    event_bus.subscribe(
        TASK_FAILED,
        on_task_failed,
    )

    event_bus.subscribe(
        AGENT_RECOVERED,
        on_agent_recovered,
    )