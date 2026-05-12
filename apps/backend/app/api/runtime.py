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
