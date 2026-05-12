from fastapi import APIRouter
from pydantic import BaseModel

from app.core.world import world

from app.core.factory import create_task


router = APIRouter()


# =========================================================
# REQUESTS
# =========================================================

class CreateTaskRequest(BaseModel):
    title: str
    description: str
    department: str


# =========================================================
# WORLD
# =========================================================

@router.get("/world")
def get_world():

    return world.serialize()


# =========================================================
# TASKS
# =========================================================

@router.post("/world/task")
def create_world_task(data: CreateTaskRequest):

    task = create_task(
        title=data.title,
        description=data.description,
        department=data.department,
    )

    return {
        "status": "created",
        "task": task,
    }