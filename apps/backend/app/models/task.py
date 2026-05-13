from __future__ import annotations

from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, Field

import uuid
import time

from app.schemas.protocol import TaskStatus


class TaskStepStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskRuntimePhase(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskStep(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )

    title: str

    description: str

    status: TaskStepStatus = TaskStepStatus.PENDING

    progress: int = 0

    started_at: Optional[float] = None

    completed_at: Optional[float] = None

    assigned_agent_id: Optional[str] = None


class Task(BaseModel):

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )

    title: str

    description: str

    department: str

    priority: str = "normal"

    status: TaskStatus = TaskStatus.CREATED

    runtime_phase: TaskRuntimePhase = (
        TaskRuntimePhase.CREATED
    )

    progress: int = 0

    plan: list[str] = Field(default_factory=list)

    steps: list[TaskStep] = Field(default_factory=list)

    active_step_index: int = 0

    assigned_to: Optional[str] = None

    assigned_by_manager_id: Optional[str] = None

    required_capabilities: list[str] = Field(
        default_factory=list
    )

    created_at: float = Field(
        default_factory=time.time
    )

    updated_at: float = Field(
        default_factory=time.time
    )

    assigned_at: Optional[float] = None

    started_at: Optional[float] = None

    completed_at: Optional[float] = None

    reviewed_at: Optional[float] = None

    result: Optional[str] = None

    result_summary: Optional[str] = None

    summary_note: Optional[str] = None

    review_draft: Optional[str] = None

    proposed_plan: list[str] = Field(default_factory=list)

    plan_notes: list[str] = Field(default_factory=list)

    failure_reason: Optional[str] = None
