from __future__ import annotations

from pydantic import BaseModel, Field


class EnvProfileCreatePayload(BaseModel):
    name: str
    provider_type: str = Field(default="demo")
    api_base_url: str = ""
    api_key: str = ""
    default_model: str
    review_model: str = ""
    test_model: str = ""
    capability_generation_model: str = ""
    report_model: str = ""
    temperature: float = 0.2
    default_timeout_sec: int = 300
    max_retries: int = 2
    max_concurrency: int = 2
    enable_docker_sandbox: bool = True
    enable_auto_sub_agents: bool = True


class EnvProfileUpdatePayload(EnvProfileCreatePayload):
    pass


class EnvProfileResponse(BaseModel):
    id: str
    name: str
    provider_type: str
    api_base_url: str = ""
    default_model: str
    review_model: str = ""
    test_model: str = ""
    capability_generation_model: str = ""
    report_model: str = ""
    temperature: float
    default_timeout_sec: int
    max_retries: int
    max_concurrency: int
    enable_docker_sandbox: bool
    enable_auto_sub_agents: bool
    has_api_key: bool
    api_key_masked: str


class EnvProfileValidationResponse(BaseModel):
    ok: bool
    provider_type: str
    selected_models: dict[str, str]
    message: str
