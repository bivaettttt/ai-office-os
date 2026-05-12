from __future__ import annotations

from pydantic import BaseModel

from app.core.agent_runtime.capabilities import (
    default_capabilities_for_department,
)


class DepartmentDefinition(BaseModel):
    id: str
    display_name: str
    manager_role: str
    default_worker_roles: list[str]
    default_capabilities: list[str]


DEPARTMENT_DEFINITIONS: dict[str, DepartmentDefinition] = {
    "development": DepartmentDefinition(
        id="development",
        display_name="Development",
        manager_role="Engineering Manager",
        default_worker_roles=[
            "Frontend Engineer",
            "Backend Engineer",
        ],
        default_capabilities=default_capabilities_for_department(
            "development"
        ),
    ),
    "analytics": DepartmentDefinition(
        id="analytics",
        display_name="Analytics",
        manager_role="Analytics Manager",
        default_worker_roles=[
            "Market Analyst",
            "Research Specialist",
        ],
        default_capabilities=default_capabilities_for_department(
            "analytics"
        ),
    ),
    "assistant": DepartmentDefinition(
        id="assistant",
        display_name="Assistant",
        manager_role="Operations Assistant Manager",
        default_worker_roles=[
            "Executive Assistant",
            "Communication Assistant",
        ],
        default_capabilities=default_capabilities_for_department(
            "assistant"
        ),
    ),
    "content": DepartmentDefinition(
        id="content",
        display_name="Content",
        manager_role="Content Manager",
        default_worker_roles=[
            "Content Writer",
            "SEO Specialist",
        ],
        default_capabilities=default_capabilities_for_department(
            "content"
        ),
    ),
    "operations": DepartmentDefinition(
        id="operations",
        display_name="Operations",
        manager_role="Operations Manager",
        default_worker_roles=[
            "Operations Coordinator",
            "Project Coordinator",
        ],
        default_capabilities=default_capabilities_for_department(
            "operations"
        ),
    ),
}


def get_department_definition(
    department: str,
) -> DepartmentDefinition | None:
    return DEPARTMENT_DEFINITIONS.get(department)
