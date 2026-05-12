from app.core.factory import (
    create_department,
    create_agent,
)


def bootstrap_world():

    # =====================================================
    # DEVELOPMENT
    # =====================================================

    create_department(
        name="development",
        description="Development Department",
    )

    create_agent(
        name="Alex",
        role="Frontend Engineer",
        department="development",
        personality="React expert",
        x=140,
        y=180,
    )

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

    create_department(
        name="assistant",
        description="Assistant Department",
    )

    create_agent(
        name="Luna",
        role="Executive Assistant",
        department="assistant",
        personality="Helpful and organized",
        x=860,
        y=180,
    )

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

    create_department(
        name="analytics",
        description="Analytics Department",
    )

    create_agent(
        name="Olivia",
        role="Market Analyst",
        department="analytics",
        personality="Data-focused",
        x=140,
        y=600,
    )

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

    create_department(
        name="content",
        description="Content Department",
    )

    create_agent(
        name="Emma",
        role="Content Writer",
        department="content",
        personality="Creative writer",
        x=860,
        y=600,
    )

    create_agent(
        name="Sophia",
        role="SEO Specialist",
        department="content",
        personality="SEO optimizer",
        x=1040,
        y=600,
    )