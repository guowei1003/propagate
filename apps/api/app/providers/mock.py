from __future__ import annotations

import textwrap
from typing import Any

from pydantic import BaseModel

from app.harness.contracts import (
    AgentSpec,
    CapabilityRequirement,
    CriterionVerdict,
    ExecutionPlan,
    MissionBrief,
    PlanStep,
    SelectedAgent,
    StepAssessment,
    VerificationResult,
)
from app.providers.base import BaseProvider, HarnessProvider, ProviderContext, ProviderResponse


class MockProvider(BaseProvider, HarnessProvider):
    async def complete_text(self, prompt: str, context: ProviderContext) -> ProviderResponse:
        return ProviderResponse(
            content=textwrap.shorten(prompt, width=200, placeholder="..."),
            metadata={"provider": "mock", "model": context.model},
        )

    async def complete_structured(
        self,
        prompt: str,
        context: ProviderContext,
        schema: type[BaseModel],
    ) -> BaseModel:
        payload = {"prompt": prompt, "provider": context.provider, "model": context.model}
        return schema.model_validate(payload)

    async def build_mission(self, task_input: dict[str, Any], context: ProviderContext) -> MissionBrief:
        constraints = list(task_input.get("constraints") or [])
        deliverables = list(task_input.get("deliverables") or [])
        risk_level = "high" if task_input.get("approval_mode") == "high_risk" else "medium"
        return MissionBrief(
            goal=task_input["goal"],
            success_criteria=[
                "执行计划中的每个步骤都有结果记录",
                "所有成功标准都被 verifier 明确核验",
                "输出脚本、报告与日志三类交付物",
            ],
            constraints=constraints or ["不得访问未授权域名", "所有执行必须可追踪"],
            deliverables=deliverables or ["脚本文件", "验证报告", "执行日志"],
            risk_level=risk_level,
            approval_mode=task_input.get("approval_mode", "high_risk"),
        )

    async def build_plan(
        self,
        mission: MissionBrief,
        selected_agents: list[dict[str, Any]],
        context: ProviderContext,
    ) -> ExecutionPlan:
        agent_map = {agent["id"]: agent for agent in selected_agents}
        steps = [
            PlanStep(
                id="analyze-task",
                title="补充任务分析",
                kind="analysis",
                assigned_agent_id="researcher" if "researcher" in agent_map else "planner",
                instructions="整理任务事实、约束与潜在风险，为执行做准备。",
                expected_artifacts=["analysis.md"],
                approval_required=False,
                max_retries=1,
                timeout_sec=60,
            ),
        ]

        if "api_operator" in agent_map:
            steps.append(
                PlanStep(
                    id="call-api",
                    title="执行 API 自动化",
                    kind="http",
                    assigned_agent_id="api_operator",
                    depends_on=["analyze-task"],
                    instructions="通过 allowlist HTTP 工具访问目标 API，并记录响应。",
                    expected_artifacts=["api-response.json"],
                    approval_required=mission.approval_mode == "step",
                    max_retries=2,
                    timeout_sec=120,
                )
            )
        elif "python_executor" in agent_map:
            steps.append(
                PlanStep(
                    id="run-python",
                    title="生成并执行 Python 脚本",
                    kind="sandbox_python",
                    assigned_agent_id="python_executor",
                    depends_on=["analyze-task"],
                    instructions="编写 Python 脚本并在沙箱执行，保存脚本与输出。",
                    expected_artifacts=["script.py", "stdout.txt"],
                    approval_required=False,
                    max_retries=2,
                    timeout_sec=120,
                )
            )
        else:
            steps.append(
                PlanStep(
                    id="run-shell",
                    title="生成并执行 shell 命令",
                    kind="sandbox_shell",
                    assigned_agent_id="shell_executor",
                    depends_on=["analyze-task"],
                    instructions="在沙箱中执行 shell 命令并保存输出。",
                    expected_artifacts=["commands.sh", "stdout.txt"],
                    approval_required=False,
                    max_retries=2,
                    timeout_sec=120,
                )
            )

        steps.extend(
            [
                PlanStep(
                    id="verify-output",
                    title="验证成功标准",
                    kind="verification",
                    assigned_agent_id="verifier",
                    depends_on=[steps[-1].id],
                    instructions="按照成功标准核验任务输出和工件。",
                    expected_artifacts=["verification.json"],
                    approval_required=False,
                    max_retries=1,
                    timeout_sec=60,
                ),
                PlanStep(
                    id="final-report",
                    title="汇总最终报告",
                    kind="report",
                    assigned_agent_id="reporter",
                    depends_on=["verify-output"],
                    instructions="输出最终总结、交付物清单和后续建议。",
                    expected_artifacts=["final-report.md"],
                    approval_required=False,
                    max_retries=1,
                    timeout_sec=60,
                ),
            ]
        )

        required_capabilities = [
            CapabilityRequirement(tags=["planning", "verification"], rationale="需要计划与验收"),
        ]
        if any("api" in criterion.lower() for criterion in mission.goal.split()):
            required_capabilities.append(
                CapabilityRequirement(tags=["http", "api-integration"], rationale="任务包含 API 自动化")
            )
        return ExecutionPlan(
            mission=mission,
            required_capabilities=required_capabilities,
            selected_agents=[
                SelectedAgent(
                    agent_id=agent["id"],
                    role=agent["role"],
                    capabilities=agent["capabilities"],
                    reason=f"匹配能力 {', '.join(agent['capabilities'])}",
                )
                for agent in selected_agents
            ],
            steps=steps,
            termination={"max_steps": len(steps) + 2, "max_replans": 3, "max_tokens": 6000},
        )

    async def assess_step(
        self,
        mission: MissionBrief,
        step: dict[str, Any],
        result: dict[str, Any],
        context: ProviderContext,
    ) -> StepAssessment:
        status = "advance"
        reason = "步骤结果满足预期"
        if result.get("status") == "failed":
            status = "retry" if result.get("attempts", 0) < step.get("max_retries", 0) else "replan"
            reason = "步骤执行失败，需要重试或重规划"
        return StepAssessment(
            step_id=step["step_id"],
            status=status,
            reason=reason,
            request_human_input=step.get("approval_required", False) and mission.approval_mode != "auto",
            budget_snapshot={"remaining_replans": 3, "remaining_step_retries": max(step.get("max_retries", 0) - result.get("attempts", 0), 0)},
        )

    async def verify(
        self,
        mission: MissionBrief,
        step: dict[str, Any] | None,
        result: dict[str, Any],
        context: ProviderContext,
    ) -> VerificationResult:
        criteria = [
            CriterionVerdict(
                criterion=criterion,
                status="passed" if result.get("status") != "failed" else "failed",
                evidence=result.get("artifacts", []),
                detail=result.get("summary", "mock verification"),
            )
            for criterion in mission.success_criteria
        ]
        passed = all(item.status == "passed" for item in criteria)
        return VerificationResult(
            step_id=step["step_id"] if step else None,
            passed=passed,
            summary="所有成功标准均已通过 mock verifier 核验" if passed else "存在未通过的成功标准",
            criteria=criteria,
            artifacts=result.get("artifacts", []),
        )
