from __future__ import annotations

from app.runtime.project_runner import start_project


class RuntimeAgent:
    def run_project(self, project_id: str, command: str, cwd: str, port: int):
        return start_project(
            project_id=project_id,
            command=command,
            cwd=cwd,
            port=port,
        )


runtime_agent = RuntimeAgent()