from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import Approval


class ApprovalService:
    async def request_approval(self, session: AsyncSession, run_id, step_id: str, reason: str) -> Approval:
        approval = Approval(run_id=run_id, step_id=step_id, reason=reason, status="pending")
        session.add(approval)
        await session.flush()
        return approval

    async def approve_step(self, session: AsyncSession, approval_id: UUID, comment: str | None = None) -> Approval:
        approval = await session.get(Approval, approval_id)
        if approval is None:
            raise ValueError("approval not found")
        approval.status = "approved"
        approval.decision = "approve"
        approval.comment = comment
        approval.resolved_at = datetime.now(timezone.utc)
        await session.flush()
        return approval

    async def reject_step(self, session: AsyncSession, approval_id: UUID, comment: str | None = None) -> Approval:
        approval = await session.get(Approval, approval_id)
        if approval is None:
            raise ValueError("approval not found")
        approval.status = "rejected"
        approval.decision = "reject"
        approval.comment = comment
        approval.resolved_at = datetime.now(timezone.utc)
        await session.flush()
        return approval

    async def list_for_run(self, session: AsyncSession, run_id) -> list[Approval]:
        result = await session.execute(select(Approval).where(Approval.run_id == run_id).order_by(Approval.requested_at.asc()))
        return list(result.scalars().all())


approval_service = ApprovalService()
