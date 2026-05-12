from fastapi import APIRouter
from pydantic import BaseModel

from app.runtime.project_runner import (
    start_project,
    stop_project,
    restart_project,
    get_runtime_status,
    get_runtime_logs,
)
from app.core.runtime_metrics import (
    build_runtime_metrics,
)
from app.core.runtime_timeline import (
    build_runtime_timeline,
)
from app.core.world import world

router = APIRouter()


class RuntimeStartRequest(BaseModel):
    project_path: str


@router.post("/runtime/start")
def runtime_start(data: RuntimeStartRequest):
    return start_project(
        project_path=data.project_path,
    )


@router.post("/runtime/stop")
def runtime_stop():
    return stop_project()


@router.post("/runtime/restart")
def runtime_restart():
    return restart_project()


@router.get("/runtime/status")
def runtime_status():
    return get_runtime_status()


@router.get("/runtime/logs")
def runtime_logs():
    return get_runtime_logs()


@router.get("/runtime/metrics")
def runtime_metrics():
    return build_runtime_metrics(world)


@router.get("/runtime/timeline")
def runtime_timeline(
    task_id: str | None = None,
    command_id: str | None = None,
    agent_id: str | None = None,
    department: str | None = None,
    severity: str | None = None,
    limit: int = 100,
):
    return build_runtime_timeline(
        world,
        task_id=task_id,
        command_id=command_id,
        agent_id=agent_id,
        department=department,
        severity=severity,
        limit=limit,
    )
