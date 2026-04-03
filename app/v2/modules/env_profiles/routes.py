from __future__ import annotations

from fastapi import APIRouter

from app.v2.modules.env_profiles.schemas import EnvProfileCreatePayload, EnvProfileUpdatePayload
from app.v2.modules.env_profiles.service import env_profile_service


router = APIRouter(prefix="/v2/env-profiles", tags=["v2-env-profiles"])


@router.get("")
def list_env_profiles():
    return env_profile_service.list_profiles()


@router.get("/{profile_id}")
def get_env_profile(profile_id: str):
    return env_profile_service.get_profile(profile_id)


@router.post("")
def create_env_profile(payload: EnvProfileCreatePayload):
    return env_profile_service.create_profile(payload)


@router.put("/{profile_id}")
def update_env_profile(profile_id: str, payload: EnvProfileUpdatePayload):
    return env_profile_service.update_profile(profile_id, payload)


@router.post("/{profile_id}/validate")
def validate_env_profile(profile_id: str):
    return env_profile_service.validate_profile(profile_id)
