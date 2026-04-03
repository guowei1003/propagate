from __future__ import annotations

from pydantic import BaseModel, Field


class TaskCreatePayload(BaseModel):
    title: str = ""
    prompt: str
    env_profile_id: str
    model_overrides: dict[str, str] = Field(default_factory=dict)


class ClarificationAnswerPayload(BaseModel):
    answers: dict[str, str]
