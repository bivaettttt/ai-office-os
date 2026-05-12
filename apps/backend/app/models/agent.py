from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field

import uuid
import time

from app.schemas.protocol import AgentStatus


class Agent(BaseModel):

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )

    name: str

    role: str

    department: str

    personality: str

    position_x: int = 0

    position_y: int = 0

    current_action: str = "idle"

    # NEW
    status: AgentStatus = AgentStatus.IDLE

    # NEW
    task_progress: int = 0

    current_task_id: Optional[str] = None

    memory: List[str] = Field(default_factory=list)

    last_update: float = Field(
        default_factory=time.time
    )
