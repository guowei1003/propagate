import asyncio
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine, Base, AsyncSessionLocal
from app.routers import tasks, events, profiles
from app.services.worker import Worker
from app.services.task_service import task_service

_worker: Worker | None = None
_worker_task: asyncio.Task | None = None


async def on_task_event(task_id: uuid.UUID, event_type: str, message: str | None, payload: dict | None):
    """Called by Worker whenever a task event occurs. Persist log + push SSE."""
    async with AsyncSessionLocal() as session:
        await task_service.append_log(session, task_id, event_type, message, payload)
    await events.publish_event(task_id, event_type, message, payload)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker, _worker_task
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    _worker = Worker(on_event=on_task_event)
    _worker_task = asyncio.create_task(_worker.start(lambda: AsyncSessionLocal))
    print("[Propagate] Worker started")

    yield

    if _worker:
        await _worker.stop()
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
    await engine.dispose()
    print("[Propagate] Shutdown complete")


app = FastAPI(
    title="Propagate API",
    version="1.0.0",
    description="AI Task Execution System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(profiles.router)
app.include_router(events.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/tasks/{task_id}/events", tags=["events"])
async def get_task_events(task_id: uuid.UUID):
    from app.routers import events as ev_module
    async with AsyncSessionLocal() as session:
        logs = await task_service.get_logs(session, task_id)
    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "message": log.message,
            "payload": log.payload,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
