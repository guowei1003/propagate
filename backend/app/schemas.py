import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    llm_model: str = Field(default="demo-heuristic", max_length=64)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    timeout_sec: int = Field(default=300, ge=10, le=3600)


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    llm_model: str | None = Field(default=None, max_length=64)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    timeout_sec: int | None = Field(default=None, ge=10, le=3600)


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime


class TaskLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_type: str
    message: str | None
    payload: dict[str, Any] | None
    created_at: datetime


class TaskResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    output: str | None
    artifacts: dict[str, Any] | None
    created_at: datetime


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    prompt: str = Field(..., min_length=1)


class TaskCreate(TaskBase):
    profile_id: uuid.UUID | None = None


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    logs: list[TaskLogResponse] = []
    result: TaskResultResponse | None = None


class TaskListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    status: str
    created_at: datetime
    updated_at: datetime


class TaskStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    updated_at: datetime
