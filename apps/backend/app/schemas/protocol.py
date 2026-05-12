from __future__ import annotations

import time
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


ClientMessageType = Literal[
    "client.hello",
    "world.subscribe",
    "world.get",
    "task.create",
]

ServerMessageType = Literal[
    "server.hello",
    "world.snapshot",
    "world.update",
    "agent.update",
    "task.update",
    "event.broadcast",
    "error",
]


class WebSocketMessage(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    ts: float = Field(default_factory=time.time)
