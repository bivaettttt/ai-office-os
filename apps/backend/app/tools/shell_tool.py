from __future__ import annotations

import subprocess


DEFAULT_TIMEOUT = 120


def run_command(
    command: str,
    cwd: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "code": result.returncode,
            "command": command,
            "cwd": cwd,
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Command timeout after {timeout} seconds",
            "code": 124,
            "command": command,
            "cwd": cwd,
        }

    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "code": 1,
            "command": command,
            "cwd": cwd,
        }