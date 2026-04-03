from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.v2.api import pages
from app.v2.api.router import router as v2_router
from app.v2.core.config import v2_settings
from app.v2.core.http import install_error_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.artifacts_root.mkdir(parents=True, exist_ok=True)
    v2_settings.bundle_root.mkdir(parents=True, exist_ok=True)
    v2_settings.runtime_root.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Propagate", lifespan=lifespan)
install_error_handlers(app)
app.include_router(v2_router)
app.include_router(pages.router)
if v2_settings.frontend_dist_dir.exists():
    assets_dir = v2_settings.frontend_dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
