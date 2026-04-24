from __future__ import annotations

from dataclasses import dataclass

from app.harness.contracts import AgentSpec, CapabilityRequirement
from app.harness.registry import list_agents


MANDATORY_AGENT_IDS = ["supervisor", "verifier", "reporter"]
FALLBACK_AGENT_IDS = ["researcher", "planner", "supervisor", "verifier", "reporter"]


@dataclass
class SelectionResult:
    agents: list[AgentSpec]
    warnings: list[str]


def infer_capability_requirements(goal: str, constraints: list[str], deliverables: list[str]) -> list[CapabilityRequirement]:
    text = " ".join([goal, *constraints, *deliverables]).lower()
    requirements = [
        CapabilityRequirement(tags=["planning", "verification"], rationale="所有任务都需要计划与验证"),
    ]
    if any(token in text for token in ["api", "http", "webhook", "endpoint"]):
        requirements.append(CapabilityRequirement(tags=["http", "api-integration"], rationale="任务涉及 API 调用"))
    if any(token in text for token in ["python", "script", "sdk"]):
        requirements.append(CapabilityRequirement(tags=["python", "sandbox-execution"], rationale="任务涉及 Python 脚本"))
    if any(token in text for token in ["shell", "bash", "command", "cli"]):
        requirements.append(CapabilityRequirement(tags=["shell", "sandbox-execution"], rationale="任务涉及 shell 命令"))
    if any(token in text for token in ["research", "investigate", "analyze", "调研", "分析"]):
        requirements.append(CapabilityRequirement(tags=["research", "fact-gathering"], rationale="任务需要事实整理"))
    return requirements


def _covers(agent: AgentSpec, requirement: CapabilityRequirement) -> bool:
    agent_caps = set(agent.capabilities)
    return set(requirement.tags).issubset(agent_caps) or any(tag in agent_caps for tag in requirement.tags)


def select_agents_for_task(
    goal: str,
    constraints: list[str],
    deliverables: list[str],
    planned_step_kinds: list[str] | None = None,
) -> SelectionResult:
    requirements = infer_capability_requirements(goal, constraints, deliverables)
    registry = list_agents()
    chosen: dict[str, AgentSpec] = {}
    warnings: list[str] = []

    for requirement in requirements:
        candidates = [agent for agent in registry if _covers(agent, requirement)]
        if not candidates:
            warnings.append(f"缺少可覆盖能力 {requirement.tags} 的 agent，已使用 fallback 组合")
            fallback = [agent for agent in registry if agent.id in FALLBACK_AGENT_IDS]
            return SelectionResult(agents=fallback, warnings=warnings)
        candidates.sort(key=lambda agent: (len(agent.capabilities), agent.id))
        chosen[candidates[0].id] = candidates[0]

    for agent_id in MANDATORY_AGENT_IDS:
        chosen[agent_id] = next(agent for agent in registry if agent.id == agent_id)

    if planned_step_kinds:
        if any(kind == "sandbox_python" for kind in planned_step_kinds):
            chosen["python_executor"] = next(agent for agent in registry if agent.id == "python_executor")
        if any(kind == "sandbox_shell" for kind in planned_step_kinds):
            chosen["shell_executor"] = next(agent for agent in registry if agent.id == "shell_executor")

    if "http" in " ".join(goal.lower().split()):
        chosen.setdefault("api_operator", next(agent for agent in registry if agent.id == "api_operator"))

    if "researcher" not in chosen:
        chosen["researcher"] = next(agent for agent in registry if agent.id == "researcher")

    return SelectionResult(agents=list(chosen.values()), warnings=warnings)
