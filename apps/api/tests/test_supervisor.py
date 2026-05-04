import pytest

from app.harness.contracts import MissionBrief
from app.harness.supervisor import evaluate_step
from app.providers.base import ProviderContext
from app.providers.mock import MockProvider


@pytest.mark.asyncio
async def test_supervisor_requests_retry_for_failed_step():
    provider = MockProvider()
    assessment = await evaluate_step(
        MissionBrief(
            goal="测试任务",
            success_criteria=["完成"],
            constraints=[],
            deliverables=[],
            risk_level="low",
            approval_mode="auto",
        ),
        {"step_id": "s1", "max_retries": 2, "approval_required": False},
        {"status": "failed", "attempts": 1, "artifacts": []},
        provider,
        ProviderContext(provider="mock", model="mock"),
    )
    assert assessment.status == "retry"
