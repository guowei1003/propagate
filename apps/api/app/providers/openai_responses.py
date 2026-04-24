from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings
from app.harness.contracts import ExecutionPlan, MissionBrief, StepAssessment, VerificationResult
from app.providers.base import BaseProvider, HarnessProvider, ProviderContext, ProviderResponse


class OpenAIResponsesProvider(BaseProvider, HarnessProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key or None,
            base_url=settings.openai_base_url,
        )

    async def complete_text(self, prompt: str, context: ProviderContext) -> ProviderResponse:
        response = await self._client.responses.create(
            model=context.model,
            input=prompt,
            temperature=context.temperature,
            max_output_tokens=context.max_tokens,
        )
        return ProviderResponse(
            content=response.output_text,
            metadata={"response_id": response.id},
        )

    async def complete_structured(self, prompt: str, context: ProviderContext, schema: type):
        response = await self._client.responses.parse(
            model=context.model,
            input=prompt,
            temperature=context.temperature,
            text_format=schema,
            max_output_tokens=context.max_tokens,
        )
        return response.output_parsed

    async def build_mission(self, task_input: dict[str, Any], context: ProviderContext) -> MissionBrief:
        prompt = (
            "将以下任务整理成 MissionBrief，必须保留目标、约束、交付物、风险等级和审批模式。"
            f"\n任务: {task_input}"
        )
        return await self.complete_structured(prompt, context, MissionBrief)

    async def build_plan(
        self,
        mission: MissionBrief,
        selected_agents: list[dict[str, Any]],
        context: ProviderContext,
    ) -> ExecutionPlan:
        prompt = (
            "基于 mission 与已选择的 agents 生成 ExecutionPlan，必须只使用给定 agent_id。"
            f"\nMission: {mission.model_dump_json()}"
            f"\nAgents: {selected_agents}"
        )
        return await self.complete_structured(prompt, context, ExecutionPlan)

    async def assess_step(
        self,
        mission: MissionBrief,
        step: dict[str, Any],
        result: dict[str, Any],
        context: ProviderContext,
    ) -> StepAssessment:
        prompt = (
            "基于任务 mission、步骤定义与执行结果，输出 StepAssessment。"
            f"\nMission: {mission.model_dump_json()}"
            f"\nStep: {step}"
            f"\nResult: {result}"
        )
        return await self.complete_structured(prompt, context, StepAssessment)

    async def verify(
        self,
        mission: MissionBrief,
        step: dict[str, Any] | None,
        result: dict[str, Any],
        context: ProviderContext,
    ) -> VerificationResult:
        prompt = (
            "根据 success criteria 验证结果，输出 VerificationResult。"
            f"\nMission: {mission.model_dump_json()}"
            f"\nStep: {step}"
            f"\nResult: {result}"
        )
        return await self.complete_structured(prompt, context, VerificationResult)
