import uuid
import asyncio
import json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/tasks", tags=["events"])

# In-memory subscriber registry for SSE
_subscribers: dict[uuid.UUID, asyncio.Queue] = {}


@router.get("/{task_id}/stream")
async def stream_task_events(task_id: uuid.UUID):
    """
    SSE endpoint for real-time task event streaming.
    Clients connect and receive events as they occur.
    """

    async def event_generator():
        queue: asyncio.Queue = _subscribers.setdefault(task_id, asyncio.Queue())
        try:
            while True:
                event = await queue.get()
                yield {
                    "event": event["event_type"],
                    "data": json.dumps({
                        "task_id": str(task_id),
                        "message": event["message"],
                        "payload": event["payload"],
                    }),
                }
                if event.get("done"):
                    break
        finally:
            _subscribers.pop(task_id, None)

    return EventSourceResponse(event_generator())


async def publish_event(task_id: uuid.UUID, event_type: str, message: str | None, payload: dict | None):
    """Publish an event to all subscribers of a task."""
    if task_id in _subscribers:
        await _subscribers[task_id].put({
            "event_type": event_type,
            "message": message,
            "payload": payload,
            "done": False,
        })


async def close_stream(task_id: uuid.UUID):
    """Signal the SSE stream to close."""
    if task_id in _subscribers:
        await _subscribers[task_id].put({"done": True})
