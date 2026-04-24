from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import RunEvent


class StreamService:
    async def append_event(
        self,
        session: AsyncSession,
        run_id,
        *,
        category: str,
        name: str,
        message: str,
        payload: dict,
    ) -> RunEvent:
        result = await session.execute(select(func.max(RunEvent.sequence)).where(RunEvent.run_id == run_id))
        next_sequence = (result.scalar_one_or_none() or 0) + 1
        event = RunEvent(
            run_id=run_id,
            sequence=next_sequence,
            category=category,
            name=name,
            message=message,
            payload=payload,
        )
        session.add(event)
        await session.flush()
        return event

    async def list_events(self, session: AsyncSession, run_id):
        result = await session.execute(
            select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.sequence.asc())
        )
        return list(result.scalars().all())


stream_service = StreamService()
