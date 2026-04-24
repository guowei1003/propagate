from __future__ import annotations

from pydantic import BaseModel


class AgentSpecResponse(BaseModel):
    id: str
    name: str
    role: str
    capabilities: list[str]
    allowed_tools: list[str]
    allowed_step_kinds: list[str]
    requires_approval_for: list[str]
    max_turns: int
    model_tier: str
