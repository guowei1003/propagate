from __future__ import annotations

from fastapi import APIRouter

from app.v2.modules.bundles import routes as bundle_routes
from app.v2.modules.capabilities import routes as capability_routes
from app.v2.modules.env_profiles import routes as env_profile_routes
from app.v2.modules.runtime import routes as runtime_routes
from app.v2.modules.tasks import routes as task_routes


router = APIRouter()
router.include_router(task_routes.router)
router.include_router(capability_routes.router)
router.include_router(env_profile_routes.router)
router.include_router(runtime_routes.router)
router.include_router(bundle_routes.router)
