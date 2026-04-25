from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MissionBrief(BaseModel):
    goal: str
    success_criteria: list[str]
    constraints: list[str]
    deliverables: list[str]
    risk_level: Literal["low", "medium", "high"]
    approval_mode: Literal["auto", "step", "high_risk"]


class CapabilityRequirement(BaseModel):
    tags: list[str]
    rationale: str


class SelectedAgent(BaseModel):
    agent_id: str
    role: str
    capabilities: list[str]
    reason: str


class PlanStep(BaseModel):
    id: str
    title: str
    kind: Literal[
        "analysis",
        "tool_call",
        "sandbox_python",
        "sandbox_shell",
        "http",
        "verification",
        "report",
    ]
    assigned_agent_id: str
    depends_on: list[str] = Field(default_factory=list)
    instructions: str
    expected_artifacts: list[str] = Field(default_factory=list)
    approval_required: bool = False
    max_retries: int = 2
    timeout_sec: int = 180


class ExecutionPlan(BaseModel):
    version: int = 1
    mission: MissionBrief
    required_capabilities: list[CapabilityRequirement]
    selected_agents: list[SelectedAgent]
    steps: list[PlanStep]
    termination: dict[str, int | str]


class CriterionVerdict(BaseModel):
    criterion: str
    status: Literal["passed", "failed", "not_evaluated"]
    evidence: list[str] = Field(default_factory=list)
    detail: str = ""


class VerificationResult(BaseModel):
    step_id: str | None = None
    passed: bool
    summary: str
    criteria: list[CriterionVerdict] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)


class StepAssessment(BaseModel):
    step_id: str
    status: Literal["advance", "retry", "replan", "halt"]
    reason: str
    request_human_input: bool = False
    budget_snapshot: dict[str, int] = Field(default_factory=dict)


class AgentSpec(BaseModel):
    id: str
    name: str
    role: str
    intro: str = ""
    capabilities: list[str]
    allowed_tools: list[str] = Field(default_factory=list)
    allowed_step_kinds: list[str] = Field(default_factory=list)
    requires_approval_for: list[str] = Field(default_factory=list)
    max_turns: int = 3
    model_tier: str = "reasoning"


class TaskCreateInput(BaseModel):
    title: str
    goal: str
    context: str | None = None
    constraints: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    approval_mode: Literal["auto", "step", "high_risk"] = "high_risk"
    profile_id: str | None = None
