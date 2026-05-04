from app.harness.registry import list_agents
from app.harness.selector import select_agents_for_task


def test_registry_contains_builtin_agents():
    agent_ids = {agent.id for agent in list_agents()}
    assert {"planner", "supervisor", "verifier", "reporter"} <= agent_ids


def test_selector_adds_mandatory_agents_for_api_task():
    result = select_agents_for_task(
        "调用 API 并生成自动化脚本",
        ["不要访问未授权域名"],
        ["脚本文件", "验证报告"],
    )
    agent_ids = {agent.id for agent in result.agents}
    assert {"supervisor", "verifier", "reporter", "researcher"} <= agent_ids
