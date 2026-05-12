from app.core.factory import (
    create_agent,
    create_department,
)


department = create_department(
    name="Development",
    description="Software engineering department",
)


manager = create_agent(
    name="Алексей",
    role="Development Manager",
    department="development",
    personality="strategic",
    x=220,
    y=120,
)

department.manager_agent_id = manager.id


backend_dev = create_agent(
    name="Мария",
    role="Backend Engineer",
    department="development",
    personality="analytical",
    x=320,
    y=220,
)

frontend_dev = create_agent(
    name="Игорь",
    role="Frontend Engineer",
    department="development",
    personality="creative",
    x=420,
    y=220,
)


department.agents.extend([
    manager.id,
    backend_dev.id,
    frontend_dev.id,
])