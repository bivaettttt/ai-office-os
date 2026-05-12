import ollama

from app.memory.agent_memory import agent_memory


def research_agent(task: str) -> str:
    agent_memory["research"].update(
        {
            "status": "researching",
            "task": "Анализ идеи и рынка",
            "phase": "working",
        }
    )
    agent_memory["active_agent"] = "research"

    prompt = f"""
Ты AI Research Agent.

Проанализируй идею стартапа:

{task}

Ответь на русском языке.
Сформируй кратко и по делу:

1. Рынок
2. Конкуренты
3. Целевая аудитория
4. MVP
5. Монетизация
6. Риски
7. Возможности роста
""".strip()

    try:
        response = ollama.chat(
            model="phi3:mini",
            messages=[
                {
                    "role": "system",
                    "content": "Отвечай только на русском языке.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            options={
                "temperature": 0.4,
                "num_predict": 700,
            },
        )
        content = response["message"]["content"].strip()

        agent_memory["research"].update(
            {
                "status": "done",
                "task": "Анализ завершен",
                "phase": "idle",
            }
        )
        agent_memory["active_agent"] = "none"
        return content

    except Exception as e:
        agent_memory["research"].update(
            {
                "status": "error",
                "task": "Ошибка анализа",
                "phase": "idle",
            }
        )
        agent_memory["active_agent"] = "none"
        return f"Ошибка Research Agent: {str(e)}"