from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field

import uuid


class Department(BaseModel):

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )

    name: str

    description: str

    manager_agent_id: Optional[str] = None

    agents: List[str] = Field(
        default_factory=list
    )