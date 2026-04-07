import uuid
from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Task, TaskLog, TaskResult, Profile
from app.schemas import TaskCreate, ProfileCreate, ProfileUpdate


class TaskService:
    async def list_tasks(
        self,
        session: AsyncSession,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Task]:
        query = select(Task).order_by(Task.created_at.desc())
        if status:
            query = query.where(Task.status == status)
        query = query.limit(limit).offset(offset)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def count_tasks(self, session: AsyncSession, status: str | None = None) -> int:
        query = select(func.count(Task.id))
        if status:
            query = query.where(Task.status == status)
        result = await session.execute(query)
        return result.scalar() or 0

    async def get_task(self, session: AsyncSession, task_id: uuid.UUID) -> Task | None:
        result = await session.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def create_task(self, session: AsyncSession, data: TaskCreate) -> Task:
        task = Task(
            title=data.title,
            prompt=data.prompt,
            status="PENDING",
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

    async def delete_task(self, session: AsyncSession, task_id: uuid.UUID) -> bool:
        task = await self.get_task(session, task_id)
        if not task:
            return False
        await session.delete(task)
        await session.commit()
        return True

    async def append_log(
        self,
        session: AsyncSession,
        task_id: uuid.UUID,
        event_type: str,
        message: str | None = None,
        payload: dict | None = None,
    ) -> TaskLog:
        log = TaskLog(
            task_id=task_id,
            event_type=event_type,
            message=message,
            payload=payload,
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log

    async def get_logs(self, session: AsyncSession, task_id: uuid.UUID) -> list[TaskLog]:
        result = await session.execute(
            select(TaskLog)
            .where(TaskLog.task_id == task_id)
            .order_by(TaskLog.created_at)
        )
        return list(result.scalars().all())

    async def get_result(self, session: AsyncSession, task_id: uuid.UUID) -> TaskResult | None:
        result = await session.execute(
            select(TaskResult).where(TaskResult.task_id == task_id)
        )
        return result.scalar_one_or_none()


class ProfileService:
    async def list_profiles(self, session: AsyncSession) -> list[Profile]:
        result = await session.execute(select(Profile).order_by(Profile.created_at.desc()))
        return list(result.scalars().all())

    async def get_profile(self, session: AsyncSession, profile_id: uuid.UUID) -> Profile | None:
        result = await session.execute(select(Profile).where(Profile.id == profile_id))
        return result.scalar_one_or_none()

    async def create_profile(self, session: AsyncSession, data: ProfileCreate) -> Profile:
        profile = Profile(**data.model_dump())
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        return profile

    async def update_profile(
        self, session: AsyncSession, profile_id: uuid.UUID, data: ProfileUpdate
    ) -> Profile | None:
        profile = await self.get_profile(session, profile_id)
        if not profile:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        await session.commit()
        await session.refresh(profile)
        return profile

    async def delete_profile(self, session: AsyncSession, profile_id: uuid.UUID) -> bool:
        profile = await self.get_profile(session, profile_id)
        if not profile:
            return False
        await session.delete(profile)
        await session.commit()
        return True


task_service = TaskService()
profile_service = ProfileService()
