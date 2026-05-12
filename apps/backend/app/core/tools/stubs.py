from __future__ import annotations

from typing import Any, Callable


def generate_report_stub(
    arguments: dict[str, Any],
) -> dict[str, Any]:
    topic = arguments.get("topic") or arguments.get("title") or "Untitled"
    return {
        "kind": "report",
        "title": str(topic),
        "summary": (
            "Safe stub report generated without external tools."
        ),
        "sections": [
            "Context",
            "Findings",
            "Next steps",
        ],
    }


def summarize_text_stub(
    arguments: dict[str, Any],
) -> dict[str, Any]:
    text = str(arguments.get("text", ""))
    return {
        "kind": "summary",
        "input_length": len(text),
        "summary": (
            text[:120]
            if text
            else "No text was provided to summarize."
        ),
    }


def inspect_project_stub(
    arguments: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "project_inspection",
        "project": arguments.get("project", "ai-office-os"),
        "metadata": {
            "source": "safe_stub",
            "files_read": 0,
            "note": (
                "No real filesystem inspection was performed."
            ),
        },
    }


def run_tests_stub(
    arguments: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "test_run",
        "suite": arguments.get("suite", "default"),
        "status": "simulated_pass",
        "tests_run": 0,
        "note": "No terminal command was executed.",
    }


def web_research_stub(
    arguments: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "web_research",
        "query": arguments.get("query", ""),
        "findings": [],
        "note": "No network request was performed.",
    }


STUB_TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "generate_report_stub": generate_report_stub,
    "summarize_text_stub": summarize_text_stub,
    "inspect_project_stub": inspect_project_stub,
    "run_tests_stub": run_tests_stub,
    "web_research_stub": web_research_stub,
}
