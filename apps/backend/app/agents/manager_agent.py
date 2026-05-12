from __future__ import annotations

import ollama
import asyncio

from app.agents.coder_agent import (
    coder_agent,
)

from app.agents.planner_agent import (
    create_plan,
)

from app.agents.research_agent import (
    research_agent,
)

from app.memory.agent_memory import (
    agent_memory,
)

from app.realtime.events import (
    emit_agent_status,
)


MODEL_NAME = "phi3:mini"


class ManagerAgent:

    def __init__(self):

        self.model = MODEL_NAME

    # =====================================================
    # LOGGING
    # =====================================================

    def _log(self, text: str):

        logs = agent_memory.setdefault(
            "logs",
            [],
        )

        logs.append(text)

        agent_memory["logs"] = logs[-100:]

    # =====================================================
    # RESET
    # =====================================================

    def _reset_runtime_state(self):

        agent_memory["logs"] = []

        agent_memory["active_agent"] = "none"

        agent_memory["last_response"] = ""

        agent_memory[
            "last_saved_project"
        ] = {}

        agent_memory["last_plan"] = {}

        agent_memory["project_tree"] = []

    # =====================================================
    # AGENTS
    # =====================================================

    def get_agents(self):

        return [
            {
                "name": "Planner Agent",
                "status": agent_memory[
                    "planner"
                ]["status"],
                "task": agent_memory[
                    "planner"
                ]["task"],
                "phase": agent_memory[
                    "planner"
                ]["phase"],
                "color": "yellow",
            },
            {
                "name": "Manager Agent",
                "status": agent_memory[
                    "manager"
                ]["status"],
                "task": agent_memory[
                    "manager"
                ]["task"],
                "phase": agent_memory[
                    "manager"
                ]["phase"],
                "color": "green",
            },
            {
                "name": "Research Agent",
                "status": agent_memory[
                    "research"
                ]["status"],
                "task": agent_memory[
                    "research"
                ]["task"],
                "phase": agent_memory[
                    "research"
                ]["phase"],
                "color": "purple",
            },
            {
                "name": "Coder Agent",
                "status": agent_memory[
                    "coder"
                ]["status"],
                "task": agent_memory[
                    "coder"
                ]["task"],
                "phase": agent_memory[
                    "coder"
                ]["phase"],
                "color": "cyan",
            },
            {
                "name": "Debug Agent",
                "status": agent_memory[
                    "debug"
                ]["status"],
                "task": agent_memory[
                    "debug"
                ]["task"],
                "phase": agent_memory[
                    "debug"
                ]["phase"],
                "color": "red",
            },
            {
                "name": "Terminal Agent",
                "status": agent_memory[
                    "terminal"
                ]["status"],
                "task": agent_memory[
                    "terminal"
                ]["task"],
                "phase": agent_memory[
                    "terminal"
                ]["phase"],
                "color": "orange",
            },
        ]

    # =====================================================
    # ARCHITECTURE
    # =====================================================

    async def _build_architecture(
        self,
        task: str,
        plan_text: str,
        research: str,
    ):

        await emit_agent_status(
            "Manager Agent",
            "working",
            task,
            "architecture",
        )

        prompt = f'''
Ты AI CTO.

Создай архитектуру проекта.

ЗАДАЧА:
{task}

ПЛАН:
{plan_text}

ИССЛЕДОВАНИЕ:
{research}

Нужно:
- backend
- frontend
- database
- deployment
- roadmap
'''.strip()

        try:

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Отвечай на русском языке.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 900,
                },
            )

            return response[
                "message"
            ]["content"].strip()

        except Exception as e:

            return (
                f"Ошибка Manager Agent: "
                f"{str(e)}"
            )

    # =====================================================
    # PROCESS
    # =====================================================

    async def process(
        self,
        message: str,
    ):

        self._reset_runtime_state()

        # =====================================
        # MANAGER START
        # =====================================

        agent_memory["manager"].update(
            {
                "status": "working",
                "task": message,
                "phase": "orchestration",
            }
        )

        await emit_agent_status(
            "Manager Agent",
            "working",
            message,
            "orchestration",
        )

        # =====================================
        # PLANNER
        # =====================================

        self._log(
            "Planner Agent started"
        )

        await emit_agent_status(
            "Planner Agent",
            "working",
            message,
            "planning",
        )

        plan = create_plan(message)

        await asyncio.sleep(1)

        # =====================================
        # RESEARCH
        # =====================================

        self._log(
            "Research Agent started"
        )

        await emit_agent_status(
            "Research Agent",
            "working",
            message,
            "research",
        )

        research = research_agent(
            message
        )

        await asyncio.sleep(1)

        # =====================================
        # ARCHITECTURE
        # =====================================

        self._log(
            "Architecture started"
        )

        architecture = (
            await self._build_architecture(
                message,
                plan["content"],
                research,
            )
        )

        await asyncio.sleep(1)

        # =====================================
        # CODER
        # =====================================

        self._log(
            "Coder Agent started"
        )

        await emit_agent_status(
            "Coder Agent",
            "working",
            message,
            "coding",
        )

        result = coder_agent(
            message,
            architecture,
            research,
        )

        await asyncio.sleep(1)

        # =====================================
        # FINAL RESPONSE
        # =====================================

        final_response = f'''
# AI STARTUP REPORT

## TASK
{message}

## PLAN
{plan['content']}

## RESEARCH
{research}

## ARCHITECTURE
{architecture}

## RESULT
{result['content']}
'''.strip()

        agent_memory[
            "last_response"
        ] = final_response

        # =====================================
        # COMPLETE
        # =====================================

        agent_memory["manager"].update(
            {
                "status": "done",
                "task": "Завершено",
                "phase": "idle",
            }
        )

        await emit_agent_status(
            "Manager Agent",
            "done",
            "Завершено",
            "idle",
        )

        return {
            "response": final_response,
            "plan": plan["content"],
            "logs": agent_memory[
                "logs"
            ],
            "agents": self.get_agents(),
            "saved": result["saved"],
        }