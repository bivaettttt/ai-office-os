from __future__ import annotations

from app.core.tools.permissions import (
    Permission,
    RiskLevel,
    ToolCategory,
    ToolDefinition,
)


DEFAULT_TOOL_DEFINITIONS = [
    ToolDefinition(
        id="generate_report_stub",
        name="Generate Report Stub",
        description=(
            "Creates a safe placeholder report result without "
            "reading files or calling external services."
        ),
        category=ToolCategory.GENERATION,
        required_capabilities=["report_writing"],
        required_permissions=[Permission.CREATE_REPORT],
        risk_level=RiskLevel.LOW,
        enabled=True,
        requires_approval=False,
    ),
    ToolDefinition(
        id="summarize_text_stub",
        name="Summarize Text Stub",
        description=(
            "Summarizes provided text locally as a deterministic "
            "placeholder response."
        ),
        category=ToolCategory.ANALYSIS,
        required_capabilities=["report_writing"],
        required_permissions=[Permission.GENERATE_CONTENT],
        risk_level=RiskLevel.LOW,
        enabled=True,
        requires_approval=False,
    ),
    ToolDefinition(
        id="inspect_project_stub",
        name="Inspect Project Stub",
        description=(
            "Returns safe fake project metadata. It does not read "
            "real project files."
        ),
        category=ToolCategory.FILESYSTEM,
        required_capabilities=["task_planning"],
        required_permissions=[Permission.READ_PROJECT_FILES],
        risk_level=RiskLevel.LOW,
        enabled=True,
        requires_approval=False,
    ),
    ToolDefinition(
        id="run_tests_stub",
        name="Run Tests Stub",
        description=(
            "Returns a simulated test result. It does not run "
            "terminal commands."
        ),
        category=ToolCategory.TERMINAL,
        required_capabilities=["quality_review"],
        required_permissions=[Permission.RUN_TESTS],
        risk_level=RiskLevel.MEDIUM,
        enabled=True,
        requires_approval=True,
    ),
    ToolDefinition(
        id="web_research_stub",
        name="Web Research Stub",
        description=(
            "Returns simulated research notes. It does not access "
            "the network."
        ),
        category=ToolCategory.NETWORK,
        required_capabilities=["web_research"],
        required_permissions=[Permission.ACCESS_NETWORK],
        risk_level=RiskLevel.HIGH,
        enabled=True,
        requires_approval=True,
    ),
]


class ToolRegistry:
    def __init__(
        self,
        definitions: list[ToolDefinition] | None = None,
    ):
        self._tools = {
            tool.id: tool
            for tool in (
                definitions or DEFAULT_TOOL_DEFINITIONS
            )
        }

    def register(
        self,
        tool: ToolDefinition,
    ) -> None:
        self._tools[tool.id] = tool

    def get(
        self,
        tool_id: str,
    ) -> ToolDefinition | None:
        return self._tools.get(tool_id)

    def list_tools(self) -> list[ToolDefinition]:
        return sorted(
            self._tools.values(),
            key=lambda item: item.id,
        )


tool_registry = ToolRegistry()
