from __future__ import annotations

from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse

from app.api.routes.dependencies import env_profiles


router = APIRouter()


@router.get("/api/env-profiles")
def list_env_profiles() -> list[dict]:
    return env_profiles.list_profiles()


@router.post("/env-profiles")
def create_env_profile(
    name: str = Form(...),
    provider_type: str = Form("demo"),
    api_base_url: str = Form(""),
    api_key: str = Form(""),
    default_model: str = Form(...),
    review_model: str = Form(...),
    test_model: str = Form(...),
    temperature: float = Form(0.2),
    max_concurrency: int = Form(...),
    default_timeout_sec: int = Form(...),
    max_retries: int = Form(...),
    enable_auto_sub_agents: str = Form("off"),
    enable_docker_sandbox: str = Form("off"),
) -> RedirectResponse:
    env_profiles.create_profile(
        name=name.strip(),
        provider_type=provider_type.strip(),
        api_base_url=api_base_url.strip(),
        api_key=api_key.strip(),
        default_model=default_model.strip(),
        review_model=review_model.strip(),
        test_model=test_model.strip(),
        temperature=temperature,
        max_concurrency=max_concurrency,
        default_timeout_sec=default_timeout_sec,
        max_retries=max_retries,
        enable_auto_sub_agents=enable_auto_sub_agents == "on",
        enable_docker_sandbox=enable_docker_sandbox == "on",
    )
    return RedirectResponse(url="/env-profiles", status_code=303)
