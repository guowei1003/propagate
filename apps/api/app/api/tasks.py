from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.schemas.runs import RunActionRequest, RunDetailResponse, RunSummaryResponse
from app.schemas.tasks import TaskCreateRequest, TaskDetailResponse, TaskSummaryResponse
from app.services.run_service import run_service
from app.services.task_service import task_service


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskSummaryResponse])
async def list_tasks(session: AsyncSession = Depends(get_db_session)):
    tasks = await task_service.list_tasks(session)
    return [
        TaskSummaryResponse(
            id=task.id,
            title=task.title,
            goal=task.goal,
            approval_mode=task.approval_mode,
            latest_run_id=task.latest_run_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        for task in tasks
    ]


@router.post("", response_model=TaskDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreateRequest, session: AsyncSession = Depends(get_db_session)):
    task = await task_service.create_task(session, payload)
    latest_run = task.runs[0]
    await run_service.start_run(session, task, latest_run)
    return TaskDetailResponse(
        id=task.id,
        title=task.title,
        goal=task.goal,
        approval_mode=task.approval_mode,
        latest_run_id=task.latest_run_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        latest_run={
            "id": str(latest_run.id),
            "status": latest_run.status,
            "thread_id": latest_run.thread_id,
        },
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: UUID, session: AsyncSession = Depends(get_db_session)):
    task = await task_service.get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    latest_run = task.runs[0] if task.runs else None
    return TaskDetailResponse(
        id=task.id,
        title=task.title,
        goal=task.goal,
        approval_mode=task.approval_mode,
        latest_run_id=task.latest_run_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        latest_run=(
            {
                "id": str(latest_run.id),
                "status": latest_run.status,
                "thread_id": latest_run.thread_id,
            }
            if latest_run
            else None
        ),
    )


@router.get("/{task_id}/runs/{run_id}", response_model=RunDetailResponse)
async def get_run(task_id: UUID, run_id: UUID, session: AsyncSession = Depends(get_db_session)):
    run = await run_service.get_run(session, task_id, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return RunDetailResponse(
        id=run.id,
        task_id=run.task_id,
        status=run.status,
        thread_id=run.thread_id,
        created_at=run.created_at,
        updated_at=run.updated_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        mission=run.mission,
        selected_agents=run.selected_agents,
        execution_plan=run.execution_plan,
        verification_summary=run.verification_summary,
        warnings=run.warnings,
        interrupt_payload=run.interrupt_payload,
        steps=[
            {
                "id": step.id,
                "step_id": step.step_id,
                "position": step.position,
                "title": step.title,
                "kind": step.kind,
                "assigned_agent_id": step.assigned_agent_id,
                "status": step.status,
                "attempts": step.attempts,
                "approval_required": step.approval_required,
                "expected_artifacts": step.expected_artifacts,
                "dependencies": step.dependencies,
                "result": step.result,
            }
            for step in run.steps
        ],
        approvals=[approval.__dict__ for approval in run.approvals],
        artifacts=[artifact.__dict__ for artifact in run.artifacts],
    )


@router.post("/{task_id}/runs/{run_id}/resume", response_model=RunSummaryResponse)
async def resume_run(task_id: UUID, run_id: UUID, session: AsyncSession = Depends(get_db_session)):
    run = await run_service.resume_run(session, task_id, run_id)
    return RunSummaryResponse(
        id=run.id,
        task_id=run.task_id,
        status=run.status,
        thread_id=run.thread_id,
        created_at=run.created_at,
        updated_at=run.updated_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


@router.post("/{task_id}/runs/{run_id}/cancel", response_model=RunSummaryResponse)
async def cancel_run(
    task_id: UUID,
    run_id: UUID,
    payload: RunActionRequest | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    _ = payload
    run = await run_service.cancel_run(session, task_id, run_id)
    return RunSummaryResponse(
        id=run.id,
        task_id=run.task_id,
        status=run.status,
        thread_id=run.thread_id,
        created_at=run.created_at,
        updated_at=run.updated_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


@router.post("/{task_id}/runs/{run_id}/replan", response_model=RunSummaryResponse)
async def replan_run(
    task_id: UUID,
    run_id: UUID,
    payload: RunActionRequest,
    session: AsyncSession = Depends(get_db_session),
):
    _ = payload
    run = await run_service.resume_run(session, task_id, run_id)
    return RunSummaryResponse(
        id=run.id,
        task_id=run.task_id,
        status=run.status,
        thread_id=run.thread_id,
        created_at=run.created_at,
        updated_at=run.updated_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )
