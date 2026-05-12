from __future__ import annotations

from pathlib import Path

from app.memory.agent_memory import agent_memory
from app.tools.shell_tool import run_command


LOG_LIMIT = 100


def _normalize_cwd(cwd: str | None) -> str | None:
    if not cwd:
        return None

    try:
        return str(Path(cwd).expanduser().resolve())
    except Exception:
        return None


def _push_log(message: str):
    logs = agent_memory.setdefault("logs", [])
    logs.append(message)
    agent_memory["logs"] = logs[-LOG_LIMIT:]


def run_terminal_command(command: str, cwd: str | None = None):
    command = command.strip()

    if not command:
        return {
            "stdout": "",
            "stderr": "Пустая команда",
            "code": 1,
            "command": command,
            "cwd": cwd,
        }

    agent_memory["terminal"].update(
        {
            "status": "working",
            "task": command,
            "phase": "running",
        }
    )

    agent_memory["active_agent"] = "terminal"

    _push_log(f"[TERMINAL] {command}")

    result = run_command(
        command=command,
        cwd=_normalize_cwd(cwd),
    )

    status = "done" if result.get("code") == 0 else "error"

    agent_memory["terminal"].update(
        {
            "status": status,
            "task": command,
            "phase": "idle",
        }
    )

    agent_memory["active_agent"] = "none"

    return result