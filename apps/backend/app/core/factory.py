from app.models.agent import Agent
from app.models.task import Task
from app.models.department import Department

from app.core.world import world


def create_department(
    name: str,
    description: str,
):

    department = Department(
        name=name,
        description=description,
    )

    world.add_department(department)

    return department


def create_agent(
    name: str,
    role: str,
    department: str,
    personality: str,
    x: int,
    y: int,
):

    agent = Agent(
        name=name,
        role=role,
        department=department,
        personality=personality,
        position_x=x,
        position_y=y,
    )

    world.add_agent(agent)

    return agent


def create_task(
    title: str,
    description: str,
    department: str,
    priority: str = "normal",
):

    task = Task(
        title=title,
        description=description,
        department=department,
        priority=priority,
    )

    world.add_task(task)

    return task
