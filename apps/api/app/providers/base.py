from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

from app.harness.contracts import ExecutionPlan, MissionBrief, StepAssessment, VerificationResult


StructuredResponse = TypeVar("StructuredResponse", bound=BaseModel)


class ProviderContext(BaseModel):
    provider: str
    model: str
    temperature: float = 0.1
    max_tokens: int = 4000


class ProviderResponse(BaseModel):
    content: str
    metadata: dict[str, Any] = {}


class BaseProvider(ABC):
    @abstractmethod
    async def complete_text(self, prompt: str, context: ProviderContext) -> ProviderResponse:
        raise NotImplementedError

    @abstractmethod
    async def complete_structured(
        self,
        prompt: str,
        context: ProviderContext,
        schema: type[StructuredResponse],
    ) -> StructuredResponse:
        raise NotImplementedError

    async def stream_events(self, prompt: str, context: ProviderContext) -> list[dict[str, Any]]:
        response = await self.complete_text(prompt, context)
        return [{"type": "text", "content": response.content}]


class HarnessProvider(ABC):
    @abstractmethod
    async def build_mission(self, task_input: dict[str, Any], context: ProviderContext) -> MissionBrief:
        raise NotImplementedError

    @abstractmethod
    async def build_plan(
        self,
        mission: MissionBrief,
        selected_agents: list[dict[str, Any]],
        context: ProviderContext,
    ) -> ExecutionPlan:
        raise NotImplementedError

    @abstractmethod
    async def assess_step(
        self,
        mission: MissionBrief,
        step: dict[str, Any],
        result: dict[str, Any],
        context: ProviderContext,
    ) -> StepAssessment:
        raise NotImplementedError

    @abstractmethod
    async def verify(
        self,
        mission: MissionBrief,
        step: dict[str, Any] | None,
        result: dict[str, Any],
        context: ProviderContext,
    ) -> VerificationResult:
        raise NotImplementedError
