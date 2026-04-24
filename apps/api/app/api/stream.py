from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.db import get_db_session
from app.services.run_service import run_service
from app.services.stream_service import stream_service


router = APIRouter(tags=["stream"])


@router.get("/tasks/{task_id}/runs/{run_id}/events")
async def get_run_events(task_id: UUID, run_id: UUID, session: AsyncSession = Depends(get_db_session)):
    run = await run_service.get_run(session, task_id, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    events = await stream_service.list_events(session, run.id)
    return [
        {
            "id": item.id,
            "run_id": item.run_id,
            "sequence": item.sequence,
            "category": item.category,
            "name": item.name,
            "message": item.message,
            "payload": item.payload,
            "created_at": item.created_at.isoformat(),
        }
        for item in events
    ]


@router.get("/tasks/{task_id}/runs/{run_id}/stream")
async def stream_run_events(task_id: UUID, run_id: UUID, session: AsyncSession = Depends(get_db_session)):
    run = await run_service.get_run(session, task_id, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    async def event_generator():
        emitted = 0
        while True:
            events = await stream_service.list_events(session, run.id)
            for event in events[emitted:]:
                yield {
                    "event": event.name,
                    "data": {
                        "sequence": event.sequence,
                        "category": event.category,
                        "message": event.message,
                        "payload": event.payload,
                    },
                }
            emitted = len(events)
            if run.status in {"completed", "failed", "canceled"} and emitted == len(events):
                break
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
