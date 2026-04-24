from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    name: str
    model_provider: str = "mock"
    model_name: str = "gpt-4.1-mini"
    temperature: float = 0.1
    max_tokens: int = 4000
    http_allowlist_domains: list[str] = Field(default_factory=list)
    http_allowlist_methods: list[str] = Field(default_factory=lambda: ["GET", "POST"])
    sandbox_cpu_limit: float = 1.0
    sandbox_memory_limit_mb: int = 512
    step_timeout_sec: int = 180
    requires_human_approval_for_high_risk: bool = True


class ProfileCreateRequest(ProfileBase):
    pass


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    model_provider: str | None = None
    model_name: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    http_allowlist_domains: list[str] | None = None
    http_allowlist_methods: list[str] | None = None
    sandbox_cpu_limit: float | None = None
    sandbox_memory_limit_mb: int | None = None
    step_timeout_sec: int | None = None
    requires_human_approval_for_high_risk: bool | None = None


class ProfileResponse(ProfileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
