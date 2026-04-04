from __future__ import annotations

from app.services.llm_service import llm_service
from app.v2.core.models import EnvProfile
from app.v2.modules.env_profiles.model_routing import resolve_model_for_stage
from app.v2.modules.env_profiles.repository import EnvProfileRepository
from app.v2.modules.env_profiles.schemas import (
    EnvProfileCreatePayload,
    EnvProfileResponse,
    EnvProfileUpdatePayload,
    EnvProfileValidationResponse,
)


def mask_api_key(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def to_domain(row: dict) -> EnvProfile:
    return EnvProfile(
        name=row["name"],
        provider_type=row["provider_type"],
        api_base_url=row.get("api_base_url") or "",
        api_key=row.get("api_key") or "",
        default_model=row["default_model"],
        review_model=row.get("review_model") or "",
        test_model=row.get("test_model") or "",
        capability_generation_model=row.get("capability_generation_model") or "",
        report_model=row.get("report_model") or "",
        temperature=float(row.get("temperature") or 0.2),
        default_timeout_sec=int(row.get("default_timeout_sec") or 300),
        max_retries=int(row.get("max_retries") or 2),
        max_concurrency=int(row.get("max_concurrency") or 2),
        enable_docker_sandbox=bool(row.get("enable_docker_sandbox")),
        enable_auto_sub_agents=bool(row.get("enable_auto_sub_agents")),
    )


def merge_profile_update_payload(existing: dict, incoming: dict) -> dict:
    merged = {**existing, **incoming}
    if not str(incoming.get("api_key", "")).strip():
        merged["api_key"] = existing.get("api_key", "")
    return merged


class EnvProfileService:
    def __init__(self) -> None:
        self.repository = EnvProfileRepository()

    def _serialize(self, row: dict) -> EnvProfileResponse:
        return EnvProfileResponse(
            id=str(row["id"]),
            name=row["name"],
            provider_type=row["provider_type"],
            api_base_url=row.get("api_base_url") or "",
            default_model=row["default_model"],
            review_model=row.get("review_model") or "",
            test_model=row.get("test_model") or "",
            capability_generation_model=row.get("capability_generation_model") or "",
            report_model=row.get("report_model") or "",
            temperature=float(row.get("temperature") or 0.2),
            default_timeout_sec=int(row.get("default_timeout_sec") or 300),
            max_retries=int(row.get("max_retries") or 2),
            max_concurrency=int(row.get("max_concurrency") or 2),
            enable_docker_sandbox=bool(row.get("enable_docker_sandbox")),
            enable_auto_sub_agents=bool(row.get("enable_auto_sub_agents")),
            has_api_key=bool(row.get("api_key")),
            api_key_masked=mask_api_key(row.get("api_key")),
        )

    def list_profiles(self) -> list[EnvProfileResponse]:
        return [self._serialize(row) for row in self.repository.list_profiles()]

    def get_profile(self, profile_id: str) -> EnvProfileResponse:
        return self._serialize(self.repository.get_profile(profile_id))

    def get_profile_for_runtime(self, profile_id: str) -> EnvProfile:
        return to_domain(self.repository.get_profile_for_runtime(profile_id))

    def create_profile(self, payload: EnvProfileCreatePayload) -> EnvProfileResponse:
        return self._serialize(self.repository.create_profile(payload))

    def update_profile(self, profile_id: str, payload: EnvProfileUpdatePayload) -> EnvProfileResponse:
        existing = self.repository.get_profile(profile_id)
        merged = merge_profile_update_payload(existing, payload.model_dump())
        return self._serialize(self.repository.update_profile(profile_id, EnvProfileUpdatePayload(**merged)))

    def validate_profile(self, profile_id: str) -> EnvProfileValidationResponse:
        profile = self.get_profile_for_runtime(profile_id)
        selected_models = {
            "requirement_analysis": resolve_model_for_stage("requirement_analysis", profile, None, {}),
            "capability_generation": resolve_model_for_stage("capability_generation", profile, None, {}),
            "review": resolve_model_for_stage("review", profile, None, {}),
            "test": resolve_model_for_stage("test", profile, None, {}),
            "report": resolve_model_for_stage("report", profile, None, {}),
        }
        if profile.provider_type == "demo":
            return EnvProfileValidationResponse(
                ok=True,
                provider_type=profile.provider_type,
                selected_models=selected_models,
                message="Demo provider is ready.",
            )
        llm_result = llm_service.generate_text(
            "Return PONG only.",
            {
                "provider_type": profile.provider_type,
                "api_base_url": profile.api_base_url,
                "api_key": profile.api_key,
                "default_model": profile.default_model,
                "review_model": profile.review_model or profile.default_model,
                "test_model": profile.test_model or profile.default_model,
                "temperature": profile.temperature,
                "default_timeout_sec": profile.default_timeout_sec,
            },
            purpose="default",
        )
        ok = not bool(llm_result.get("error"))
        return EnvProfileValidationResponse(
            ok=ok,
            provider_type=profile.provider_type,
            selected_models=selected_models,
            message="Validation succeeded." if ok else str(llm_result.get("error") or llm_result.get("content", "")),
        )


env_profile_service = EnvProfileService()
