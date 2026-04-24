from __future__ import annotations

from app.harness.contracts import MissionBrief, PlanStep


SIDE_EFFECT_STEP_KINDS = {"http", "tool_call"}


def step_requires_approval(step: PlanStep, mission: MissionBrief, profile: dict | None = None) -> bool:
    if step.approval_required:
        return True
    if mission.approval_mode == "step":
        return True
    if mission.risk_level == "high" and profile and profile.get("requires_human_approval_for_high_risk", True):
        return True
    return step.kind in SIDE_EFFECT_STEP_KINDS and mission.approval_mode == "high_risk"


def should_interrupt_for_budget(step_index: int, step_count: int, replans: int, max_replans: int) -> bool:
    return step_index >= step_count or replans > max_replans
