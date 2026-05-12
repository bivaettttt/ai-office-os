from __future__ import annotations

import time
import uuid

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class CommandStatus(StrEnum):
    RECEIVED = "received"
    PARSED = "parsed"
    ROUTED = "routed"
    TASK_CREATED = "task_created"
    FAILED = "failed"


class UserCommand(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    raw_text: str
    normalized_text: str = ""
    status: CommandStatus = CommandStatus.RECEIVED
    inferred_department: Optional[str] = None
    inferred_priority: str = "normal"
    inferred_capabilities: list[str] = Field(
        default_factory=list
    )
    created_task_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    processed_at: Optional[float] = None
    error_message: Optional[str] = None
