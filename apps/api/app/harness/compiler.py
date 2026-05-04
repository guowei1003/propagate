from __future__ import annotations

from app.harness.contracts import ExecutionPlan, MissionBrief, SelectedAgent
from app.harness.registry import get_agent
from app.providers.base import HarnessProvider, ProviderContext


async def compile_execution_plan(
    mission: MissionBrief,
    selected_agents: list[dict],
    provider: HarnessProvider,
    context: ProviderContext,
) -> ExecutionPlan:
    plan = await provider.build_plan(mission, selected_agents, context)
    selected_by_id = {agent["id"]: agent for agent in selected_agents}
    for step in plan.steps:
        if step.assigned_agent_id not in selected_by_id:
            agent = get_agent(step.assigned_agent_id)
            selected_by_id[agent.id] = agent.model_dump()
    plan.selected_agents = [
        SelectedAgent(
            agent_id=agent.get("agent_id", agent["id"]),
            role=agent["role"],
            capabilities=agent["capabilities"],
            reason=agent.get("reason", "由计划编译阶段自动补齐所需执行器"),
        )
        for agent in selected_by_id.values()
    ]
    return plan
