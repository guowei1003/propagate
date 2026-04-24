from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RunActionRequest(BaseModel):
    reason: str | None = None


class RunSummaryResponse(BaseModel):
    id: UUID
    task_id: UUID
    status: str
    thread_id: str
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RunStepResponse(BaseModel):
    id: UUID
    step_id: str
    position: int
    title: str
    kind: str
    assigned_agent_id: str
    status: str
    attempts: int
    approval_required: bool
    expected_artifacts: list[str]
    dependencies: list[str]
    result: dict | None = None


class RunEventResponse(BaseModel):
    id: int
    run_id: UUID
    sequence: int
    category: str
    name: str
    message: str
    payload: dict
    created_at: datetime


class RunDetailResponse(RunSummaryResponse):
    mission: dict | None = None
    selected_agents: list[dict] = Field(default_factory=list)
    execution_plan: dict | None = None
    verification_summary: dict | None = None
    warnings: list[str] = Field(default_factory=list)
    interrupt_payload: dict | None = None
    steps: list[RunStepResponse] = Field(default_factory=list)
    approvals: list[dict] = Field(default_factory=list)
    artifacts: list[dict] = Field(default_factory=list)
