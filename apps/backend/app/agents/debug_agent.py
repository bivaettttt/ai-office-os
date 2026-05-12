from __future__ import annotations

import re
from pathlib import Path

import ollama

from app.memory.agent_memory import agent_memory
from app.tools.file_tool import save_file

MODEL_NAME = "phi3:mini"


def extract_error_file(logs: str):
    patterns = [
        r'File "(.+?)", line (\d+)',
        r"\./(.+?) \((\d+):(\d+)\)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, logs)

        if matches:
            match = matches[-1]

            if len(match) >= 2:
                return match[0], int(match[1])

    return None, None


def read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""


def build_fix_prompt(
    task: str,
    logs: str,
    file_path: str,
    file_content: str,
):
    return f"""
Ты elite senior engineer.

Нужно исправить ошибку в проекте.

ВАЖНО:
- Верни ТОЛЬКО полный исправленный код
- Без markdown
- Без пояснений
- Код должен быть полностью валидным
- JSX должен быть корректным
- TypeScript должен компилироваться
- Next.js 15 compatible
- Не сокращай код
- Не используй placeholders

ЗАДАЧА:
{task}

ОШИБКА:
{logs}

ФАЙЛ:
{file_path}

КОД:
{file_content}
""".strip()


async def fix_traceback(
    traceback_text: str,
    project_folder: str | None = None,
):
    agent_memory["debug"].update(
        {
            "status": "working",
            "task": "Исправление ошибки",
            "phase": "debugging",
        }
    )

    file_path, line_number = extract_error_file(traceback_text)

    if not file_path:
        agent_memory["debug"]["status"] = "error"

        return {
            "status": "error",
            "message": "Не удалось определить файл ошибки",
        }

    if project_folder and not file_path.startswith("/"):
        file_path = str(Path(project_folder) / file_path)

    file_content = read_file(file_path)

    if not file_content:
        agent_memory["debug"]["status"] = "error"

        return {
            "status": "error",
            "message": "Не удалось прочитать файл",
            "file": file_path,
        }

    task = "AI OS autonomous debugging"

    prompt = build_fix_prompt(
        task=task,
        logs=traceback_text,
        file_path=file_path,
        file_content=file_content,
    )

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": """
Ты AI debugging agent.

Ты исправляешь production код.
Ты обязан возвращать только валидный код.
""",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            options={
                "temperature": 0.1,
                "num_predict": 4000,
            },
        )

        fixed_code = response["message"]["content"].strip()

        if fixed_code.startswith("```"):
            fixed_code = fixed_code.replace("```tsx", "")
            fixed_code = fixed_code.replace("```ts", "")
            fixed_code = fixed_code.replace("```python", "")
            fixed_code = fixed_code.replace("```", "")

        save_file(file_path, fixed_code)

        agent_memory["debug"].update(
            {
                "status": "done",
                "task": "Ошибка исправлена",
                "phase": "idle",
            }
        )

        return {
            "status": "success",
            "message": "Файл автоматически исправлен",
            "file": file_path,
            "line": line_number,
        }

    except Exception as e:
        agent_memory["debug"].update(
            {
                "status": "error",
                "task": "Ошибка debug agent",
                "phase": "idle",
            }
        )

        return {
            "status": "error",
            "message": str(e),
        }