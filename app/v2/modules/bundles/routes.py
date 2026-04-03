from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.v2.modules.bundles.service import bundle_service


router = APIRouter(prefix="/v2/runs", tags=["v2-bundles"])


@router.post("/{run_id}/bundle/build")
def build_bundle(run_id: str):
    return bundle_service.build_bundle(run_id)


@router.get("/{run_id}/bundle")
def get_bundle(run_id: str):
    return bundle_service.get_bundle(run_id)


@router.get("/{run_id}/bundle/download")
def download_bundle(run_id: str):
    archive = bundle_service.get_bundle_archive(run_id)
    return FileResponse(archive, filename=archive.name, media_type="application/gzip")
