from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.schemas.approvals import ApprovalDecisionRequest, ApprovalResponse
from app.services.approval_service import approval_service


router = APIRouter(tags=["approvals"])


@router.post("/tasks/{task_id}/runs/{run_id}/approve", response_model=ApprovalResponse)
async def approve_step(
    task_id: UUID,
    run_id: UUID,
    payload: ApprovalDecisionRequest,
    session: AsyncSession = Depends(get_db_session),
):
    _ = task_id, run_id
    try:
        approval = await approval_service.approve_step(session, payload.approval_id, payload.comment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await session.commit()
    return ApprovalResponse.model_validate(approval, from_attributes=True)


@router.post("/tasks/{task_id}/runs/{run_id}/reject", response_model=ApprovalResponse)
async def reject_step(
    task_id: UUID,
    run_id: UUID,
    payload: ApprovalDecisionRequest,
    session: AsyncSession = Depends(get_db_session),
):
    _ = task_id, run_id
    try:
        approval = await approval_service.reject_step(session, payload.approval_id, payload.comment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await session.commit()
    return ApprovalResponse.model_validate(approval, from_attributes=True)
