from __future__ import annotations

from app.harness.contracts import MissionBrief, StepAssessment
from app.providers.base import HarnessProvider, ProviderContext


async def evaluate_step(
    mission: MissionBrief,
    step: dict,
    result: dict,
    provider: HarnessProvider,
    context: ProviderContext,
) -> StepAssessment:
    return await provider.assess_step(mission, step, result, context)
