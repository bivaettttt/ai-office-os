from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

import uuid
import time

from app.schemas.protocol import TaskStatus


class Task(BaseModel):

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )

    title: str

    description: str

    department: str

    priority: str = "normal"

    status: TaskStatus = TaskStatus.CREATED

    progress: int = 0

    assigned_to: Optional[str] = None

    created_at: float = Field(
        default_factory=time.time
    )

    updated_at: float = Field(
        default_factory=time.time
    )

    assigned_at: Optional[float] = None

    completed_at: Optional[float] = None

    result: Optional[str] = None
