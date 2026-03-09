from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import clarifications, env_profiles, events, pages, tasks
from app.config import BASE_DIR, settings
from app.db import init_db
from app.repositories.env_profile_repository import EnvProfileRepository
from app.workers.engine import worker_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    EnvProfileRepository().seed_default_profile()
    settings.artifacts_root.mkdir(parents=True, exist_ok=True)
    worker_engine.start()
    try:
        yield
    finally:
        worker_engine.stop()


app = FastAPI(title="Propagate", lifespan=lifespan)
app.include_router(pages.router)
app.include_router(tasks.router)
app.include_router(clarifications.router)
app.include_router(env_profiles.router)
app.include_router(events.router)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "web" / "static")), name="static")

