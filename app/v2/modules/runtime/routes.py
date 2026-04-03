from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.v2.modules.runtime.service import runtime_service


router = APIRouter(prefix="/v2/runs", tags=["v2-runs"])


@router.post("/{run_id}/resume")
def resume_run(run_id: str):
    return runtime_service.resume_run(run_id)


@router.get("/{run_id}/artifacts")
def get_run_artifacts(run_id: str):
    return runtime_service.get_run_artifacts(run_id)


@router.get("/{run_id}/stream")
async def stream_run(run_id: str, request: Request):
    async def event_stream():
        seen: set[str] = set()
        while True:
            if await request.is_disconnected():
                break
            events = runtime_service.stream_events(run_id)
            sent = False
            for item in events:
                event_id = item.get("id")
                if event_id in seen:
                    continue
                seen.add(event_id)
                sent = True
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            if not sent:
                yield ": heartbeat\n\n"
            import asyncio

            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
