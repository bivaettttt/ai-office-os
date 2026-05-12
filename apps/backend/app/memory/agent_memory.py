from __future__ import annotations


agent_memory = {
    "planner": {
        "status": "idle",
        "task": "",
        "phase": "idle",
    },

    "manager": {
        "status": "idle",
        "task": "",
        "phase": "idle",
    },

    "research": {
        "status": "idle",
        "task": "",
        "phase": "idle",
    },

    "coder": {
        "status": "idle",
        "task": "",
        "phase": "idle",
    },

    "debug": {
        "status": "idle",
        "task": "",
        "phase": "idle",
    },

    "terminal": {
        "status": "idle",
        "task": "",
        "phase": "idle",
    },

    "logs": [],

    "active_agent": "none",

    "last_response": "",

    "last_saved_project": {},

    "last_plan": {},

    "project_tree": [],
}