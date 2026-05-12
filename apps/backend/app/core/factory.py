from app.models.agent import Agent
from app.models.task import Task
from app.models.department import Department

from app.core.world import world
from app.core.agent_runtime.capabilities import (
    default_capabilities_for_department,
    infer_required_capabilities,
    normalize_capabilities,
)
from app.core.agent_runtime.planning import (
    generate_task_steps,
)


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
    capabilities: list[str] | None = None,
    is_manager: bool = False,
    manager_for_department: str | None = None,
):

    agent = Agent(
        name=name,
        role=role,
        department=department,
        personality=personality,
        position_x=x,
        position_y=y,
        capabilities=normalize_capabilities(
            capabilities
            or default_capabilities_for_department(
                department
            )
        ),
        is_manager=is_manager,
        manager_for_department=manager_for_department,
    )

    world.add_agent(agent)

    return agent


def create_task(
    title: str,
    description: str,
    department: str,
    priority: str = "normal",
    required_capabilities: list[str] | None = None,
):

    steps = generate_task_steps(department)

    task = Task(
        title=title,
        description=description,
        department=department,
        priority=priority,
        plan=[step.title for step in steps],
        steps=steps,
        required_capabilities=normalize_capabilities(
            required_capabilities
            or infer_required_capabilities(
                f"{title} {description}",
                department,
            )
        ),
    )

    world.add_task(task)

    return task
