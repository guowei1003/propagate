import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.schemas import TaskCreate, TaskResponse, TaskListResponse
from app.services.task_service import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskListResponse])
async def list_tasks(
    status: str | None = Query(None, description="Filter by task status (PENDING, RUNNING, COMPLETED, FAILED)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await task_service.list_tasks(db, status=status, limit=limit, offset=offset)


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.create_task(db, data)
    logs = await task_service.get_logs(db, task.id)
    result = await task_service.get_result(db, task.id)
    return TaskResponse(
        id=task.id,
        title=task.title,
        prompt=task.prompt,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        logs=[],
        result=None,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    logs = await task_service.get_logs(db, task_id)
    result = await task_service.get_result(db, task_id)
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    deleted = await task_service.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
