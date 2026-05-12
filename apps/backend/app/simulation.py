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

                agent.task_progress += progress

                task = None

                if agent.current_task_id:

                    task = (
                        world_state.tasks.get(
                            agent.current_task_id
                        )
                    )

                    if task:

                        task.progress = (
                            agent.task_progress
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
                        task.updated_at = time.time()

                    agent.current_task_id = None
                    agent.task_progress = 0

                # COMPLETE

                elif agent.task_progress >= 100:

                    agent.task_progress = 100

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

                    if task:

                        task.progress = 100

                        task.status = (
                            "completed"
                        )
                        task.completed_at = time.time()
                        task.updated_at = time.time()

                        task.result = (
                            f"{agent.name} завершил задачу"
                        )

                    agent.current_task_id = None

                    agent.task_progress = 0

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
