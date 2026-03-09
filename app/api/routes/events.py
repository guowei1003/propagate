from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.routes.dependencies import events
from app.config import settings


router = APIRouter()


@router.get("/api/tasks/{task_id}/events")
def list_events(task_id: str, after_id: int | None = None) -> list[dict]:
    return events.list_by_task(task_id, after_id=after_id)


@router.get("/api/tasks/{task_id}/stream")
async def stream_task_events(task_id: str, last_event_id: int = 0) -> StreamingResponse:
    async def event_generator():
        cursor = last_event_id
        while True:
            batch = events.list_by_task(task_id, after_id=cursor, limit=100)
            for item in batch:
                cursor = item["id"]
                yield f"id: {item['id']}\ndata: {json.dumps(item, ensure_ascii=False)}\n\n"
            await asyncio.sleep(settings.event_stream_interval_sec)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
