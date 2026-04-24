from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    title: str
    goal: str
    context: str | None = None
    constraints: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    approval_mode: str = "high_risk"
    profile_id: UUID | None = None


class TaskSummaryResponse(BaseModel):
    id: UUID
    title: str
    goal: str
    approval_mode: str
    latest_run_id: UUID | None
    created_at: datetime
    updated_at: datetime


class TaskDetailResponse(TaskSummaryResponse):
    latest_run: dict | None = None
