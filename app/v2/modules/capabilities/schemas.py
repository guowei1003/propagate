from __future__ import annotations

from pydantic import BaseModel, Field


class CapabilityGeneratePayload(BaseModel):
    name: str
    description: str
    instructions: str
    task_id: str | None = None
    run_id: str | None = None
    allowed_tools: list[str] = Field(default_factory=list)
    allowed_commands: list[str] = Field(default_factory=list)
    allowed_file_scope: list[str] = Field(default_factory=lambda: ["/workspace"])
    risk_tags: list[str] = Field(default_factory=list)
    default_model_selector: str = ""
    generation_model: str = ""
    generation_prompt: str = ""
    generation_raw_output: str = ""


class CapabilityDecisionPayload(BaseModel):
    approver: str
    comment: str = ""
