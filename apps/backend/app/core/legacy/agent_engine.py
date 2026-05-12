from __future__ import annotations

"""Deprecated legacy agent engine.

This module is intentionally not imported by the application. The current
runtime uses app.simulation and app.core.orchestration instead.
"""

import random
import threading
import time

from app.core.world import world

from app.models.agent import Agent


AGENT_THOUGHTS = [
    "Analyzing task",
    "Thinking",
    "Reviewing architecture",
    "Writing report",
    "Searching internet",
    "Planning execution",
    "Reading documentation",
    "Optimizing solution",
    "Communicating with manager",
    "Reviewing code",
]


# =========================================================
# MOVEMENT
# =========================================================

def move_agent(agent: Agent):

    dx = random.randint(-20, 20)
    dy = random.randint(-20, 20)

    agent.position_x += dx
    agent.position_y += dy

    agent.position_x = max(
        40,
        min(1600, agent.position_x),
    )

    agent.position_y = max(
        40,
        min(900, agent.position_y),
    )


# =========================================================
# TASK ASSIGNMENT
# =========================================================

def assign_tasks():

    tasks = list(world.tasks.values())

    agents = list(world.agents.values())

    for task in tasks:

        if task.status != "created":
            continue

        available_agents = [
            agent
            for agent in agents
            if (
                agent.department == task.department
                and agent.status == "idle"
            )
        ]

        if not available_agents:
            continue

        agent = random.choice(
            available_agents
        )

        task.assigned_to = agent.id

        task.status = "in_progress"

        agent.status = "working"

        agent.current_task_id = task.id

        agent.current_action = (
            f"Working on: {task.title}"
        )

        world.events.append({
            "type": "task_assigned",
            "agent": agent.name,
            "task": task.title,
            "timestamp": time.time(),
        })


# =========================================================
# AGENT PROCESSING
# =========================================================

def process_agents():

    agents = list(world.agents.values())

    tasks = world.tasks

    for agent in agents:

        move_agent(agent)

        # =============================================
        # IDLE
        # =============================================

        if agent.status == "idle":

            agent.current_action = (
                random.choice(
                    AGENT_THOUGHTS
                )
            )

        # =============================================
        # WORKING
        # =============================================

        elif agent.status == "working":

            if random.random() > 0.96:

                task = tasks.get(
                    agent.current_task_id
                )

                if task:

                    task.status = "completed"

                    task.result = (
                        f"Task completed by "
                        f"{agent.name}"
                    )

                    world.events.append({
                        "type": "task_completed",
                        "agent": agent.name,
                        "task": task.title,
                        "timestamp": time.time(),
                    })

                agent.status = "idle"

                agent.current_task_id = None

                agent.current_action = "Idle"

        agent.last_update = time.time()


# =========================================================
# LOOP
# =========================================================

def simulation_loop():

    while True:

        try:

            assign_tasks()

            process_agents()

            time.sleep(2)

        except Exception as e:

            print(
                "AGENT LOOP ERROR:",
                e,
            )

            time.sleep(3)


# =========================================================
# START
# =========================================================

def start_agent_engine():

    thread = threading.Thread(
        target=simulation_loop,
        daemon=True,
    )

    thread.start()

    print(
        "AI AGENT ENGINE STARTED"
    )
