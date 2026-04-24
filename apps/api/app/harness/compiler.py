from __future__ import annotations

from app.harness.contracts import ExecutionPlan, MissionBrief
from app.providers.base import HarnessProvider, ProviderContext


async def compile_execution_plan(
    mission: MissionBrief,
    selected_agents: list[dict],
    provider: HarnessProvider,
    context: ProviderContext,
) -> ExecutionPlan:
    return await provider.build_plan(mission, selected_agents, context)
