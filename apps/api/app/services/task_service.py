from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.harness.memory import create_memory
from app.models.run import TaskRun
from app.models.task import Task
from app.schemas.tasks import TaskCreateRequest


class TaskService:
    async def create_task(self, session: AsyncSession, payload: TaskCreateRequest) -> Task:
        task = Task(
            title=payload.title,
            goal=payload.goal,
            context=payload.context,
            constraints=payload.constraints,
            deliverables=payload.deliverables,
            approval_mode=payload.approval_mode,
        )
        session.add(task)
        await session.flush()

        task_run = TaskRun(
            task_id=task.id,
            profile_id=payload.profile_id,
            thread_id=f"run-{uuid4()}",
            status="queued",
            memory=create_memory(),
        )
        session.add(task_run)
        await session.flush()

        task.latest_run_id = task_run.id
        await session.commit()
        await session.refresh(task)
        return task

    async def list_tasks(self, session: AsyncSession) -> list[Task]:
        result = await session.execute(
            select(Task)
            .options(selectinload(Task.runs))
            .order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_task(self, session: AsyncSession, task_id: UUID) -> Task | None:
        result = await session.execute(
            select(Task)
            .options(selectinload(Task.runs))
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()


task_service = TaskService()
