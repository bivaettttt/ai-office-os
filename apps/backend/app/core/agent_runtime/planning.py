from __future__ import annotations

from app.models.task import TaskStep


PLAN_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "development": [
        ("Understand request", "Clarify the requested engineering change."),
        ("Inspect project context", "Review the relevant project state."),
        ("Implement change", "Apply the requested implementation."),
        ("Validate result", "Check that the result behaves correctly."),
        ("Summarize output", "Prepare a concise completion summary."),
    ],
    "analytics": [
        ("Understand research goal", "Clarify the research question."),
        ("Collect sources", "Gather relevant source material."),
        ("Analyze findings", "Identify patterns and implications."),
        ("Build summary", "Condense findings into a clear summary."),
        ("Prepare report", "Format the final analytics report."),
    ],
    "assistant": [
        ("Understand personal request", "Clarify the user request."),
        ("Check context", "Review available context."),
        ("Execute action", "Perform the requested support action."),
        ("Confirm completion", "Confirm that the action is complete."),
    ],
    "content": [
        ("Understand content goal", "Clarify audience and intent."),
        ("Draft content", "Prepare the first content draft."),
        ("Review tone", "Check voice, clarity, and fit."),
        ("Finalize output", "Prepare final content output."),
    ],
    "operations": [
        ("Inspect system state", "Review the operational context."),
        ("Apply operational action", "Perform the operational step."),
        ("Validate system health", "Check the resulting state."),
        ("Report status", "Summarize current operational status."),
    ],
}

DEFAULT_TEMPLATE = [
    ("Understand request", "Clarify the requested work."),
    ("Execute work", "Perform the requested work."),
    ("Validate result", "Check the result."),
    ("Summarize output", "Prepare a completion summary."),
]


def generate_task_steps(
    department: str,
) -> list[TaskStep]:
    template = PLAN_TEMPLATES.get(
        department,
        DEFAULT_TEMPLATE,
    )

    return [
        TaskStep(
            title=title,
            description=description,
        )
        for title, description in template
    ]


def generate_task_plan(
    department: str,
) -> list[str]:
    return [
        step.title
        for step in generate_task_steps(department)
    ]
