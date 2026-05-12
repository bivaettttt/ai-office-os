from app.core.factory import (
    create_department,
    create_agent,
)


def bootstrap_world():

    # =====================================================
    # DEVELOPMENT
    # =====================================================

    development = create_department(
        name="development",
        description="Development Department",
    )

    development_manager = create_agent(
        name="Alex",
        role="Engineering Manager",
        department="development",
        personality="React expert",
        x=140,
        y=180,
        capabilities=[
            "code_generation",
            "code_review",
            "debugging",
            "task_planning",
            "quality_review",
            "project_management",
        ],
        is_manager=True,
        manager_for_department="development",
    )
    development.manager_agent_id = development_manager.id

    create_agent(
        name="Ethan",
        role="Backend Engineer",
        department="development",
        personality="Python architect",
        x=320,
        y=180,
    )

    # =====================================================
    # ASSISTANT
    # =====================================================

    assistant = create_department(
        name="assistant",
        description="Assistant Department",
    )

    assistant_manager = create_agent(
        name="Luna",
        role="Operations Assistant Manager",
        department="assistant",
        personality="Helpful and organized",
        x=860,
        y=180,
        capabilities=[
            "scheduling",
            "communication",
            "task_planning",
            "project_management",
        ],
        is_manager=True,
        manager_for_department="assistant",
    )
    assistant.manager_agent_id = assistant_manager.id

    create_agent(
        name="Mia",
        role="Communication Assistant",
        department="assistant",
        personality="Human-like communicator",
        x=1040,
        y=180,
    )

    # =====================================================
    # ANALYTICS
    # =====================================================

    analytics = create_department(
        name="analytics",
        description="Analytics Department",
    )

    analytics_manager = create_agent(
        name="Olivia",
        role="Analytics Manager",
        department="analytics",
        personality="Data-focused",
        x=140,
        y=600,
        capabilities=[
            "web_research",
            "data_analysis",
            "report_writing",
            "task_planning",
            "quality_review",
        ],
        is_manager=True,
        manager_for_department="analytics",
    )
    analytics.manager_agent_id = analytics_manager.id

    create_agent(
        name="Noah",
        role="Research Specialist",
        department="analytics",
        personality="Deep researcher",
        x=320,
        y=600,
    )

    # =====================================================
    # CONTENT
    # =====================================================

    content = create_department(
        name="content",
        description="Content Department",
    )

    content_manager = create_agent(
        name="Emma",
        role="Content Manager",
        department="content",
        personality="Creative writer",
        x=860,
        y=600,
        capabilities=[
            "content_writing",
            "report_writing",
            "communication",
            "task_planning",
            "quality_review",
        ],
        is_manager=True,
        manager_for_department="content",
    )
    content.manager_agent_id = content_manager.id

    create_agent(
        name="Sophia",
        role="SEO Specialist",
        department="content",
        personality="SEO optimizer",
        x=1040,
        y=600,
    )

    # =====================================================
    # OPERATIONS
    # =====================================================

    operations = create_department(
        name="operations",
        description="Operations Department",
    )

    operations_manager = create_agent(
        name="Grace",
        role="Operations Manager",
        department="operations",
        personality="Calm coordinator",
        x=650,
        y=180,
        capabilities=[
            "project_management",
            "task_planning",
            "communication",
            "quality_review",
        ],
        is_manager=True,
        manager_for_department="operations",
    )
    operations.manager_agent_id = operations_manager.id

    create_agent(
        name="Owen",
        role="Operations Coordinator",
        department="operations",
        personality="Process-focused",
        x=760,
        y=220,
        capabilities=[
            "project_management",
            "task_planning",
            "communication",
            "scheduling",
        ],
    )
