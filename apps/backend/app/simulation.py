import asyncio
import random
import time

from app.orchestration.event_bus import (
    event_bus,
)

from app.orchestration.events import (
    TASK_COMPLETED,
    TASK_FAILED,
    AGENT_RECOVERED,
)
from app.core.agent_runtime.execution import (
    advance_task_steps,
    all_steps_completed,
    review_completed_task,
)
from app.models.task import TaskStepStatus

# =========================================================
# ROOM BOUNDS
# =========================================================

ROOM_BOUNDS = {

    "development": {
        "x1": 60,
        "x2": 520,
        "y1": 80,
        "y2": 340,
    },

    "analytics": {
        "x1": 60,
        "x2": 520,
        "y1": 500,
        "y2": 760,
    },

    "assistant": {
        "x1": 780,
        "x2": 1240,
        "y1": 80,
        "y2": 340,
    },

    "content": {
        "x1": 780,
        "x2": 1240,
        "y1": 500,
        "y2": 760,
    },

    "operations": {
        "x1": 600,
        "x2": 820,
        "y1": 70,
        "y2": 330,
    },
}

# =========================================================
# ACTIONS
# =========================================================

AGENT_ACTIONS = {

    "development": [

        "Пишет backend",
        "Создает API",
        "Исправляет баг",
        "Рефакторит код",
        "Пишет тесты",
    ],

    "analytics": [

        "Анализирует рынок",
        "Собирает метрики",
        "Изучает конкурентов",
        "Готовит отчет",
    ],

    "assistant": [

        "Отвечает клиенту",
        "Планирует задачи",
        "Создает meeting",
        "Организует команду",
    ],

    "content": [

        "Пишет статью",
        "Создает контент",
        "Редактирует текст",
        "Готовит пост",
    ],

    "operations": [

        "Координирует процесс",
        "Проверяет качество",
        "Планирует выполнение",
        "Следит за нагрузкой",
    ],
}

# =========================================================
# HELPERS
# =========================================================

def clamp(
    value,
    minimum,
    maximum,
):

    return max(
        minimum,
        min(value, maximum)
    )

# =========================================================
# SIMULATION
# =========================================================

async def simulate_agents(world_state):

    while True:

        for agent in world_state.agents.values():

            room = ROOM_BOUNDS.get(
                agent.department
            )

            if not room:
                continue

            # RANDOM WALK

            if random.random() < 0.7:

                dx = random.randint(-8, 8)
                dy = random.randint(-8, 8)

                agent.position_x += dx
                agent.position_y += dy

            # ROOM LIMITS

            agent.position_x = clamp(
                agent.position_x,
                room["x1"],
                room["x2"],
            )

            agent.position_y = clamp(
                agent.position_y,
                room["y1"],
                room["y2"],
            )

            # IDLE

            if agent.status == "idle":

                actions = AGENT_ACTIONS.get(
                    agent.department,
                    ["Ожидает задачу"],
                )

                if random.random() < 0.03:

                    agent.current_action = (
                        random.choice(actions)
                    )

            # WORKING

            elif agent.status == "working":

                progress = random.randint(1, 6)

                task = None

                if agent.current_task_id:

                    task = (
                        world_state.tasks.get(
                            agent.current_task_id
                        )
                    )

                    if task:

                        step_events = advance_task_steps(
                            task,
                            agent.id,
                            progress,
                        )

                        agent.task_progress = task.progress
                        task.updated_at = time.time()
                        agent.last_active_at = time.time()

                        for step_event in step_events:
                            step = step_event["step"]

                            if (
                                step_event["type"]
                                == "step_started"
                            ):
                                await event_bus.emit(
                                    "task.step_started",
                                    {
                                        "task_id": task.id,
                                        "task_title": task.title,
                                        "step_id": step.id,
                                        "step_title": step.title,
                                        "agent_id": agent.id,
                                        "agent_name": agent.name,
                                    },
                                )
                                world_state.add_activity(
                                    agent.id,
                                    task.id,
                                    "step_started",
                                    (
                                        f"{agent.name} started step: "
                                        f"{step.title}"
                                    ),
                                )

                            if (
                                step_event["type"]
                                == "step_completed"
                            ):
                                await event_bus.emit(
                                    "task.step_completed",
                                    {
                                        "task_id": task.id,
                                        "task_title": task.title,
                                        "step_id": step.id,
                                        "step_title": step.title,
                                        "agent_id": agent.id,
                                        "agent_name": agent.name,
                                    },
                                )
                                world_state.add_activity(
                                    agent.id,
                                    task.id,
                                    "step_completed",
                                    (
                                        f"{agent.name} completed step: "
                                        f"{step.title}"
                                    ),
                                )
                        task.updated_at = time.time()

                # RANDOM FAILURE

                if random.random() < 0.003:

                    agent.status = "error"

                    agent.current_action = (
                        "Столкнулся с ошибкой"
                    )

                    await event_bus.emit(

                        TASK_FAILED,

                        {
                            "agent": agent.name,
                            "task": (
                                task.title
                                if task
                                else None
                            ),
                        }
                    )

                    if task:
                        task.status = "failed"
                        task.failure_reason = (
                            "Visual simulation failure"
                        )
                        task.updated_at = time.time()
                        if task.steps:
                            active_step = task.steps[
                                task.active_step_index
                            ]
                            active_step.status = (
                                TaskStepStatus.FAILED
                            )
                            active_step.completed_at = time.time()
                        world_state.add_activity(
                            agent.id,
                            task.id,
                            "task_failed",
                            (
                                f"{agent.name} failed task: "
                                f"{task.title}"
                            ),
                        )

                    agent.current_task_id = None
                    agent.task_progress = 0
                    agent.workload = max(0, agent.workload - 1)
                    agent.last_active_at = time.time()

                # COMPLETE

                elif task and all_steps_completed(task):

                    agent.task_progress = 100

                    task.status = "review"
                    task.updated_at = time.time()

                    await event_bus.emit(
                        "manager.review_started",
                        {
                            "manager_id": (
                                task.assigned_by_manager_id
                            ),
                            "task_id": task.id,
                            "task_title": task.title,
                        },
                    )

                    summary = review_completed_task(
                        task,
                        agent.name,
                    )

                    await event_bus.emit(
                        "task.reviewed",
                        {
                            "manager_id": (
                                task.assigned_by_manager_id
                            ),
                            "task_id": task.id,
                            "task_title": task.title,
                            "summary": summary,
                        },
                    )

                    world_state.add_activity(
                        task.assigned_by_manager_id,
                        task.id,
                        "task_reviewed",
                        summary,
                    )

                    agent.status = "idle"

                    agent.current_action = (
                        "Ожидает задачу"
                    )

                    await event_bus.emit(

                        TASK_COMPLETED,

                        {
                            "agent": agent.name,
                            "task": (
                                task.title
                                if task
                                else None
                            ),
                        }
                    )

                    world_state.add_activity(
                        agent.id,
                        task.id,
                        "task_completed",
                        summary,
                    )

                    agent.current_task_id = None

                    agent.task_progress = 0
                    agent.workload = max(0, agent.workload - 1)
                    agent.last_active_at = time.time()

            # ERROR

            elif agent.status == "error":

                if random.random() < 0.15:

                    agent.status = "idle"

                    agent.current_action = (
                        "Восстановлен после ошибки"
                    )

                    await event_bus.emit(

                        AGENT_RECOVERED,

                        {
                            "agent": agent.name,
                        }
                    )

        await asyncio.sleep(0.12)
