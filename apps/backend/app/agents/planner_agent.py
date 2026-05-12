from __future__ import annotations

import json
import re
from typing import Any

import ollama

from app.memory.agent_memory import agent_memory


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9]*\n?", "", cleaned)
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

    return cleaned.strip()


def _extract_json(text: str) -> dict[str, Any] | None:
    cleaned = _strip_code_fence(text)

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            return None

    return None


def _fallback_plan(task: str) -> dict[str, Any]:
    lower = task.lower()

    steps = [
        "Определить цель проекта и ключевой сценарий пользователя",
        "Провести короткое исследование рынка и конкурентов",
        "Сформировать архитектуру MVP",
        "Сгенерировать файлы проекта и базовый интерфейс",
        "Проверить ошибки и подготовить проект к запуску",
    ]

    if any(word in lower for word in ["crm", "продаж", "sales"]):
        steps.insert(1, "Понять структуру CRM: лиды, сделки, контакты, аналитика")

    if any(word in lower for word in ["маркет", "marketing", "продвиж"]):
        steps.append("Добавить маркетинговые сценарии и каналы привлечения")

    return {
        "goal": f"Собрать AI-проект под задачу: {task}",
        "steps": steps,
        "agents": [
            "Planner Agent",
            "Research Agent",
            "Manager Agent",
            "Coder Agent",
            "Debug Agent",
            "Terminal Agent",
        ],
        "expected_output": "План, архитектура, runnable-проект и список файлов",
        "risks": [
            "Слишком сложный MVP",
            "Ошибки генерации кода",
            "Несовпадение структуры файлов",
        ],
    }


def _format_plan(plan: dict[str, Any]) -> str:
    goal = str(plan.get("goal", "План проекта"))
    steps = plan.get("steps", [])
    agents = plan.get("agents", [])
    expected_output = str(plan.get("expected_output", ""))
    risks = plan.get("risks", [])

    lines: list[str] = []
    lines.append("# Project Plan")
    lines.append("")
    lines.append("## Goal")
    lines.append(goal)
    lines.append("")
    lines.append("## Steps")

    if isinstance(steps, list):
        for idx, step in enumerate(steps, start=1):
            lines.append(f"{idx}. {step}")
    else:
        lines.append(str(steps))

    lines.append("")
    lines.append("## Agents")

    if isinstance(agents, list):
        for agent in agents:
            lines.append(f"- {agent}")
    else:
        lines.append(str(agents))

    lines.append("")
    lines.append("## Expected Output")
    lines.append(expected_output)
    lines.append("")
    lines.append("## Risks")

    if isinstance(risks, list):
        for risk in risks:
            lines.append(f"- {risk}")
    else:
        lines.append(str(risks))

    return "\n".join(lines).strip()


def create_plan(task: str) -> dict[str, Any]:
    agent_memory["planner"].update(
        {
            "status": "working",
            "task": "Разбиение задачи на этапы",
            "phase": "planning",
        }
    )
    agent_memory["active_agent"] = "planner"

    prompt = f"""
Ты Planner Agent AI OS.

Нужно спланировать задачу:
{task}

Верни ТОЛЬКО JSON без markdown и без пояснений.

Формат:
{{
  "goal": "Короткая цель проекта",
  "steps": [
    "Шаг 1",
    "Шаг 2",
    "Шаг 3"
  ],
  "agents": [
    "Planner Agent",
    "Research Agent",
    "Manager Agent",
    "Coder Agent",
    "Debug Agent",
    "Terminal Agent"
  ],
  "expected_output": "Что должно получиться",
  "risks": [
    "Риск 1",
    "Риск 2"
  ]
}}
""".strip()

    raw = ""
    plan_data: dict[str, Any] | None = None

    try:
        response = ollama.chat(
            model="phi3:mini",
            messages=[
                {
                    "role": "system",
                    "content": "Отвечай только на русском языке и возвращай строгий JSON.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            options={
                "temperature": 0.3,
                "num_predict": 700,
            },
        )
        raw = response.get("message", {}).get("content", "").strip()
        plan_data = _extract_json(raw)
    except Exception as e:
        raw = f"Ошибка Planner Agent: {str(e)}"

    if plan_data is None:
        plan_data = _fallback_plan(task)

    content = _format_plan(plan_data)

    agent_memory["last_plan"] = plan_data
    agent_memory["planner"].update(
        {
            "status": "done",
            "task": "План готов",
            "phase": "idle",
        }
    )
    agent_memory["active_agent"] = "none"

    return {
        "content": content,
        "data": plan_data,
        "raw": raw,
    }