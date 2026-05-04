import pytest

from app.harness.compiler import compile_execution_plan
from app.harness.contracts import MissionBrief
from app.providers.base import ProviderContext
from app.providers.mock import MockProvider


@pytest.mark.asyncio
async def test_compile_execution_plan_returns_structured_steps():
    provider = MockProvider()
    mission = MissionBrief(
        goal="生成一个 Python 自动化脚本",
        success_criteria=["脚本产出", "验证通过"],
        constraints=["不要访问未授权域名"],
        deliverables=["脚本文件", "验证报告"],
        risk_level="medium",
        approval_mode="high_risk",
    )
    plan = await compile_execution_plan(
        mission,
        [
            {"id": "planner", "role": "planner", "capabilities": ["planning"]},
            {"id": "verifier", "role": "verifier", "capabilities": ["verification"]},
            {"id": "reporter", "role": "reporter", "capabilities": ["reporting"]},
        ],
        provider,
        ProviderContext(provider="mock", model="gpt-4.1-mini"),
    )
    assert plan.steps
    assert plan.steps[0].id == "analyze-task"
    assert any(agent.agent_id == "reporter" for agent in plan.selected_agents)
